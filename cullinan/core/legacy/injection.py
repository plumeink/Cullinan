# -*- coding: utf-8 -*-
"""通用依赖注入系统 - Core 层基础设施

.. deprecated:: 2.0
    本模块已被弃用。请使用 2.0 的 ApplicationContext 和 Definition 系统。
    详见 docs/wiki/ioc_di_v2.md 和 docs/migration_guide_v2.md。

提供类似 Spring 的依赖注入功能，支持：
- 类型注解注入
- 延迟注入（与扫描顺序无关）
- 自动装配（基于类型或名称）
- 可选依赖和必需依赖

性能优化：
- 使用 __slots__ 减少内存占用
- 延迟解析依赖（首次使用时才解析）
- 缓存类型提示避免重复解析
"""

import warnings

# 弃用警告
warnings.warn(
    "cullinan.core.injection 模块已在 2.0 中弃用。"
    "请迁移到 cullinan.core.application_context.ApplicationContext。"
    "详见 docs/migration_guide_v2.md",
    DeprecationWarning,
    stacklevel=2
)

from typing import Type, Any, Dict, Optional, get_type_hints, Set, List, Tuple
import logging
import threading
from contextvars import ContextVar

from .registry import Registry
from .exceptions import RegistryError, CircularDependencyError
# Import ProviderSource interface (Task-1.3)
from .provider_source import ProviderSource

logger = logging.getLogger(__name__)

# 线程本地的解析栈，用于检测循环依赖
_resolving_stack: ContextVar[Set[str]] = ContextVar('_resolving_stack', default=None)


# ============================================================================
# 注入标记类
# ============================================================================

class Inject:
    """依赖注入描述符 - 类似 Spring 的 @Autowired（延迟加载）

    使用方式：
        class UserController:
            # 方式1: 自动推断（从类型注解）
            user_service: UserService = Inject()

            # 方式2: 指定名称
            auth: Any = Inject(name='AuthService')

            # 方式3: 可选依赖
            cache: Any = Inject(name='CacheService', required=False)

    特性:
    - 延迟加载：首次访问时才解析依赖
    - 自动推断：从类型注解或属性名推断服务名
    - 实例缓存：解析后缓存到实例，避免重复查找
    - 支持字符串注解：user_service: 'UserService' = Inject()
    - 支持测试 Mock：可手动设置属性值

    Args:
        name: 依赖名称（如果不指定，从属性名或类型推断）
        required: 是否必需（True 时找不到依赖会抛出异常）
    """

    __slots__ = ('name', 'required', '_attr_name', '_resolved_name', '_use_new_model')

    def __init__(self, name: Optional[str] = None, required: bool = True):
        self.name = name
        self.required = required
        self._attr_name = None
        self._resolved_name = None
        # Task-3.3: 启用新的统一模型
        self._use_new_model = True

    def __set_name__(self, owner, name):
        """当作为类属性时自动调用，获取属性名"""
        self._attr_name = name
        logger.debug(f"Registered Inject: {owner.__name__}.{name} -> {self.name or 'auto'}")

        # Task-3.3: 如果启用新模型，向 InjectionRegistry 注册元信息
        if self._use_new_model:
            self._register_injection_point(owner, name)

    def _register_injection_point(self, owner: Type, attr_name: str) -> None:
        """向 InjectionRegistry 注册注入点元信息（Task-3.3）"""
        try:
            from .injection_model import InjectionPoint, infer_dependency_name

            # 获取类型注解
            attr_type = None
            if hasattr(owner, '__annotations__'):
                attr_type = owner.__annotations__.get(attr_name)

            # 推断依赖名称
            dependency_name = infer_dependency_name(
                explicit_name=self.name,
                attr_name=attr_name,
                attr_type=attr_type
            )

            # 创建注入点
            point = InjectionPoint(
                attr_name=attr_name,
                dependency_name=dependency_name,
                required=self.required,
                attr_type=attr_type
            )

            # 注册到 InjectionRegistry
            registry = get_injection_registry()
            if hasattr(registry, 'register_injection_point'):
                registry.register_injection_point(owner, point)
                logger.debug(f"Registered InjectionPoint: {owner.__name__}.{attr_name} -> {dependency_name}")
        except ImportError:
            # 如果新模型未导入（向后兼容），使用旧逻辑
            logger.debug(f"New injection model not available, using legacy mode")
            self._use_new_model = False

    def __get__(self, instance, owner):
        """获取注入的依赖实例（延迟加载）"""
        if instance is None:
            return self

        # 检查实例字典中是否已缓存
        if self._attr_name:
            attr_value = instance.__dict__.get(self._attr_name)
            if attr_value is not None:
                return attr_value

        # Task-3.3: 使用统一执行器进行注入
        if self._use_new_model:
            value = self._inject_with_new_model(instance, owner)
            if value is not None or not self.required:
                return value
        
        # 如果新模型未启用或返回 None，抛出增强的错误信息
        if self.required:
            self._raise_detailed_error(instance, owner)
        return None

    def _raise_detailed_error(self, instance: Any, owner: Type) -> None:
        """抛出详细的错误信息，帮助用户诊断问题"""
        # 尝试解析依赖名称
        dep_name = self._resolve_name(owner) if hasattr(self, '_resolve_name') else 'Unknown'

        # 尝试获取可用的服务列表
        available_services = []
        try:
            from ..service import get_service_registry
            service_registry = get_service_registry()
            if hasattr(service_registry, 'list'):
                available_services = list(service_registry.list())
            elif hasattr(service_registry, '_items'):
                available_services = list(service_registry._items.keys())
        except Exception:
            pass

        error_msg = (
            f"Required dependency '{dep_name}' not found for "
            f"{owner.__name__}.{self._attr_name}.\n"
        )

        if available_services:
            error_msg += f"Available services: {', '.join(available_services)}\n"
        else:
            error_msg += "No services registered.\n"

        error_msg += (
            "\nPossible causes:\n"
            f"  1. Service '{dep_name}' not decorated with @service\n"
            "  2. Service module not scanned (check module location)\n"
            "  3. Service initialization failed (check logs)\n"
            "  4. Module not included in packaged environment\n"
            "\nSolutions:\n"
            "  - For packaged apps: Use cullinan.configure(explicit_services=[...])\n"
            "  - Check if service module is in correct location for scanning\n"
            "  - Add diagnostic logging to verify service registration\n"
        )

        raise RegistryError(error_msg)

    def _inject_with_new_model(self, instance: Any, owner: Type) -> Optional[Any]:
        """使用新的统一模型进行注入（Task-3.3）

        如果新模型失败，自动尝试回退到直接从 ServiceRegistry 获取。
        """
        try:
            from .injection_executor import get_injection_executor

            executor = get_injection_executor()
            registry = get_injection_registry()

            # 获取类的注入元数据
            if hasattr(registry, 'get_injection_metadata'):
                metadata = registry.get_injection_metadata(owner)
                if metadata:
                    # 只注入当前属性
                    point = metadata.get_injection_point(self._attr_name)
                    if point:
                        # 使用执行器解析并注入
                        value = executor.resolve_injection_point(instance, point)
                        if value is not None:
                            setattr(instance, self._attr_name, value)
                            logger.debug(f"Injected {point.dependency_name} using new model")
                        return value
        except (ImportError, AttributeError, RuntimeError) as e:
            # RuntimeError: InjectionExecutor not initialized - 回退到旧逻辑
            logger.debug(f"Failed to use new injection model: {e}, falling back to legacy")

        # 自动回退：直接从 ServiceRegistry 获取
        return self._fallback_inject(instance, owner)

    def _fallback_inject(self, instance: Any, owner: Type) -> Optional[Any]:
        """回退注入：直接从 ServiceRegistry 获取服务

        当新的注入模型失败时，尝试直接从 ServiceRegistry 获取服务实例。
        这提供了更好的容错性，特别是在打包环境中。
        """
        try:
            # 解析依赖名称
            dep_name = self._resolve_name(owner)

            from ..service import get_service_registry
            service_registry = get_service_registry()

            if service_registry.has(dep_name):
                value = service_registry.get_instance(dep_name)
                if value is not None:
                    setattr(instance, self._attr_name, value)
                    logger.info(
                        f"Injected {dep_name} using fallback "
                        f"(direct from ServiceRegistry) for "
                        f"{owner.__name__}.{self._attr_name}"
                    )
                    return value
        except Exception as fallback_error:
            logger.debug(f"Fallback injection also failed: {fallback_error}")

        return None

    def __set__(self, instance, value):
        """允许手动设置（用于测试 Mock）"""
        if self._attr_name:
            instance.__dict__[self._attr_name] = value

    def _resolve_name(self, owner_class: Type) -> str:
        """解析依赖名称（从 name、类型注解或属性名）

        Task-3.4: 使用统一的工具函数
        """
        from .injection_utils import resolve_dependency_name_from_annotation

        # 优先使用明确指定的名称
        if self.name:
            return self.name

        # 从类型注解推断
        if self._attr_name and hasattr(owner_class, '__annotations__'):
            anno = owner_class.__annotations__.get(self._attr_name)
            if anno:
                return resolve_dependency_name_from_annotation(None, self._attr_name, anno)

        # 回退到属性名
        if self._attr_name:
            from .injection_utils import convert_snake_to_pascal
            return convert_snake_to_pascal(self._attr_name)

        return 'Unknown'

    def __repr__(self):
        return f"Inject(name={self.name!r}, required={self.required})"


class InjectByName:
    """基于字符串名称的依赖注入描述符（延迟加载，完全无需 import）

    类似 Spring 的 @Autowired，但完全基于字符串名称，无需 import 依赖类。

    使用方式:
        from cullinan.core import InjectByName

        class UserController:
            # 方式1: 显式指定名称
            user_service = InjectByName('UserService')

            # 方式2: 根据属性名自动推断（user_service -> UserService）
            email_service = InjectByName()

            def get(self):
                # self.user_service 自动注入，延迟加载
                return self.user_service.get_all()

    特性:
    - 延迟加载：只在第一次访问时才注入
    - 自动推断：user_service -> UserService
    - 缓存机制：注入后缓存到实例，避免重复查找
    - 完全无需 import 依赖类
    - 支持测试 Mock
    """

    __slots__ = ('service_name', '_attr_name', 'required', '_use_new_model')

    def __init__(self, service_name: Optional[str] = None, required: bool = True):
        """初始化注入描述符

        Args:
            service_name: 依赖名称，如果为 None 则根据属性名自动推断
            required: 是否必需（True 时找不到依赖会抛出异常）
        """
        self.service_name = service_name
        self._attr_name = None
        self.required = required
        # Task-3.3 Step 4: 启用新的统一模型
        self._use_new_model = True

    def __set_name__(self, owner, name):
        """当作为类属性时自动调用，获取属性名"""
        self._attr_name = name

        # 如果没有指定 service_name，根据属性名自动推断
        # user_service -> UserService
        # email_service -> EmailService
        if self.service_name is None:
            self.service_name = ''.join(
                word.capitalize() for word in name.split('_')
            )

        logger.debug(f"Registered InjectByName: {owner.__name__}.{name} -> {self.service_name}")

        # Task-3.3 Step 4: 如果启用新模型，向 InjectionRegistry 注册元信息
        if self._use_new_model:
            self._register_injection_point(owner, name)

    def _register_injection_point(self, owner: Type, attr_name: str) -> None:
        """向 InjectionRegistry 注册注入点元信息（Task-3.3 Step 4）"""
        try:
            from .injection_model import InjectionPoint, ResolveStrategy

            # 创建注入点（使用 BY_NAME 策略）
            point = InjectionPoint(
                attr_name=attr_name,
                dependency_name=self.service_name,
                required=self.required,
                attr_type=None,  # InjectByName 不使用类型
                resolve_strategy=ResolveStrategy.BY_NAME
            )

            # 注册到 InjectionRegistry
            registry = get_injection_registry()
            if hasattr(registry, 'register_injection_point'):
                registry.register_injection_point(owner, point)
                logger.debug(f"Registered InjectionPoint (by name): {owner.__name__}.{attr_name} -> {self.service_name}")
        except ImportError:
            # 如果新模型未导入（向后兼容），使用旧逻辑
            logger.debug(f"New injection model not available, using legacy mode")
            self._use_new_model = False

    def __get__(self, instance, owner):
        """获取注入的依赖实例（延迟加载）"""
        if instance is None:
            return self

        # 检查实例字典中是否已缓存
        attr_value = instance.__dict__.get(self._attr_name)
        if attr_value is not None:
            return attr_value

        # Task-3.3 Step 4: 使用统一执行器进行注入
        if self._use_new_model:
            value = self._inject_with_new_model(instance, owner)
            if value is not None or not self.required:
                return value
        
        # 如果新模型未启用或返回 None，抛出增强的错误信息
        if self.required:
            self._raise_detailed_error(instance)
        return None

    def _raise_detailed_error(self, instance: Any) -> None:
        """抛出详细的错误信息，帮助用户诊断问题"""
        # 尝试获取可用的服务列表
        available_services = []
        try:
            from ..service import get_service_registry
            service_registry = get_service_registry()
            if hasattr(service_registry, 'list'):
                available_services = list(service_registry.list())
            elif hasattr(service_registry, '_items'):
                available_services = list(service_registry._items.keys())
        except Exception:
            pass

        error_msg = (
            f"Required dependency '{self.service_name}' not found for "
            f"{instance.__class__.__name__}.{self._attr_name}.\n"
        )

        if available_services:
            error_msg += f"Available services: {', '.join(available_services)}\n"
        else:
            error_msg += "No services registered.\n"

        error_msg += (
            "\nPossible causes:\n"
            f"  1. Service '{self.service_name}' not decorated with @service\n"
            "  2. Service module not scanned (check module location)\n"
            "  3. Service initialization failed (check logs)\n"
            "  4. Module not included in packaged environment\n"
            "\nSolutions:\n"
            "  - For packaged apps: Use cullinan.configure(explicit_services=[...])\n"
            "  - Check if service module is in correct location for scanning\n"
            "  - Add diagnostic logging to verify service registration\n"
        )

        raise RegistryError(error_msg)

    def _inject_with_new_model(self, instance: Any, owner: Type) -> Optional[Any]:
        """使用新的统一模型进行注入（Task-3.3 Step 4）

        如果新模型失败，自动尝试回退到直接从 ServiceRegistry 获取。
        """
        try:
            from .injection_executor import get_injection_executor

            executor = get_injection_executor()
            registry = get_injection_registry()

            # 获取类的注入元数据
            if hasattr(registry, 'get_injection_metadata'):
                metadata = registry.get_injection_metadata(owner)
                if metadata:
                    # 只注入当前属性
                    point = metadata.get_injection_point(self._attr_name)
                    if point:
                        # 使用执行器解析并注入
                        value = executor.resolve_injection_point(instance, point)
                        if value is not None:
                            setattr(instance, self._attr_name, value)
                            logger.debug(f"Injected {point.dependency_name} using new model (by name)")
                        return value
        except (ImportError, AttributeError, RuntimeError) as e:
            # RuntimeError: InjectionExecutor not initialized - 回退到旧逻辑
            logger.debug(f"Failed to use new injection model: {e}, falling back to legacy")

        # 自动回退：直接从 ServiceRegistry 获取
        return self._fallback_inject(instance)

    def _fallback_inject(self, instance: Any) -> Optional[Any]:
        """回退注入：直接从 ServiceRegistry 获取服务

        当新的注入模型失败时，尝试直接从 ServiceRegistry 获取服务实例。
        这提供了更好的容错性，特别是在打包环境中。
        """
        try:
            from ..service import get_service_registry
            service_registry = get_service_registry()

            if service_registry.has(self.service_name):
                value = service_registry.get_instance(self.service_name)
                if value is not None:
                    setattr(instance, self._attr_name, value)
                    logger.info(
                        f"Injected {self.service_name} using fallback "
                        f"(direct from ServiceRegistry) for "
                        f"{instance.__class__.__name__}.{self._attr_name}"
                    )
                    return value
        except Exception as fallback_error:
            logger.debug(f"Fallback injection also failed: {fallback_error}")

        return None

    def __set__(self, instance, value):
        """允许手动设置（用于测试 Mock）"""
        instance.__dict__[self._attr_name] = value

    def __repr__(self):
        return f"InjectByName(name={self.service_name!r}, required={self.required})"


# ============================================================================
# 依赖注入元数据
# ============================================================================

class InjectionMetadata:
    """注入元数据 - 记录类需要注入的信息

    性能优化：使用 __slots__ 减少内存占用
    """
    __slots__ = ('target_class', 'injections')

    def __init__(self, target_class: Type):
        self.target_class = target_class
        # {attribute_name: (dependency_name, required)}
        self.injections: Dict[str, tuple] = {}

    def add_injection(self, attr_name: str, dep_name: str, required: bool = True):
        """添加注入信息"""
        self.injections[attr_name] = (dep_name, required)

    def __repr__(self):
        return f"InjectionMetadata({self.target_class.__name__}, {len(self.injections)} injections)"


# ============================================================================
# 依赖注入注册表
# ============================================================================

class InjectionRegistry:
    """依赖注入注册表 - 管理所有需要注入的类

    职责：
    1. 扫描类的类型注解，记录注入需求
    2. 在运行时解析并注入依赖
    3. 支持多个依赖提供者（ProviderSource）
    4. 按优先级协调多个 ProviderSource

    Task-1.3 改进：
    - 使用 ProviderSource 接口而非具体的 Registry
    - 统一的依赖解析路径
    - 更清晰的层间职责
    """

    __slots__ = ('_metadata', '_provider_sources', '_type_hint_cache', '_lock', '_unified_metadata')

    def __init__(self):
        # {class: InjectionMetadata}
        self._metadata: Dict[Type, InjectionMetadata] = {}

        # Task-1.3: 使用 ProviderSource 接口
        # List of (priority, ProviderSource) tuples, sorted by priority (descending)
        self._provider_sources: List[Tuple[int, ProviderSource]] = []


        # 类型提示缓存
        self._type_hint_cache: Dict[Type, Dict] = {}
        # 线程锁
        self._lock = threading.RLock()

        # Task-3.3: 统一注入元数据
        self._unified_metadata: Dict[Type, 'UnifiedInjectionMetadata'] = {}

    def scan_class(self, cls: Type) -> InjectionMetadata:
        """扫描类的类型注解，记录需要注入的属性

        Task-3.3 Step 6: 优化性能
        - 优先检查统一元数据缓存
        - 减少重复扫描
        - 批量处理注入点

        Args:
            cls: 要扫描的类

        Returns:
            注入元数据对象
        """
        with self._lock:
            # 检查是否已有旧格式元数据
            if cls in self._metadata:
                return self._metadata[cls]

            # Task-3.3 Step 6: 检查是否已有统一元数据，如果有则转换
            if cls in self._unified_metadata:
                unified_meta = self._unified_metadata[cls]
                # 从统一元数据创建旧格式（向后兼容）
                metadata = InjectionMetadata(cls)
                for point in unified_meta.injection_points:  # 这是一个列表
                    metadata.add_injection(point.attr_name, point.dependency_name, point.required)
                self._metadata[cls] = metadata
                return metadata

            # 没有缓存，需要扫描
            metadata = InjectionMetadata(cls)

            try:
                # 获取类型提示（带缓存）
                hints = self._get_type_hints(cls)

                for attr_name, attr_type in hints.items():
                    # 检查是否有 Inject 标记
                    default_value = getattr(cls, attr_name, None)

                    if isinstance(default_value, Inject):
                        # 确定依赖名称
                        dep_name = self._resolve_dependency_name(
                            default_value.name,
                            attr_name,
                            attr_type
                        )

                        metadata.add_injection(attr_name, dep_name, default_value.required)
                        logger.debug(
                            f"Scan: {cls.__name__}.{attr_name} -> {dep_name} "
                            f"(required={default_value.required})"
                        )

            except Exception as e:
                logger.warning(f"Failed to scan {cls.__name__}: {e}")

            if metadata.injections:
                self._metadata[cls] = metadata
                logger.debug(f"Registered injection metadata for {cls.__name__}")

            return metadata

    def _get_type_hints(self, cls: Type) -> Dict:
        """获取类型提示（带缓存，支持字符串注解）

        支持：
        1. 标准类型注解: service: EmailService = Inject()
        2. 字符串注解: service: 'EmailService' = Inject()  (推荐，无需 import)
        3. 原始注解: 直接从 __annotations__ 读取
        """
        if cls not in self._type_hint_cache:
            try:
                # 尝试使用 get_type_hints（会解析字符串）
                self._type_hint_cache[cls] = get_type_hints(cls)
            except Exception as e:
                logger.debug(f"get_type_hints failed for {cls.__name__}: {e}, falling back to __annotations__")
                # 回退到直接使用 __annotations__（保留字符串）
                # 这样支持 'EmailService' 形式的注解，无需 import
                try:
                    self._type_hint_cache[cls] = getattr(cls, '__annotations__', {})
                except Exception as e2:
                    logger.debug(f"Could not get annotations for {cls.__name__}: {e2}")
                    self._type_hint_cache[cls] = {}
        return self._type_hint_cache[cls]

    def _resolve_dependency_name(self, explicit_name: Optional[str],
                                  attr_name: str, attr_type: Type) -> str:
        """解析依赖名称（Task-3.4: 使用统一工具函数）

        优先级：
        1. Inject(name='xxx') 明确指定的名称
        2. 从类型注解推断（支持字符串 'ServiceName' 和实际类型）
        3. 使用属性名转换
        """
        from .injection_utils import resolve_dependency_name_from_annotation
        return resolve_dependency_name_from_annotation(explicit_name, attr_name, attr_type)

    def add_provider_source(self, source: ProviderSource) -> None:
        """添加依赖提供源 (Task-1.3 新方法)

        使用 ProviderSource 接口，支持任何实现了该接口的依赖提供者。
        优先级从 source.get_priority() 获取。

        Args:
            source: 实现 ProviderSource 接口的依赖提供源

        Example:
            from cullinan.core import get_injection_registry
            from cullinan.service import get_service_registry

            injection_registry = get_injection_registry()
            service_registry = get_service_registry()

            # ServiceRegistry 实现了 ProviderSource 接口
            injection_registry.add_provider_source(service_registry)
        """
        with self._lock:
            priority = source.get_priority()
            self._provider_sources.append((priority, source))
            # 按优先级排序（降序）
            self._provider_sources.sort(key=lambda x: x[0], reverse=True)
            logger.debug(
                f"Added ProviderSource: {source.__class__.__name__} "
                f"(priority={priority})"
            )


    def inject(self, instance: Any) -> None:
        """注入依赖到实例

        .. deprecated:: 0.9
            推荐使用 InjectionExecutor.inject_instance() 代替。
            此方法将在 v1.0 移除。

        Args:
            instance: 要注入的实例

        Raises:
            RegistryError: 当必需的依赖找不到时
        """
        # Task-3.3 Step 6: 标记为废弃
        import warnings
        warnings.warn(
            "InjectionRegistry.inject() is deprecated. "
            "Use InjectionExecutor.inject_instance() instead. "
            "This method will be removed in v1.0.",
            DeprecationWarning,
            stacklevel=2
        )

        cls = type(instance)
        metadata = self._metadata.get(cls)

        if metadata is None:
            for base in cls.__mro__[1:]:
                if base in self._metadata:
                    metadata = self._metadata[base]
                    logger.debug(f"Found injection metadata for {cls.__name__} from base class {base.__name__}")
                    break

        if not metadata:
            return

        # Task-1.3: 检查 provider 源
        if not self._provider_sources:
            logger.warning(f"No provider source set, cannot inject {cls.__name__}")
            return

        for attr_name, (dep_name, required) in metadata.injections.items():
            try:
                # 从提供者注册表获取依赖对象
                dep_instance = self._resolve_dependency(dep_name)

                if dep_instance is None:
                    if required:
                        raise RegistryError(
                            f"Required dependency not found: {dep_name} "
                            f"for {cls.__name__}.{attr_name}"
                        )
                    else:
                        logger.debug(
                            f"Optional dependency not found: {dep_name}, "
                            f"skipping {cls.__name__}.{attr_name}"
                        )
                        continue

                # 注入！
                setattr(instance, attr_name, dep_instance)
                logger.debug(f"Injected {dep_name} -> {cls.__name__}.{attr_name}")

            except Exception as e:
                logger.error(f"Injection failed for {cls.__name__}.{attr_name}: {e}")
                if required:
                    raise

    def _resolve_dependency(self, name: str) -> Optional[Any]:
        """从提供者解析依赖（按优先级），带循环依赖检测

        Task-1.3: 使用 ProviderSource 接口

        Args:
            name: 依赖名称

        Returns:
            依赖实例，或 None

        Raises:
            CircularDependencyError: 如果检测到循环依赖
        """
        # 获取当前线程的解析栈
        resolving = _resolving_stack.get()
        if resolving is None:
            resolving = set()
            _resolving_stack.set(resolving)

        # 检测循环依赖
        if name in resolving:
            cycle_path = ' -> '.join(list(resolving) + [name])
            raise CircularDependencyError(
                f"Circular dependency detected: {cycle_path}"
            )

        # 将当前依赖加入解析栈
        resolving.add(name)
        try:
            # Task-1.3: 使用 ProviderSource 接口
            for priority, source in self._provider_sources:
                if source.can_provide(name):
                    try:
                        dep = source.provide(name)
                        if dep is not None:
                            logger.debug(
                                f"Resolved '{name}' from {source.__class__.__name__} "
                                f"(priority={priority})"
                            )
                            return dep
                    except Exception as e:
                        logger.debug(
                            f"ProviderSource {source.__class__.__name__} "
                            f"failed to provide '{name}': {e}"
                        )


            return None
        finally:
            # 从解析栈中移除
            resolving.discard(name)
            if not resolving:
                _resolving_stack.set(None)

    # ========================================================================
    # Task-3.3: 新的统一注入模型支持
    # ========================================================================

    def register_injection_point(self, cls: Type, point: 'InjectionPoint') -> None:
        """注册注入点到类（Task-3.3 新方法）

        Args:
            cls: 目标类
            point: InjectionPoint 对象
        """
        try:
            from .injection_model import UnifiedInjectionMetadata, InjectionPoint

            # 获取或创建 UnifiedInjectionMetadata
            if cls not in self._unified_metadata:
                self._unified_metadata[cls] = UnifiedInjectionMetadata(cls)

            self._unified_metadata[cls].add_injection_point(point)
            logger.debug(
                f"Registered InjectionPoint: {cls.__name__}.{point.attr_name} -> "
                f"{point.dependency_name}"
            )
        except ImportError as e:
            logger.debug(f"Unified injection model not available: {e}")

    def get_injection_metadata(self, cls: Type) -> Optional['UnifiedInjectionMetadata']:
        """获取类的统一注入元数据（Task-3.3 新方法）

        Args:
            cls: 目标类

        Returns:
            UnifiedInjectionMetadata 对象，或 None
        """
        return self._unified_metadata.get(cls)

    def get_metadata(self, cls: Type, prefer_unified: bool = True) -> Optional[Any]:
        """获取类的注入元数据（统一接口）

        Task-3.3 Step 6: 统一元数据访问接口

        Args:
            cls: 目标类
            prefer_unified: 是否优先返回统一元数据

        Returns:
            元数据对象（UnifiedInjectionMetadata 或 InjectionMetadata），或 None
        """
        if prefer_unified:
            # 优先返回统一元数据
            unified = self._unified_metadata.get(cls)
            if unified:
                return unified
            # 如果没有，返回旧元数据
            return self._metadata.get(cls)
        else:
            # 优先返回旧元数据
            old = self._metadata.get(cls)
            if old:
                return old
            # 如果没有，返回统一元数据
            return self._unified_metadata.get(cls)

    # ========================================================================
    # END Task-3.3
    # ========================================================================

    def has_injections(self, cls: Type) -> bool:
        """检查类是否需要依赖注入

        Task-3.3 Step 6: 支持统一元数据

        Args:
            cls: 要检查的类

        Returns:
            True 如果需要注入，否则 False
        """
        # 检查两种元数据存储
        return cls in self._metadata or cls in self._unified_metadata

    def get_injection_info(self, cls: Type) -> Optional[Dict[str, tuple]]:
        """获取类的注入信息（用于调试）

        Task-3.3 Step 6: 支持统一元数据

        Args:
            cls: 要查询的类

        Returns:
            注入信息字典，或 None
        """
        # 优先返回旧格式元数据
        metadata = self._metadata.get(cls)
        if metadata:
            return metadata.injections

        # 如果没有旧格式，尝试从统一元数据转换
        unified_meta = self._unified_metadata.get(cls)
        if unified_meta:
            # 转换为旧格式: {attr_name: (dependency_name, required)}
            return {
                point.attr_name: (point.dependency_name, point.required)
                for point in unified_meta.injection_points  # 这是一个列表
            }

        return None

    def clear(self) -> None:
        """清空所有注入元数据"""
        with self._lock:
            self._metadata.clear()
            self._provider_sources.clear()
            self._type_hint_cache.clear()
            self._unified_metadata.clear()
            logger.debug("Cleared injection registry")


# 全局注入注册表实例
_global_injection_registry = InjectionRegistry()


def get_injection_registry() -> InjectionRegistry:
    """获取全局注入注册表

    Returns:
        全局 InjectionRegistry 实例
    """
    return _global_injection_registry


def reset_injection_registry() -> None:
    """重置全局注入注册表（用于测试）"""
    _global_injection_registry.clear()
    logger.debug("Reset global injection registry")


# ============================================================================
# 装饰器：自动扫描和注入
# ============================================================================

def injectable(cls: Optional[Type] = None):
    """标记类可注入 - 自动扫描类型注解并在实例化时注入

    使用方式：
        @injectable
        class UserController:
            user_service: UserService = Inject()

    注意：
    - 装饰器会包装 __init__ 方法
    - 在 __init__ 执行后自动注入依赖
    - 与扫描顺序无关（延迟注入）

    Args:
        cls: 要标记的类

    Returns:
        包装后的类（在 __init__ 时自动注入）
    """
    def decorator(target_class: Type) -> Type:
        # 1. 扫描类的注入需求
        registry = get_injection_registry()
        registry.scan_class(target_class)

        # 2. 包装 __init__，在实例化后自动注入
        original_init = target_class.__init__

        # 使用 functools.wraps 保留原始函数的元数据
        import functools

        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            # 调用原始 __init__
            original_init(self, *args, **kwargs)

            # Task-3.3 Step 5: 使用统一的 InjectionExecutor 进行注入
            try:
                from .injection_executor import get_injection_executor, has_injection_executor

                if has_injection_executor():
                    executor = get_injection_executor()
                    metadata = registry.get_injection_metadata(target_class)

                    if metadata and metadata.has_injections():
                        executor.inject_instance(self, metadata)
                        logger.debug(f"Injected dependencies for {target_class.__name__} using InjectionExecutor")
                        return
            except (ImportError, AttributeError, RuntimeError) as e:
                logger.error(f"InjectionExecutor not available: {e}")
                raise RegistryError(
                    f"Failed to inject dependencies for {target_class.__name__}: "
                    f"InjectionExecutor not properly initialized"
                ) from e

        target_class.__init__ = new_init

        logger.debug(f"Marked {target_class.__name__} as injectable")
        return target_class

    # 支持 @injectable 和 @injectable()
    if cls is None:
        return decorator
    else:
        return decorator(cls)


# ============================================================================
# 构造器注入装饰器
# ============================================================================

def inject_constructor(cls: Optional[Type] = None):
    """构造器注入装饰器 - 自动解析并注入构造函数参数

    与 @injectable 不同，此装饰器在调用 __init__ 之前解析参数并注入。
    适用于需要在构造时传入依赖的场景。

    使用方式：
        @inject_constructor
        class UserController:
            def __init__(self, user_service: UserService, config: Config):
                self.user_service = user_service
                self.config = config

    混合使用：
        @inject_constructor
        @injectable
        class UserController:
            # 构造器注入（必需）
            def __init__(self, user_service: UserService):
                self.user_service = user_service

            # 属性注入（可选）
            cache: Cache = Inject(required=False)

    Args:
        cls: 要装饰的类

    Returns:
        包装后的类
    """
    import inspect
    from typing import get_type_hints
    import functools

    def decorator(target_class: Type) -> Type:
        original_init = target_class.__init__

        try:
            # 获取构造函数签名和类型提示
            sig = inspect.signature(original_init)
            hints = get_type_hints(original_init)
        except Exception as e:
            logger.warning(f"Cannot get signature for {target_class.__name__}.__init__: {e}")
            return target_class

        # 分析需要注入的参数
        injectable_params = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 获取参数类型
            param_type = hints.get(param_name)
            if param_type is None:
                continue

            # 判断是否必需
            required = param.default == inspect.Parameter.empty
            injectable_params[param_name] = (param_type, required)

        if not injectable_params:
            # 没有可注入的参数，直接返回
            return target_class

        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            # 解析并注入依赖
            registry = get_injection_registry()

            # 绑定已提供的参数
            try:
                bound_args = sig.bind_partial(self, *args, **kwargs)
            except TypeError:
                # 如果绑定失败，直接调用原始构造函数（让它抛出正确的错误）
                original_init(self, *args, **kwargs)
                return

            # 为未提供的参数注入依赖
            for param_name, (param_type, required) in injectable_params.items():
                if param_name not in bound_args.arguments:
                    # 参数未提供，尝试从注册表解析
                    dep_name = param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)
                    dep_instance = registry._resolve_dependency(dep_name)

                    if dep_instance is None:
                        if required:
                            raise RegistryError(
                                f"Cannot inject required parameter '{param_name}' "
                                f"of type '{dep_name}' in {target_class.__name__}.__init__. "
                                f"Ensure it's registered with @service or in a registry."
                            )
                        # 可选参数未找到，使用默认值（如果有的话）
                    else:
                        kwargs[param_name] = dep_instance
                        logger.debug(f"Injected {dep_name} into {target_class.__name__}.__init__({param_name})")

            # 调用原始构造函数
            original_init(self, *args, **kwargs)

        target_class.__init__ = new_init
        logger.debug(f"Enabled constructor injection for {target_class.__name__}")
        return target_class

    # 支持 @inject_constructor 和 @inject_constructor()
    if cls is None:
        return decorator
    else:
        return decorator(cls)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    'Inject',
    'InjectByName',
    'InjectionRegistry',
    'InjectionMetadata',
    'get_injection_registry',
    'reset_injection_registry',
    'injectable',
    'inject_constructor',  # 新增
]
