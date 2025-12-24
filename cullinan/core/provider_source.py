# -*- coding: utf-8 -*-
"""Provider Source 抽象接口 - IoC/DI 系统的依赖提供源

定义统一的依赖提供接口，让所有提供依赖的 Registry 实现该接口。
这样 InjectionRegistry 只需要依赖抽象接口，而不是具体实现。

设计原则：
- 依赖倒置：上层依赖抽象而非具体
- 接口隔离：只暴露必要的方法
- 单一职责：只负责依赖提供，不管理生命周期

作者：Plumeink
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, List


class ProviderSource(ABC):
    """依赖提供源抽象接口

    所有提供依赖实例的 Registry 都应该实现此接口。
    这样 InjectionRegistry 只需要依赖抽象接口，而不是具体实现。

    实现此接口的类包括：
    - ProviderRegistry: 提供 ClassProvider、InstanceProvider、FactoryProvider 实例
    - ServiceRegistry: 提供 Service 实例（带生命周期管理）
    - 其他自定义 Registry（扩展）

    设计要点：
    1. 只定义"提供依赖"的能力，不涉及注册、生命周期等
    2. 支持优先级，让 InjectionRegistry 按优先级查询
    3. 接口方法应该高效（O(1) 或 O(log n)）

    Example:
        # 实现自定义 ProviderSource
        class ConfigRegistry(ProviderSource):
            def can_provide(self, name: str) -> bool:
                return name in self._configs

            def provide(self, name: str) -> Optional[Any]:
                return self._configs.get(name)

            def list_available(self) -> List[str]:
                return list(self._configs.keys())

            def get_priority(self) -> int:
                return 50  # Higher priority than default

        # 注册到 InjectionRegistry
        injection_registry.add_provider_source(ConfigRegistry())
    """

    @abstractmethod
    def can_provide(self, name: str) -> bool:
        """检查是否能提供指定名称的依赖

        此方法应该高效（O(1)），因为会被频繁调用。

        Args:
            name: 依赖名称（通常是类名或服务名）

        Returns:
            True 表示可以提供，False 表示不能提供

        Example:
            >>> source.can_provide('UserService')
            True
            >>> source.can_provide('NonExistentService')
            False
        """
        pass

    @abstractmethod
    def provide(self, name: str) -> Optional[Any]:
        """提供指定名称的依赖实例

        仅在 can_provide() 返回 True 后调用。
        如果依赖存在但创建失败，应该抛出异常而非返回 None。

        Args:
            name: 依赖名称

        Returns:
            依赖实例，如果无法提供则返回 None

        Raises:
            DependencyResolutionError: 如果依赖解析失败
            CircularDependencyError: 如果存在循环依赖

        Example:
            >>> instance = source.provide('UserService')
            >>> assert instance is not None
            >>> assert isinstance(instance, UserService)
        """
        pass

    @abstractmethod
    def list_available(self) -> List[str]:
        """列出所有可用的依赖名称

        用于调试和诊断，不需要高性能。

        Returns:
            依赖名称列表

        Example:
            >>> names = source.list_available()
            >>> print(names)
            ['UserService', 'EmailService', 'CacheService']
        """
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """获取此 ProviderSource 的优先级

        InjectionRegistry 按优先级从高到低依次查询。
        优先级范围建议：
        - 100+: 高优先级（如配置、环境变量）
        - 10-99: 正常优先级（如 ServiceRegistry）
        - 1-9: 低优先级（如默认值、fallback）
        - 0: 最低优先级

        Returns:
            优先级数值，越大越优先

        Example:
            >>> source.get_priority()
            10
        """
        pass

    def __repr__(self) -> str:
        """返回可读的字符串表示"""
        available_count = len(self.list_available()) if hasattr(self, 'list_available') else '?'
        return (
            f"{self.__class__.__name__}("
            f"priority={self.get_priority()}, "
            f"available={available_count})"
        )


class SimpleProviderSource(ProviderSource):
    """简单的 ProviderSource 实现（用于测试和示例）

    基于字典的简单实现，适合：
    - 单元测试中的 Mock
    - 简单的配置提供
    - 示例代码

    Example:
        >>> source = SimpleProviderSource(priority=20)
        >>> source.register('config', {'debug': True})
        >>> source.register('version', '1.0.0')
        >>> source.can_provide('config')
        True
        >>> source.provide('config')
        {'debug': True}
    """

    __slots__ = ('_providers', '_priority')

    def __init__(self, priority: int = 5):
        """初始化简单提供源

        Args:
            priority: 优先级（默认 5）
        """
        self._providers: dict[str, Any] = {}
        self._priority = priority

    def register(self, name: str, instance: Any) -> None:
        """注册一个依赖实例

        Args:
            name: 依赖名称
            instance: 依赖实例
        """
        self._providers[name] = instance

    def can_provide(self, name: str) -> bool:
        """检查是否能提供依赖 (O(1))"""
        return name in self._providers

    def provide(self, name: str) -> Optional[Any]:
        """提供依赖实例 (O(1))"""
        return self._providers.get(name)

    def list_available(self) -> List[str]:
        """列出所有可用依赖"""
        return list(self._providers.keys())

    def get_priority(self) -> int:
        """返回优先级"""
        return self._priority


__all__ = [
    'ProviderSource',
    'SimpleProviderSource',
]

