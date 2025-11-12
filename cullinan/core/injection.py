# -*- coding: utf-8 -*-
"""通用依赖注入系统 - Core 层基础设施

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

from typing import Type, Any, Dict, Optional, get_type_hints
from dataclasses import dataclass
import logging
import inspect

from .registry import Registry
from .exceptions import RegistryError

logger = logging.getLogger(__name__)


# ============================================================================
# 注入标记类
# ============================================================================

@dataclass
class Inject:
    """依赖注入标记 - 类似 Spring 的 @Autowired

    使用方式：
        class UserController:
            # 方式1: 自动推断（从类型注解）
            user_service: UserService = Inject()

            # 方式2: 指定名称
            auth: Any = Inject(name='AuthService')

            # 方式3: 可选依赖
            cache: Any = Inject(name='CacheService', required=False)

    Args:
        name: 依赖名称（如果不指定，从属性名或类型推断）
        required: 是否必需（True 时找不到依赖会抛出异常）
    """
    name: Optional[str] = None
    required: bool = True

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

    __slots__ = ('service_name', '_attr_name', 'required')

    def __init__(self, service_name: Optional[str] = None, required: bool = True):
        """初始化注入描述符

        Args:
            service_name: 依赖名称，如果为 None 则根据属性名自动推断
            required: 是否必需（True 时找不到依赖会抛出异常）
        """
        self.service_name = service_name
        self._attr_name = None
        self.required = required

    def __set_name__(self, owner, name):
        """当作为类属性时��动调用，获取属性名"""
        self._attr_name = name

        # 如果没有指定 service_name，根据属性名自动推断
        # user_service -> UserService
        # email_service -> EmailService
        if self.service_name is None:
            self.service_name = ''.join(
                word.capitalize() for word in name.split('_')
            )

        logger.debug(f"Registered InjectByName: {owner.__name__}.{name} -> {self.service_name}")

    def __get__(self, instance, owner):
        """获取注入的依赖实例（延迟加载）"""
        if instance is None:
            return self

        # 检查实例字典中是否已缓存
        attr_value = instance.__dict__.get(self._attr_name)
        if attr_value is not None:
            return attr_value

        # 从全局注入注册表解析依赖
        registry = get_injection_registry()
        dependency = registry._resolve_dependency(self.service_name)

        if dependency is None:
            if self.required:
                raise RegistryError(
                    f"Required dependency '{self.service_name}' not found for "
                    f"{instance.__class__.__name__}.{self._attr_name}. "
                    f"Ensure it's registered with appropriate decorator."
                )
            else:
                logger.debug(
                    f"Optional dependency '{self.service_name}' not found, "
                    f"returning None for {instance.__class__.__name__}.{self._attr_name}"
                )
                return None

        # 缓存到实例字典，下次访问直接返回（O(1)）
        instance.__dict__[self._attr_name] = dependency
        logger.debug(
            f"Injected {self.service_name} into "
            f"{instance.__class__.__name__}.{self._attr_name}"
        )

        return dependency

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
    3. 支持多个依赖提供者（Registry）
    """

    __slots__ = ('_metadata', '_provider_registries', '_type_hint_cache')

    def __init__(self):
        # {class: InjectionMetadata}
        self._metadata: Dict[Type, InjectionMetadata] = {}
        # 依赖提供者注册表列表（按优先级查找）
        self._provider_registries: list = []
        # 类型提示缓存
        self._type_hint_cache: Dict[Type, Dict] = {}

    def scan_class(self, cls: Type) -> InjectionMetadata:
        """扫描类的类型注解，记录需要注入的属性

        Args:
            cls: 要扫描的类

        Returns:
            注入元数据对象
        """
        if cls in self._metadata:
            return self._metadata[cls]

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
        """解析依赖名称（支持字符串类型注解，像 SpringBoot 一样无需 import）

        优先级：
        1. Inject(name='xxx') 明确指定的名称
        2. 从类型注解推断（支持字符串 'ServiceName' 和实际类型）
        3. 使用属性名

        示例：
            # 方式1: 字符串注解（无需 import，推荐）
            email_service: 'EmailService' = Inject()

            # 方式2: 实际类型（需要 import）
            email_service: EmailService = Inject()

            # 方式3: 显式指定
            email_service = Inject(name='EmailService')
        """
        if explicit_name:
            return explicit_name

        # 支持字符串类型注解（像 Spring 一样无需 import）
        if isinstance(attr_type, str):
            # 'EmailService' -> 'EmailService'
            return attr_type

        # 尝试从类型推断
        if attr_type is not Any and hasattr(attr_type, '__name__'):
            return attr_type.__name__

        # 回退到属性名（驼峰转类名）
        # 例如: email_service -> EmailService
        if '_' in attr_name:
            # snake_case -> PascalCase
            return ''.join(word.capitalize() for word in attr_name.split('_'))

        return attr_name

    def add_provider_registry(self, registry: Registry, priority: int = 0) -> None:
        """添加依赖提供者注册表

        Args:
            registry: 提供依赖对象的注册表（如 ServiceRegistry）
            priority: 优先级（数字越大优先级越高）
        """
        self._provider_registries.append((priority, registry))
        # 按优先级排序（降序）
        self._provider_registries.sort(key=lambda x: x[0], reverse=True)
        logger.debug(f"Added provider: {registry.__class__.__name__} (priority={priority})")

    def inject(self, instance: Any) -> None:
        """注入依赖到实例

        Args:
            instance: 要注入的实例

        Raises:
            RegistryError: 当必需的依赖找不到时
        """
        cls = type(instance)
        metadata = self._metadata.get(cls)

        if not metadata:
            return

        if not self._provider_registries:
            logger.warning(f"No provider registry set, cannot inject {cls.__name__}")
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
        """从提供者注册表解析依赖（按优先级）

        Args:
            name: 依赖名称

        Returns:
            依赖实例，或 None
        """
        for priority, registry in self._provider_registries:
            # 尝试从注册表获取实例
            dep = None

            if hasattr(registry, 'get_instance'):
                # 优先使用 get_instance（适用于 ServiceRegistry）
                try:
                    dep = registry.get_instance(name)
                except Exception as e:
                    logger.debug(f"get_instance failed for {name}: {e}")

            if dep is None and hasattr(registry, 'get'):
                # 回退：直接从注册表获取
                dep = registry.get(name)

            if dep is not None:
                return dep

        return None

    def has_injections(self, cls: Type) -> bool:
        """检查类是否需要依赖注入

        Args:
            cls: 要检查的类

        Returns:
            True 如果需要注入，否则 False
        """
        return cls in self._metadata

    def get_injection_info(self, cls: Type) -> Optional[Dict[str, tuple]]:
        """获取类的注入信息（用于调试）

        Args:
            cls: 要查询的类

        Returns:
            注入信息字典，或 None
        """
        metadata = self._metadata.get(cls)
        return metadata.injections if metadata else None

    def clear(self) -> None:
        """清空所有注入元数据"""
        self._metadata.clear()
        self._provider_registries.clear()
        self._type_hint_cache.clear()
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
            # 自动注入依赖
            try:
                registry.inject(self)
            except Exception as e:
                logger.error(f"Injection failed during {target_class.__name__}.__init__: {e}")
                raise

        target_class.__init__ = new_init

        logger.debug(f"Marked {target_class.__name__} as injectable")
        return target_class

    # 支持 @injectable 和 @injectable()
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
]

