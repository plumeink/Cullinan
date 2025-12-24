# -*- coding: utf-8 -*-
"""Controller registry for Cullinan framework.

统一使用 cullinan.core 的 DI 系统，作为 InjectionRegistry 的 provider。

架构设计（类似 Spring MVC）：
- ControllerRegistry 存储 Controller 类定义和路由信息
- 作为 provider 向 core.InjectionRegistry 提供 Controller 实例
- 完全解耦，依赖注入由 @injectable 处理
- 支持路由注册和 HTTP 方法映射

Performance optimizations:
- Fast O(1) controller and method lookup
- Lazy metadata and method storage initialization
- Memory-efficient with __slots__
- Batch method registration support
"""

from typing import Type, Any, Optional, Dict, List, Tuple
import logging
import threading

from cullinan.core import Registry
from cullinan.core.exceptions import RegistryError, DependencyResolutionError
from cullinan.core.provider_source import ProviderSource

logger = logging.getLogger(__name__)


class ControllerRegistry(Registry[Type[Any]], ProviderSource):
    """Controller 注册表 - cullinan.core DI 系统的 Controller Provider

    职责（类似 Spring MVC 的 RequestMappingHandlerMapping）：
    1. 存储 Controller 类定义
    2. 管理 URL 路由和 HTTP 方法映射
    3. 作为 provider 向 InjectionRegistry 提供 Controller 实例
    4. 按需创建 Controller 实例（每次请求或单例）

    与 core.InjectionRegistry 的关系：
    - ControllerRegistry 在初始化时注册为 InjectionRegistry 的 provider
    - Controller 使用 Inject() 或 InjectByName() 注入 Service
    - @injectable 装饰器会在 Controller 实例化时自动注入依赖

    Usage:
        # 通过 @controller 装饰器自动注册（推荐）
        @controller(url='/api/users')
        class UserController:
            user_service = InjectByName('UserService')

        # 或者手动注册
        registry = get_controller_registry()
        registry.register('UserController', UserController, url_prefix='/api/users')
        registry.register_method('UserController', '', 'get', handler_func)
    """

    __slots__ = ('_controller_methods', '_controller_instances', '_instance_lock')

    def __init__(self):
        """初始化 Controller 注册表，并注册为 core DI 系统的 provider"""
        super().__init__()

        # Lazy init - 仅在首次注册方法时创建
        # Maps controller_name -> [(url, method, func), ...]
        self._controller_methods: Optional[Dict[str, List[Tuple[str, str, Any]]]] = None

        # Controller 实例缓存（单例模式）
        # 每个 Controller 只创建一次，所有请求共享同一实例
        # 注意：Controller 必须设计为无状态（线程安全）
        self._controller_instances: Dict[str, Any] = {}

        # 线程锁（确保单例的线程安全）
        self._instance_lock = threading.RLock()

        # 【关键】注册自己为 core.InjectionRegistry 的依赖提供者
        # 使用 ProviderSource 接口（如果已实现）
        from cullinan.core import get_injection_registry
        injection_registry = get_injection_registry()
        
        # Check if this registry implements ProviderSource
        from cullinan.core.provider_source import ProviderSource
        if isinstance(self, ProviderSource):
            injection_registry.add_provider_source(self)
            logger.debug("ControllerRegistry registered as core DI provider (via ProviderSource)")
        else:
            logger.warning("ControllerRegistry does not implement ProviderSource interface")

    def register(self, name: str, controller_class: Type[Any],
                 url_prefix: str = '', **metadata) -> None:
        """注册 Controller 类到统一 DI 容器（O(1) 操作）

        注意：
        - Controller 类应该使用 @controller 装饰器，它会自动调用 @injectable
        - @injectable 会扫描类的类型注解（Inject、InjectByName）并在实例化时注入
        - Controller 实例通常按请求创建，也可以配置为单例

        Args:
            name: Controller 唯一标识符（通常是类名）
            controller_class: Controller 类
            url_prefix: 所有路由的 URL 前缀
            **metadata: 其他元数据（如 middleware、auth 要求等）

        Raises:
            RegistryError: 如果名称已注册、无效或注册表已冻结
        """
        self._check_frozen()
        self._validate_name(name)

        # Fast path: 检查是否已注册
        if name in self._items:
            logger.warning(f"Controller already registered: {name}")
            return

        # 注册 Controller 类 (O(1))
        self._items[name] = controller_class

        # Lazy metadata initialization
        if url_prefix or metadata:
            if self._metadata is None:
                self._metadata = {}
            meta = metadata.copy()
            meta['url_prefix'] = url_prefix
            self._metadata[name] = meta
        elif self._metadata is not None or url_prefix == '':
            # 为一致性存储空前缀
            if self._metadata is None:
                self._metadata = {}
            self._metadata[name] = {'url_prefix': url_prefix}

        logger.debug(f"Registered controller: {name} with prefix: {url_prefix} (DI via core.injectable)")

    def register_method(self, controller_name: str, url: str,
                       http_method: str, handler_func: Any) -> None:
        """Register a method handler for a controller (O(1) operation).

        Args:
            controller_name: Name of the controller
            url: URL pattern for this method (relative to controller prefix)
            http_method: HTTP method (get, post, put, delete, etc.)
            handler_func: The handler function

        Raises:
            RegistryError: If controller not found or registry frozen
        """
        self._check_frozen()

        if controller_name not in self._items:
            raise RegistryError(f"Controller not found: {controller_name}")

        # Lazy init method storage
        if self._controller_methods is None:
            self._controller_methods = {}

        # Ensure list exists for this controller
        if controller_name not in self._controller_methods:
            self._controller_methods[controller_name] = []

        # Register method (O(1) append)
        method_info = (url, http_method, handler_func)
        self._controller_methods[controller_name].append(method_info)

        logger.debug(f"Registered method: {controller_name}.{http_method} {url}")

    def register_methods_batch(self, controller_name: str,
                               methods: List[Tuple[str, str, Any]]) -> int:
        """Register multiple methods for a controller in batch (optimized).

        More efficient than calling register_method multiple times.

        Args:
            controller_name: Name of the controller
            methods: List of (url, http_method, handler_func) tuples

        Returns:
            Number of methods successfully registered

        Raises:
            RegistryError: If controller not found or registry frozen
        """
        self._check_frozen()

        if controller_name not in self._items:
            raise RegistryError(f"Controller not found: {controller_name}")

        # Lazy init method storage
        if self._controller_methods is None:
            self._controller_methods = {}

        # Ensure list exists
        if controller_name not in self._controller_methods:
            self._controller_methods[controller_name] = []

        # Batch append (more efficient than multiple appends)
        self._controller_methods[controller_name].extend(methods)

        logger.debug(f"Registered {len(methods)} methods for controller: {controller_name}")
        return len(methods)

    def get(self, name: str) -> Optional[Type[Any]]:
        """获取 Controller 类（O(1) 操作）

        Args:
            name: Controller 标识符

        Returns:
            Controller 类，如果未找到则返回 None
        """
        return self._items.get(name)

    def get_instance(self, name: str) -> Optional[Any]:
        """获取或创建 Controller 单例实例（O(1) 缓存查找，线程安全）

        工作流程（类似 ServiceRegistry.get_instance）：
        1. 检查缓存，如果已存在则直接返回（O(1））
        2. 如果不存在，创建新实例（调用 __init__）
        3. @injectable 装饰器会在 __init__ 后自动注入依赖
        4. 缓存实例供所有请求共享

        注意：
        - Controller 是单例，所有请求共享同一个实例
        - Controller 必须设计为无状态（不在实例变量存储请求数据）
        - 请求相关数据通过方法参数传递

        Args:
            name: Controller 标识符

        Returns:
            Controller 实例，如果未找到则返回 None

        Raises:
            DependencyResolutionError: 如果依赖无法解析
        """
        # Fast path: 返回缓存的实例 (O(1)) - 读取不需要锁
        instance = self._controller_instances.get(name)
        if instance is not None:
            return instance

        # 检查 Controller 是否存在
        if name not in self._items:
            logger.debug(f"Controller not found: {name}")
            return None

        # 线程安全的单例创建（Double-check locking pattern）
        with self._instance_lock:
            # Double-check: 另一个线程可能已经创建了它
            instance = self._controller_instances.get(name)
            if instance is not None:
                return instance

            try:
                controller_class = self._items[name]

                # 【关键】直接实例化 Controller 类
                # @injectable 装饰器已经包装了 __init__，会在实例化后自动注入依赖
                instance = controller_class()

                # 立即缓存实例 (O(1))
                self._controller_instances[name] = instance

                logger.debug(f"Created controller singleton: {name} (dependencies injected by @injectable)")
                return instance

            except Exception as e:
                logger.error(f"Failed to instantiate controller {name}: {e}", exc_info=True)
                raise DependencyResolutionError(f"Failed to create controller {name}: {e}") from e

    def get_methods(self, controller_name: str) -> List[Tuple[str, str, Any]]:
        """Get all registered methods for a controller (O(1) lookup + copy).

        Args:
            controller_name: Name of the controller

        Returns:
            List of (url, http_method, handler_func) tuples (copy for safety)
        """
        if self._controller_methods is None:
            return []
        return self._controller_methods.get(controller_name, []).copy()

    def has_methods(self, controller_name: str) -> bool:
        """Check if controller has any methods registered (O(1) operation).

        Args:
            controller_name: Name of the controller

        Returns:
            True if controller has methods, False otherwise
        """
        if self._controller_methods is None:
            return False
        return controller_name in self._controller_methods and \
               len(self._controller_methods[controller_name]) > 0

    def get_method_count(self, controller_name: str) -> int:
        """Get number of methods for a controller (O(1) operation).

        Args:
            controller_name: Name of the controller

        Returns:
            Number of registered methods
        """
        if self._controller_methods is None:
            return 0
        return len(self._controller_methods.get(controller_name, []))

    def get_url_prefix(self, controller_name: str) -> Optional[str]:
        """Get the URL prefix for a controller (O(1) operation).

        Args:
            controller_name: Name of the controller

        Returns:
            URL prefix string, or None if controller not found
        """
        if self._metadata is None:
            return None
        metadata = self._metadata.get(controller_name)
        if metadata:
            return metadata.get('url_prefix', '')
        return None

    def clear(self) -> None:
        """Clear all registered controllers and methods.

        Useful for testing or application reinitialization.
        """
        super().clear()
        if self._controller_methods is not None:
            self._controller_methods.clear()
        logger.debug("Cleared all registered controllers")

    def count(self) -> int:
        """Get the number of registered controllers (O(1) operation).

        Returns:
            Number of registered controllers
        """
        return len(self._items)

    def list_all_methods(self) -> Dict[str, List[Tuple[str, str, Any]]]:
        """Get all registered methods for all controllers.

        Returns:
            Dictionary mapping controller names to their method lists (copy)
        """
        if self._controller_methods is None:
            return {}
        return {name: methods.copy() for name, methods in self._controller_methods.items()}

    # ========================================================================
    # ProviderSource Interface Implementation
    # ========================================================================

    def can_provide(self, name: str) -> bool:
        """Check if this registry can provide the given controller.

        Args:
            name: Controller name

        Returns:
            True if controller is registered
        """
        return name in self._items

    def provide(self, name: str) -> Optional[Any]:
        """Provide a controller instance.

        Args:
            name: Controller name

        Returns:
            Controller instance or None if not found
        """
        return self.get_instance(name)

    def list_available(self) -> List[str]:
        """List all available controller names.

        Returns:
            List of controller names
        """
        return list(self._items.keys())

    def get_priority(self) -> int:
        """Get the priority of this provider source.

        Returns:
            Priority value (5 for controllers, lower than services)
        """
        return 5


# Global controller registry instance (singleton pattern)
_global_controller_registry = ControllerRegistry()


def get_controller_registry() -> ControllerRegistry:
    """Get the global controller registry instance.

    Returns:
        The global ControllerRegistry instance
    """
    return _global_controller_registry


def reset_controller_registry() -> None:
    """Reset the global controller registry.

    Useful for testing to ensure clean state between tests.
    """
    _global_controller_registry.clear()
    logger.debug("Reset global controller registry")
