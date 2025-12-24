# -*- coding: utf-8 -*-
"""Service registry for Cullinan framework.

统一使用 cullinan.core 的 DI 系统，作为 InjectionRegistry 的 provider。

架构设计（类似 Spring ApplicationContext）：
- ServiceRegistry 存储服务类定义
- 作为 provider 向 core.InjectionRegistry 提供服务实例
- 完全解耦，不再使用 legacy DependencyInjector
- 支持生命周期管理（on_init/on_startup/on_shutdown/on_destroy）

Performance optimizations:
- Fast O(1) service lookup with direct dict access
- Lazy metadata initialization
- Memory-efficient with __slots__
- Singleton instance caching
"""

from typing import Type, Optional, List, Dict, Any, Set
import logging
import inspect

from cullinan.core import Registry, LifecycleManager
from cullinan.core.exceptions import RegistryError, DependencyResolutionError
# Import ProviderSource interface (Task-1.3)
from cullinan.core.provider_source import ProviderSource
from .base import Service

logger = logging.getLogger(__name__)


class ServiceRegistry(Registry[Type[Service]], ProviderSource):
    """服务注册表 - cullinan.core DI 系统的 Service Provider (实现 ProviderSource 接口)

    职责（类似 Spring 的 BeanFactory）：
    1. 存储服务类定义
    2. 创建和缓存服务单例实例
    3. 作为 ProviderSource 向 InjectionRegistry 提供服务实例
    4. 管理服务生命周期（on_init/on_startup/on_shutdown/on_destroy）

    实现 ProviderSource 接口（Task-1.3）：
    - can_provide(name): 检查是否能提供服务
    - provide(name): 提供服务实例
    - list_available(): 列出所有可用服务
    - get_priority(): 返回优先级（默认 10）

    与 core.InjectionRegistry 的关系：
    - ServiceRegistry 在初始化时注册为 InjectionRegistry 的 ProviderSource
    - 当 Controller/Service 使用 Inject() 或 InjectByName() 时
    - InjectionRegistry 会调用 ServiceRegistry.provide() 获取实例
    - 形成完整的依赖注入链条

    Usage:
        # 通过 @service 装饰器自动注册（推荐）
        @service
        class EmailService(Service):
            pass

        # 或者手动注册
        registry = get_service_registry()
        registry.register('EmailService', EmailService)

        # 初始化所有服务
        registry.initialize_all()
        
        # 获取服务实例（通常不需要手动调用，通过 Inject() 自动注入）
        email_service = registry.get_instance('EmailService')

        # 清理
        registry.destroy_all()
    """
    
    __slots__ = ('_instances', '_initialized', '_instance_lock', '_lifecycle_manager', '_priority')

    def __init__(self, priority: int = 10, auto_register: bool = True):
        """初始化服务注册表

        Args:
            priority: ProviderSource 优先级（默认 10）
            auto_register: 是否自动注册到 InjectionRegistry（默认 True，向后兼容）
        """
        super().__init__()

        # 服务实例缓存 (O(1) lookup)
        self._instances: Dict[str, Service] = {}

        # 已初始化的服务集合 (O(1) membership check)
        self._initialized: Set[str] = set()

        # 线程锁（确保单例的线程安全）
        import threading
        self._instance_lock = threading.RLock()

        # 生命周期管理器
        self._lifecycle_manager = LifecycleManager()

        # ProviderSource 优先级
        self._priority = priority

        # 始终注册到 InjectionRegistry (使用 ProviderSource 接口)
        if auto_register:
            from cullinan.core import get_injection_registry
            injection_registry = get_injection_registry()
            injection_registry.add_provider_source(self)
            logger.debug(f"ServiceRegistry auto-registered as core DI provider (priority={self._priority})")

    def register(self, name: str, service_class: Type[Service], 
                 dependencies: Optional[List[str]] = None, **metadata) -> None:
        """注册服务类到统一 DI 容器（O(1) 操作）

        注意：
        - 服务类应该使用 @service 装饰器，它会自动调用 @injectable
        - @injectable 会扫描类的类型注解（Inject、InjectByName）并在实例化时注入
        - dependencies 参数仅用于元数据和依赖顺序分析，实际注入由 core 处理

        Args:
            name: 服务唯一标识符（通常是类名）
            service_class: 服务类（不是实例）
            dependencies: 依赖的服务名称列表（可选，仅用于元数据）
            **metadata: 其他元数据

        Raises:
            RegistryError: 如果名称已注册、无效或注册表已冻结
        """
        self._check_frozen()
        self._validate_name(name)
        
        # Fast path: 检查是否已注册
        if name in self._items:
            logger.warning(f"Service already registered: {name}")
            return
        
        # 存储服务类 (O(1))
        self._items[name] = service_class
        
        # Lazy metadata initialization - 仅在需要时创建
        if dependencies or metadata:
            if self._metadata is None:
                self._metadata = {}
            meta = metadata.copy()
            meta['dependencies'] = dependencies or []
            self._metadata[name] = meta

        logger.debug(f"Registered service class: {name} (DI via core.injectable)")

    def get(self, name: str) -> Optional[Type[Service]]:
        """Get the service class (not instance) by name (O(1) operation).

        Args:
            name: Service identifier
        
        Returns:
            Service class, or None if not found
        """
        return self._items.get(name)
    
    def get_instance(self, name: str) -> Optional[Service]:
        """获取或创建服务实例（O(1) 缓存查找，线程安全）

        工作流程：
        1. 检查缓存，如果已存在则直接返回（O(1））
        2. 如果不存在，创建新实例（调用 __init__）
        3. @injectable 装饰器会在 __init__ 后自动注入依赖
        4. 调用生命周期钩子 on_init()
        5. 缓存实例供下次使用

        注意：
        - 此方法仅支持同步 on_init()
        - 如果服务有异步 on_init()，使用 initialize_all_async()

        Args:
            name: 服务标识符

        Returns:
            服务实例，如果未找到则返回 None

        Raises:
            DependencyResolutionError: 如果依赖无法解析
        """
        # Fast path: 返回缓存的实例 (O(1)) - 读取不需要锁
        instance = self._instances.get(name)
        if instance is not None:
            return instance

        # 检查服务是否存在
        if name not in self._items:
            logger.debug(f"Service not found: {name}")
            return None
        
        # 线程安全的单例创建
        with self._instance_lock:
            # Double-check pattern: 另一个线程可能已经创建了它
            instance = self._instances.get(name)
            if instance is not None:
                return instance

            try:
                service_class = self._items[name]

                # 【关键】直接实例化服务类
                # @injectable 装饰器已经包装了 __init__，会在实例化后自动注入依赖
                # 不再需要 legacy DependencyInjector.resolve()
                instance = service_class()

                # 立即缓存实例 (O(1))
                self._instances[name] = instance

                # 调用 on_init 生命周期钩子（如果存在且尚未初始化）
                if name not in self._initialized:
                    if hasattr(instance, 'on_init') and callable(instance.on_init):
                        try:
                            result = instance.on_init()
                            # [FIX HIGH] 检查 on_init 是否是异步的
                            # 同步路径不能执行异步方法，抛出明确错误而不是静默失败
                            if inspect.iscoroutine(result):
                                result.close()  # 清理 coroutine 以避免警告
                                raise RuntimeError(
                                    f"Service '{name}.on_init()' is async but 'get_instance()' is synchronous. "
                                    f"Please use 'await initialize_all_async()' instead, or make 'on_init()' synchronous."
                                )
                            self._initialized.add(name)
                            logger.debug(f"Called on_init for service: {name}")
                        except RuntimeError:
                            # 重新抛出我们自己的 RuntimeError
                            raise
                        except Exception as e:
                            logger.error(f"Error in on_init for {name}: {e}", exc_info=True)
                            # 如果初始化失败，从实例缓存中移除
                            self._instances.pop(name, None)
                            raise
                    else:
                        # 即使没有 on_init 方法也标记为已初始化
                        self._initialized.add(name)

                logger.debug(f"Created service instance: {name} (dependencies injected by @injectable)")
                return instance

            except Exception as e:
                logger.error(f"Failed to instantiate service {name}: {e}", exc_info=True)
                raise DependencyResolutionError(f"Failed to create {name}: {e}") from e

    def initialize_all(self) -> None:
        """初始化所有注册的服务

        执行流程：
        1. 按照注册顺序创建实例（调用 get_instance）
        2. get_instance 会触发 @injectable 自动注入依赖
        3. 调用 on_init() 生命周期钩子
        4. 调用 on_startup() 生命周期钩子

        注意：
        - 对于异步方法，请使用 initialize_all_async()
        - 依赖顺序由 core.InjectionRegistry 自动处理
        - 错误处理策略由 configure(startup_error_policy=...) 控制
        """
        # 获取启动错误策略
        from cullinan.config import get_config
        config = get_config()
        error_policy = config.startup_error_policy

        # 获取所有服务名称
        service_names = list(self._items.keys())
        
        if not service_names:
            logger.debug("No services to initialize")
            return
        
        # 按注册顺序初始化（core DI 系统会自动处理依赖顺序）
        logger.info(f"Initializing {len(service_names)} services (error_policy={error_policy})...")

        failed_services = []  # 记录失败的服务

        for name in service_names:
            try:
                # get_instance 会创建实例并调用 on_init
                # 注意：get_instance 可能抛出 DependencyResolutionError
                instance = self.get_instance(name)
                if not instance:
                    error_msg = f"Failed to create instance for {name}"
                    logger.warning(error_msg)

                    if error_policy == 'strict':
                        raise RuntimeError(error_msg)
                    elif error_policy == 'warn':
                        failed_services.append(name)
                        continue
                    # 'ignore' 策略：继续
                    continue

                # 调用 on_startup 钩子
                if hasattr(instance, 'on_startup') and callable(instance.on_startup):
                    try:
                        result = instance.on_startup()
                        # [FIX HIGH] 同步路径检测到异步方法时抛出错误
                        if inspect.iscoroutine(result):
                            result.close()  # 清理 coroutine
                            raise RuntimeError(
                                f"Service '{name}.on_startup()' is async but 'initialize_all()' is synchronous. "
                                f"Please use 'await initialize_all_async()' instead, or make 'on_startup()' synchronous."
                            )
                        logger.debug(f"Called on_startup for service: {name}")
                    except RuntimeError as e:
                        # RuntimeError（包括我们的 async 检测错误）总是重新抛出
                        if 'is async but' in str(e):
                            raise
                        # 其他 RuntimeError 根据策略处理
                        logger.error(f"Error in on_startup for {name}: {e}", exc_info=True)
                        if error_policy == 'strict':
                            raise
                        elif error_policy == 'warn':
                            logger.warning(f"Service {name} on_startup failed, but continuing due to 'warn' policy")
                            failed_services.append(name)
                            continue
                    except Exception as e:
                        logger.error(f"Error in on_startup for {name}: {e}", exc_info=True)

                        # 根据策略处理错误
                        if error_policy == 'strict':
                            raise
                        elif error_policy == 'warn':
                            logger.warning(f"Service {name} on_startup failed, but continuing due to 'warn' policy")
                            failed_services.append(name)
                            continue
                        # 'ignore' 策略：继续

            except DependencyResolutionError as e:
                # get_instance 抛出的依赖解析错误
                logger.error(f"Failed to resolve dependencies for {name}: {e}", exc_info=True)

                if error_policy == 'strict':
                    raise  # 立即退出
                elif error_policy == 'warn':
                    logger.warning(f"Service {name} dependency resolution failed, but continuing due to 'warn' policy")
                    failed_services.append(name)
                    continue
                # 'ignore' 策略：继续

            except RuntimeError as e:
                # RuntimeError 需要特殊处理（包括 async 检测）
                if 'is async but' in str(e):
                    raise  # async 检测错误总是抛出

                logger.error(f"Failed to initialize service {name}: {e}", exc_info=True)
                if error_policy == 'strict':
                    raise
                elif error_policy == 'warn':
                    logger.warning(f"Service {name} initialization failed, but continuing due to 'warn' policy")
                    failed_services.append(name)
                    continue

            except Exception as e:
                logger.error(f"Failed to initialize service {name}: {e}", exc_info=True)

                # 根据策略处理错误
                if error_policy == 'strict':
                    raise  # 立即退出
                elif error_policy == 'warn':
                    logger.warning(f"Service {name} initialization failed, but continuing due to 'warn' policy")
                    failed_services.append(name)
                    continue
                # 'ignore' 策略：继续

        # 输出最终状态
        successful_count = len(self._instances)
        failed_count = len(failed_services)

        if failed_count > 0:
            logger.warning(
                f"Initialized {successful_count} services, {failed_count} failed: {', '.join(failed_services)}"
            )
            if error_policy != 'strict':
                logger.warning("Application running in degraded mode due to failed services")
        else:
            logger.info(f"Successfully initialized {successful_count} services")

    async def initialize_all_async(self) -> None:
        """初始化所有注册的服务（异步版本）

        执行流程：
        1. 创建实例（调用 get_instance 或直接实例化）
        2. @injectable 自动注入依赖
        3. 调用 on_init_async() 或 on_init()
        4. 调用 on_startup_async() 或 on_startup()
        """
        service_names = list(self._items.keys())
        
        if not service_names:
            logger.debug("No services to initialize")
            return
        
        logger.info(f"Initializing {len(service_names)} services (async)...")

        # 创建实例并调用 on_init
        for name in service_names:
            try:
                if name not in self._instances:
                    service_class = self._items[name]
                    # 直接实例化（@injectable 会自动注入）
                    instance = service_class()
                    self._instances[name] = instance

                    # 调用 on_init (async 优先)
                    if hasattr(instance, 'on_init') and callable(instance.on_init):
                        result = instance.on_init()
                        if inspect.iscoroutine(result):
                            await result
                            logger.debug(f"Called on_init (async) for service: {name}")
                        else:
                            logger.debug(f"Called on_init (sync) for service: {name}")
                    # 检查 on_init_async（显式命名的异步方法）
                    elif hasattr(instance, 'on_init_async') and callable(instance.on_init_async):
                        from cullinan.service.base import Service
                        if instance.on_init_async.__func__ is not Service.on_init_async:
                            await instance.on_init_async()
                            logger.debug(f"Called on_init_async for service: {name}")

                    self._initialized.add(name)

            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}", exc_info=True)
                raise
        
        # 调用 on_startup (async 支持)
        logger.debug("Calling on_startup() for all services...")
        for name in service_names:
            instance = self._instances.get(name)
            if instance:
                try:
                    # 优先检查 on_startup 是否是 async 方法（子类重写）
                    if hasattr(instance, 'on_startup') and callable(instance.on_startup):
                        result = instance.on_startup()
                        if inspect.iscoroutine(result):
                            await result
                            logger.debug(f"Called on_startup (async) for service: {name}")
                        else:
                            logger.debug(f"Called on_startup (sync) for service: {name}")
                    # 再检查 on_startup_async（显式命名的异步方法）
                    elif hasattr(instance, 'on_startup_async') and callable(instance.on_startup_async):
                        # 检查是否是基类的默认空实现
                        from cullinan.service.base import Service
                        if instance.on_startup_async.__func__ is not Service.on_startup_async:
                            await instance.on_startup_async()
                            logger.debug(f"Called on_startup_async for service: {name}")
                except Exception as e:
                    logger.error(f"Error in on_startup for {name}: {e}", exc_info=True)
                    # 不抛出异常，继续处理其他服务

        logger.info(f"Startup complete for {len(service_names)} services (async)")

    def destroy_all(self) -> None:
        """Destroy all service instances in reverse dependency order.
        
        Calls lifecycle hooks:
        1. on_shutdown() - explicitly called here
        2. on_destroy() - called for cleanup

        For async methods, use destroy_all_async() instead.

        Raises:
            RuntimeError: If async lifecycle methods are detected on sync path
        """
        # Get shutdown order (reverse of initialization)
        if not self._instances:
            logger.debug("No services to destroy")
            return

        # Calculate reverse order
        shutdown_order = list(reversed(list(self._instances.keys())))

        # Call on_shutdown() lifecycle methods
        logger.debug("Calling on_shutdown() for all services...")
        for name in shutdown_order:
            instance = self._instances.get(name)
            if instance:
                try:
                    # Check for on_shutdown method
                    if hasattr(instance, 'on_shutdown') and callable(instance.on_shutdown):
                        result = instance.on_shutdown()
                        # [FIX HIGH] 同步路径检测到异步方法时抛出错误
                        if inspect.iscoroutine(result):
                            result.close()
                            raise RuntimeError(
                                f"Service '{name}.on_shutdown()' is async but 'destroy_all()' is synchronous. "
                                f"Please use 'await destroy_all_async()' instead, or make 'on_shutdown()' synchronous."
                            )
                        logger.debug(f"Called on_shutdown for service: {name}")

                    # Also check on_pre_destroy
                    elif hasattr(instance, 'on_pre_destroy') and callable(instance.on_pre_destroy):
                        result = instance.on_pre_destroy()
                        if inspect.iscoroutine(result):
                            result.close()
                            raise RuntimeError(
                                f"Service '{name}.on_pre_destroy()' is async but 'destroy_all()' is synchronous. "
                                f"Please use 'await destroy_all_async()' instead."
                            )
                        logger.debug(f"Called on_pre_destroy for service: {name}")
                except RuntimeError:
                    # 重新抛出我们的 RuntimeError（不捕获）
                    raise
                except Exception as e:
                    logger.error(f"Error in on_shutdown/on_pre_destroy for {name}: {e}", exc_info=True)
                    # Continue with other services

        # Call on_destroy() lifecycle methods
        logger.debug("Calling on_destroy() for all services...")
        for name in shutdown_order:
            instance = self._instances.get(name)
            if instance:
                try:
                    if hasattr(instance, 'on_destroy') and callable(instance.on_destroy):
                        result = instance.on_destroy()
                        # [FIX HIGH] 同步路径检测到异步方法时抛出错误
                        if inspect.iscoroutine(result):
                            result.close()
                            raise RuntimeError(
                                f"Service '{name}.on_destroy()' is async but 'destroy_all()' is synchronous. "
                                f"Please use 'await destroy_all_async()' instead, or make 'on_destroy()' synchronous."
                            )
                        logger.debug(f"Called on_destroy for service: {name}")
                except RuntimeError:
                    # 重新抛出我们的 RuntimeError（不捕获）
                    raise
                except Exception as e:
                    logger.error(f"Error in on_destroy for {name}: {e}", exc_info=True)
                    # Continue with other services

        logger.info(f"Destroyed {len(shutdown_order)} service instances")

    async def destroy_all_async(self) -> None:
        """Destroy all service instances in reverse dependency order (async version).
        
        Calls async lifecycle hooks:
        1. on_shutdown() or on_shutdown_async()
        2. on_destroy() or on_destroy_async()
        """
        try:
            # Get shutdown order (reverse of initialization)
            if not self._instances:
                logger.debug("No services to destroy")
                return

            # Calculate reverse order
            shutdown_order = list(reversed(list(self._instances.keys())))

            # Call on_shutdown() lifecycle methods (async support)
            logger.debug("Calling on_shutdown() for all services...")
            for name in shutdown_order:
                instance = self._instances.get(name)
                if instance:
                    try:
                        # 优先检查 on_shutdown（可能是 async def）
                        if hasattr(instance, 'on_shutdown') and callable(instance.on_shutdown):
                            result = instance.on_shutdown()
                            if inspect.iscoroutine(result):
                                await result
                                logger.debug(f"Called on_shutdown (async) for service: {name}")
                            else:
                                logger.debug(f"Called on_shutdown (sync) for service: {name}")
                        # 检查显式命名的 on_shutdown_async
                        elif hasattr(instance, 'on_shutdown_async') and callable(instance.on_shutdown_async):
                            from cullinan.service.base import Service
                            if instance.on_shutdown_async.__func__ is not Service.on_shutdown_async:
                                await instance.on_shutdown_async()
                                logger.debug(f"Called on_shutdown_async for service: {name}")
                        # 检查 on_pre_destroy
                        elif hasattr(instance, 'on_pre_destroy') and callable(instance.on_pre_destroy):
                            result = instance.on_pre_destroy()
                            if inspect.iscoroutine(result):
                                await result
                                logger.debug(f"Called on_pre_destroy (async) for service: {name}")
                            else:
                                logger.debug(f"Called on_pre_destroy (sync) for service: {name}")
                        elif hasattr(instance, 'on_pre_destroy_async') and callable(instance.on_pre_destroy_async):
                            from cullinan.service.base import Service
                            if hasattr(Service, 'on_pre_destroy_async') and instance.on_pre_destroy_async.__func__ is not Service.on_pre_destroy_async:
                                await instance.on_pre_destroy_async()
                                logger.debug(f"Called on_pre_destroy_async for service: {name}")
                    except Exception as e:
                        logger.error(f"Error in on_shutdown for {name}: {e}", exc_info=True)
                        # Continue with other services

            # Call on_destroy() lifecycle methods (async support)
            logger.debug("Calling on_destroy() for all services...")
            for name in shutdown_order:
                instance = self._instances.get(name)
                if instance:
                    try:
                        # 优先检查 on_destroy（可能是 async def）
                        if hasattr(instance, 'on_destroy') and callable(instance.on_destroy):
                            result = instance.on_destroy()
                            if inspect.iscoroutine(result):
                                await result
                                logger.debug(f"Called on_destroy (async) for service: {name}")
                            else:
                                logger.debug(f"Called on_destroy (sync) for service: {name}")
                        # 检查显式命名的 on_destroy_async
                        elif hasattr(instance, 'on_destroy_async') and callable(instance.on_destroy_async):
                            from cullinan.service.base import Service
                            if instance.on_destroy_async.__func__ is not Service.on_destroy_async:
                                await instance.on_destroy_async()
                                logger.debug(f"Called on_destroy_async for service: {name}")
                    except Exception as e:
                        logger.error(f"Error in on_destroy for {name}: {e}", exc_info=True)
                        # Continue with other services

            logger.info(f"Destroyed {len(shutdown_order)} service instances (async)")
        except Exception as e:
            logger.error(f"Service destruction failed: {e}", exc_info=True)
    
    def clear(self) -> None:
        """清空所有服务和实例

        用于测试或应用程序重新初始化。
        注意：不会清除 core.InjectionRegistry，仅清除 ServiceRegistry 自己的数据。
        """
        super().clear()
        self._instances.clear()
        self._initialized.clear()
        logger.debug("Cleared service registry")

        # 重新注册到 InjectionRegistry (使用 ProviderSource)
        try:
            from cullinan.core import get_injection_registry
            injection_registry = get_injection_registry()
            injection_registry.add_provider_source(self)
            logger.debug(f"ServiceRegistry re-registered after clear (priority={self._priority})")
        except Exception as e:
            logger.debug(f"Failed to re-register ServiceRegistry: {e}")

    def list_instances(self) -> Dict[str, Service]:
        """Get all service instances that have been created.
        
        Returns:
            Dictionary mapping service names to instances
        """
        return self._instances.copy()
    
    def has_instance(self, name: str) -> bool:
        """Check if a service instance has been created.
        
        Args:
            name: Service identifier
        
        Returns:
            True if instance exists, False otherwise
        """
        return name in self._instances

    # ========================================================================
    # ProviderSource Interface Implementation (Task-1.3)
    # ========================================================================

    def can_provide(self, name: str) -> bool:
        """检查是否能提供指定名称的服务 (ProviderSource 接口)

        Args:
            name: 服务名称

        Returns:
            True 表示可以提供，False 表示不能提供
        """
        return self.has(name)

    def provide(self, name: str) -> Optional[Service]:
        """提供指定名称的服务实例 (ProviderSource 接口)

        此方法是 ProviderSource 接口的实现，被 InjectionRegistry 调用。
        内部调用 get_instance() 来获取服务实例。

        Args:
            name: 服务名称

        Returns:
            服务实例，如果无法提供则返回 None
        """
        return self.get_instance(name)

    def list_available(self) -> List[str]:
        """列出所有可用的服务名称 (ProviderSource 接口)

        Returns:
            服务名称列表
        """
        return list(self._items.keys())

    def get_priority(self) -> int:
        """获取此 ProviderSource 的优先级 (ProviderSource 接口)

        Returns:
            优先级数值，越大越优先（默认 10）
        """
        return self._priority


# Global service registry instance (for backward compatibility)
_global_service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance.
    
    Returns:
        The global ServiceRegistry instance
    """
    return _global_service_registry


def reset_service_registry() -> None:
    """Reset the global service registry.
    
    Useful for testing to ensure clean state between tests.
    """
    _global_service_registry.clear()
    logger.debug("Reset global service registry")
