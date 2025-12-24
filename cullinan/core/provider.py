# -*- coding: utf-8 -*-
"""Provider 抽象 - 依赖提供者系统

提供统一的依赖提供接口，支持：
- 实例提供者（直接返回实例）
- 类提供者（实例化类）
- 工厂提供者（调用工厂函数）
- 单例和瞬时作用域

类似 Spring 的 Provider 接口，为 DI 容器提供灵活的实例创建方式。
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Callable, Optional, Any, Dict, List
import threading
import logging

# Import ProviderSource interface (Task-1.3)
from .provider_source import ProviderSource

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Provider(ABC, Generic[T]):
    """依赖提供者抽象基类

    定义了获取依赖实例的统一接口。
    Provider 负责创建、缓存和返回依赖实例。
    """

    @abstractmethod
    def get(self) -> T:
        """获取依赖实例

        Returns:
            依赖实例对象
        """
        pass

    @abstractmethod
    def is_singleton(self) -> bool:
        """判断是否为单例模式

        Returns:
            True 表示单例，False 表示每次创建新实例
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(singleton={self.is_singleton()})"


class InstanceProvider(Provider[T]):
    """实例提供者 - 直接返回已有实例

    用于注册已经创建好的实例对象。
    总是单例模式。

    Example:
        config = Config()
        provider = InstanceProvider(config)
        assert provider.get() is config
    """

    __slots__ = ('_instance',)

    def __init__(self, instance: T):
        """初始化实例提供者

        Args:
            instance: 要提供的实例对象
        """
        if instance is None:
            raise ValueError("Instance cannot be None")
        self._instance = instance

    def get(self) -> T:
        """返回实例

        Returns:
            始终返回构造时传入的实例
        """
        return self._instance

    def is_singleton(self) -> bool:
        """始终为单例

        Returns:
            True
        """
        return True

    def __repr__(self) -> str:
        return f"InstanceProvider(instance={self._instance!r})"


class ClassProvider(Provider[T]):
    """类提供者 - 实例化类

    通过实例化指定的类来提供依赖。
    支持单例和瞬时两种模式。

    Example:
        # 单例模式
        provider = ClassProvider(UserService, singleton=True)
        s1 = provider.get()
        s2 = provider.get()
        assert s1 is s2

        # 瞬时模式
        provider = ClassProvider(TempData, singleton=False)
        t1 = provider.get()
        t2 = provider.get()
        assert t1 is not t2
    """

    __slots__ = ('_cls', '_singleton', '_instance', '_lock')

    def __init__(self, cls: type, singleton: bool = True):
        """初始化类提供者

        Args:
            cls: 要实例化的类
            singleton: 是否为单例模式
        """
        if not isinstance(cls, type):
            raise TypeError(f"Expected type, got {type(cls)}")
        self._cls = cls
        self._singleton = singleton
        self._instance: Optional[T] = None
        self._lock = threading.RLock()

    def get(self) -> T:
        """获取实例

        如果是单例模式，首次调用时创建实例并缓存。
        如果是瞬时模式，每次都创建新实例。

        Returns:
            类的实例
        """
        if self._singleton:
            with self._lock:
                if self._instance is None:
                    logger.debug(f"Creating singleton instance of {self._cls.__name__}")
                    self._instance = self._cls()
                return self._instance
        else:
            logger.debug(f"Creating transient instance of {self._cls.__name__}")
            return self._cls()

    def is_singleton(self) -> bool:
        """返回是否为单例

        Returns:
            单例标志
        """
        return self._singleton

    def __repr__(self) -> str:
        return f"ClassProvider(cls={self._cls.__name__}, singleton={self._singleton})"


class FactoryProvider(Provider[T]):
    """工厂提供者 - 调用工厂函数

    通过调用工厂函数来提供依赖。
    支持单例和瞬时两种模式。

    Example:
        def create_database():
            return Database(host='localhost')

        # 单例模式
        provider = FactoryProvider(create_database, singleton=True)
        db1 = provider.get()
        db2 = provider.get()
        assert db1 is db2

        # 瞬时模式
        provider = FactoryProvider(lambda: TempFile(), singleton=False)
        f1 = provider.get()
        f2 = provider.get()
        assert f1 is not f2
    """

    __slots__ = ('_factory', '_singleton', '_instance', '_lock')

    def __init__(self, factory: Callable[[], T], singleton: bool = False):
        """初始化工厂提供者

        Args:
            factory: 无参数的工厂函数，返回实例
            singleton: 是否为单例模式
        """
        if not callable(factory):
            raise TypeError(f"Factory must be callable, got {type(factory)}")
        self._factory = factory
        self._singleton = singleton
        self._instance: Optional[T] = None
        self._lock = threading.RLock()

    def get(self) -> T:
        """获取实例

        如果是单例模式，首次调用工厂函数并缓存结果。
        如果是瞬时模式，每次都调用工厂函数。

        Returns:
            工厂函数返回的实例
        """
        if self._singleton:
            with self._lock:
                if self._instance is None:
                    logger.debug(f"Calling factory function (singleton)")
                    self._instance = self._factory()
                return self._instance
        else:
            logger.debug(f"Calling factory function (transient)")
            return self._factory()

    def is_singleton(self) -> bool:
        """返回是否为单例

        Returns:
            单例标志
        """
        return self._singleton

    def __repr__(self) -> str:
        return f"FactoryProvider(factory={self._factory}, singleton={self._singleton})"


class ScopedProvider(Provider[T]):
    """带作用域的提供者

    通过 Scope 控制实例的生命周期。
    结合 Provider 和 Scope，提供灵活的依赖管理。

    Example:
        from cullinan.core.scope import SingletonScope

        provider = ScopedProvider(
            lambda: UserService(),
            SingletonScope(),
            'UserService'
        )
    """

    __slots__ = ('_factory', '_scope', '_key')

    def __init__(self, factory: Callable[[], T], scope: Any, key: str):
        """初始化带作用域的提供者

        Args:
            factory: 创建实例的工厂函数
            scope: 作用域对象
            key: 在作用域中的唯一标识
        """
        if not callable(factory):
            raise TypeError(f"Factory must be callable, got {type(factory)}")
        if scope is None:
            raise ValueError("Scope cannot be None")
        if not key:
            raise ValueError("Key cannot be empty")

        self._factory = factory
        self._scope = scope
        self._key = key

    def get(self) -> T:
        """通过作用域获取实例

        Returns:
            作用域管理的实例
        """
        return self._scope.get(self._key, self._factory)

    def is_singleton(self) -> bool:
        """判断是否为单例

        Returns:
            是否为单例
        """
        from .scope import SingletonScope
        return isinstance(self._scope, SingletonScope)

    def get_scope(self) -> Any:
        """获取作用域对象

        Returns:
            Scope 实例
        """
        return self._scope

    def __repr__(self) -> str:
        return f"ScopedProvider(scope={self._scope}, key='{self._key}')"


class ProviderRegistry(ProviderSource):
    """Provider 注册表 (实现 ProviderSource 接口)

    管理 Provider 的注册和查找。
    支持通过名称或类型注册 Provider。

    实现 ProviderSource 接口，可以作为 InjectionRegistry 的依赖提供源。
    这样 InjectionRegistry 只需要依赖抽象接口，而不是具体的 ProviderRegistry。

    优先级：默认为 5（低优先级）
    """

    __slots__ = ('_providers', '_lock', '_priority')

    def __init__(self, priority: int = 5):
        """初始化 Provider 注册表

        Args:
            priority: 优先级（默认 5，低优先级）
        """
        self._providers: Dict[str, Provider] = {}
        self._lock = threading.RLock()
        self._priority = priority

    def register_provider(self, name: str, provider: Provider) -> None:
        """注册 Provider

        Args:
            name: Provider 名称
            provider: Provider 实例
        """
        with self._lock:
            if name in self._providers:
                logger.warning(f"Provider already registered: {name}, replacing")
            self._providers[name] = provider
            logger.debug(f"Registered provider: {name} -> {provider}")

    def register_instance(self, name: str, instance: Any) -> None:
        """注册实例（快捷方法）

        Args:
            name: 实例名称
            instance: 实例对象
        """
        provider = InstanceProvider(instance)
        self.register_provider(name, provider)

    def register_class(self, name: str, cls: type, singleton: bool = True) -> None:
        """注册类（快捷方法）

        Args:
            name: 类名称
            cls: 类对象
            singleton: 是否为单例
        """
        provider = ClassProvider(cls, singleton=singleton)
        self.register_provider(name, provider)

    def register_factory(self, name: str, factory: Callable[[], Any],
                        singleton: bool = False) -> None:
        """注册工厂（快捷方法）

        Args:
            name: 工厂名称
            factory: 工厂函数
            singleton: 是否为单例
        """
        provider = FactoryProvider(factory, singleton=singleton)
        self.register_provider(name, provider)

    def get_provider(self, name: str) -> Optional[Provider]:
        """获取 Provider

        Args:
            name: Provider 名称

        Returns:
            Provider 实例，如果不存在则返回 None
        """
        return self._providers.get(name)

    def get_instance(self, name: str) -> Optional[Any]:
        """获取实例（通过 Provider）

        Args:
            name: 实例名称

        Returns:
            实例对象，如果 Provider 不存在则返回 None
        """
        provider = self.get_provider(name)
        if provider is None:
            return None
        return provider.get()

    def has_provider(self, name: str) -> bool:
        """检查是否存在 Provider

        Args:
            name: Provider 名称

        Returns:
            True 如果存在，否则 False
        """
        return name in self._providers

    def unregister(self, name: str) -> bool:
        """取消注册 Provider

        Args:
            name: Provider 名称

        Returns:
            True 如果成功取消，False 如果不存在
        """
        with self._lock:
            if name in self._providers:
                del self._providers[name]
                logger.debug(f"Unregistered provider: {name}")
                return True
            return False

    def clear(self) -> None:
        """清空所有 Provider"""
        with self._lock:
            self._providers.clear()
            logger.debug("Cleared all providers")

    def count(self) -> int:
        """返回 Provider 数量

        Returns:
            Provider 数量
        """
        return len(self._providers)

    def list_names(self) -> list[str]:
        """列出所有 Provider 名称

        Returns:
            Provider 名称列表
        """
        return list(self._providers.keys())

    # ========================================================================
    # ProviderSource Interface Implementation (Task-1.3)
    # ========================================================================

    def can_provide(self, name: str) -> bool:
        """检查是否能提供指定名称的依赖 (ProviderSource 接口)

        Args:
            name: 依赖名称

        Returns:
            True 表示可以提供，False 表示不能提供
        """
        return self.has_provider(name)

    def provide(self, name: str) -> Optional[Any]:
        """提供指定名称的依赖实例 (ProviderSource 接口)

        Args:
            name: 依赖名称

        Returns:
            依赖实例，如果无法提供则返回 None
        """
        return self.get_instance(name)

    def list_available(self) -> List[str]:
        """列出所有可用的依赖名称 (ProviderSource 接口)

        Returns:
            依赖名称列表
        """
        return self.list_names()

    def get_priority(self) -> int:
        """获取此 ProviderSource 的优先级 (ProviderSource 接口)

        Returns:
            优先级数值，越大越优先
        """
        return self._priority


__all__ = [
    'Provider',
    'InstanceProvider',
    'ClassProvider',
    'FactoryProvider',
    'ScopedProvider',
    'ProviderRegistry',
]

