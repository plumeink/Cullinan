# -*- coding: utf-8 -*-
"""Scope 作用域系统 - 依赖生命周期管理

提供类似 Spring 的作用域管理，支持：
- SingletonScope（单例作用域）
- TransientScope（瞬时作用域）
- RequestScope（请求作用域）

作用域控制依赖实例的生命周期和共享范围。
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
import threading
import logging

logger = logging.getLogger(__name__)


class Scope(ABC):
    """作用域抽象基类

    定义了作用域的统一接口。作用域负责管理依赖实例的生命周期。
    """

    @abstractmethod
    def get(self, key: str, factory: Callable[[], Any]) -> Any:
        """获取或创建实例

        Args:
            key: 实例的唯一标识
            factory: 创建实例的工厂函数（无参数）

        Returns:
            实例对象
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """清理作用域内的所有实例"""
        pass

    @abstractmethod
    def remove(self, key: str) -> bool:
        """移除指定的实例

        Args:
            key: 实例标识

        Returns:
            True 如果移除成功，False 如果实例不存在
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class SingletonScope(Scope):
    """单例作用域 - 应用级别

    在整个应用生命周期内，每个 key 只创建一个实例。
    线程安全的实例缓存。

    Example:
        scope = SingletonScope()
        instance1 = scope.get('service', lambda: Service())
        instance2 = scope.get('service', lambda: Service())
        assert instance1 is instance2  # 同一个实例
    """

    __slots__ = ('_instances', '_lock')

    def __init__(self):
        """初始化单例作用域"""
        self._instances: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def get(self, key: str, factory: Callable[[], Any]) -> Any:
        """获取或创建单例实例

        如果实例已存在，直接返回；否则调用工厂函数创建并缓存。

        Args:
            key: 实例标识
            factory: 工厂函数

        Returns:
            单例实例
        """
        with self._lock:
            if key not in self._instances:
                logger.debug(f"Creating singleton instance for key: {key}")
                self._instances[key] = factory()
            else:
                logger.debug(f"Returning cached singleton instance for key: {key}")
            return self._instances[key]

    def clear(self) -> None:
        """清空所有缓存的实例"""
        with self._lock:
            count = len(self._instances)
            self._instances.clear()
            logger.debug(f"Cleared {count} singleton instances")

    def remove(self, key: str) -> bool:
        """移除指定的单例实例

        Args:
            key: 实例标识

        Returns:
            True 如果移除成功
        """
        with self._lock:
            if key in self._instances:
                del self._instances[key]
                logger.debug(f"Removed singleton instance: {key}")
                return True
            return False

    def count(self) -> int:
        """返回缓存的实例数量

        Returns:
            实例数量
        """
        return len(self._instances)

    def has(self, key: str) -> bool:
        """检查是否存在指定的实例

        Args:
            key: 实例标识

        Returns:
            True 如果存在
        """
        return key in self._instances

    def __repr__(self) -> str:
        return f"SingletonScope(instances={len(self._instances)})"


class TransientScope(Scope):
    """瞬时作用域 - 每次创建新实例

    每次调用 get() 都会创建新的实例，不进行任何缓存。
    适用于无状态或短生命周期的对象。

    Example:
        scope = TransientScope()
        instance1 = scope.get('temp', lambda: TempData())
        instance2 = scope.get('temp', lambda: TempData())
        assert instance1 is not instance2  # 不同的实例
    """

    __slots__ = ()

    def get(self, key: str, factory: Callable[[], Any]) -> Any:
        """每次都创建新实例

        Args:
            key: 实例标识（在瞬时作用域中不使用）
            factory: 工厂函数

        Returns:
            新创建的实例
        """
        logger.debug(f"Creating transient instance for key: {key}")
        return factory()

    def clear(self) -> None:
        """瞬时作用域无需清理"""
        pass

    def remove(self, key: str) -> bool:
        """瞬时作用域无实例可移除

        Returns:
            始终返回 False
        """
        return False

    def __repr__(self) -> str:
        return "TransientScope()"


class RequestScope(Scope):
    """请求作用域 - 每个请求一个实例

    在同一个请求上下文中，每个 key 只创建一个实例。
    不同请求之间的实例是独立的。
    与 Cullinan 的 RequestContext 集成。

    Example:
        scope = RequestScope()

        # 在请求处理中
        with create_context():
            instance1 = scope.get('handler', lambda: RequestHandler())
            instance2 = scope.get('handler', lambda: RequestHandler())
            assert instance1 is instance2  # 同一请求内相同

        # 新请求
        with create_context():
            instance3 = scope.get('handler', lambda: RequestHandler())
            assert instance1 is not instance3  # 不同请求不同实例
    """

    __slots__ = ('_get_context', '_storage_key')

    def __init__(self, storage_key: str = '_scoped_instances'):
        """初始化请求作用域

        Args:
            storage_key: 在 RequestContext 中存储实例的键名
        """
        self._storage_key = storage_key
        # 延迟导入，避免循环依赖
        from .context import get_current_context
        self._get_context = get_current_context

    def get(self, key: str, factory: Callable[[], Any]) -> Any:
        """获取或创建请求范围的实例

        Args:
            key: 实例标识
            factory: 工厂函数

        Returns:
            请求范围内的实例

        Raises:
            RuntimeError: 如果没有活动的请求上下文
        """
        ctx = self._get_context()
        if ctx is None:
            raise RuntimeError(
                f"No active request context for request-scoped dependency '{key}'. "
                f"Ensure the request is wrapped with create_context() or within a request handler."
            )

        # 获取或创建实例存储
        instances = ctx.get(self._storage_key)
        if instances is None:
            instances = {}
            ctx.set(self._storage_key, instances)

        # 获取或创建实例
        if key not in instances:
            logger.debug(f"Creating request-scoped instance for key: {key}")
            instances[key] = factory()
        else:
            logger.debug(f"Returning cached request-scoped instance for key: {key}")

        return instances[key]

    def clear(self) -> None:
        """清空当前请求上下文中的所有实例"""
        ctx = self._get_context()
        if ctx is not None:
            instances = ctx.get(self._storage_key)
            if instances:
                count = len(instances)
                instances.clear()
                logger.debug(f"Cleared {count} request-scoped instances")

    def remove(self, key: str) -> bool:
        """移除当前请求上下文中的指定实例

        Args:
            key: 实例标识

        Returns:
            True 如果移除成功
        """
        ctx = self._get_context()
        if ctx is not None:
            instances = ctx.get(self._storage_key)
            if instances and key in instances:
                del instances[key]
                logger.debug(f"Removed request-scoped instance: {key}")
                return True
        return False

    def count(self) -> int:
        """返回当前请求上下文中的实例数量

        Returns:
            实例数量，如果没有上下文则返回 0
        """
        ctx = self._get_context()
        if ctx is not None:
            instances = ctx.get(self._storage_key)
            if instances:
                return len(instances)
        return 0

    def has(self, key: str) -> bool:
        """检查当前请求上下文中是否存在指定实例

        Args:
            key: 实例标识

        Returns:
            True 如果存在
        """
        ctx = self._get_context()
        if ctx is not None:
            instances = ctx.get(self._storage_key)
            if instances:
                return key in instances
        return False

    def __repr__(self) -> str:
        return f"RequestScope(storage_key='{self._storage_key}')"


# 预定义的全局作用域实例
_singleton_scope = SingletonScope()
_transient_scope = TransientScope()
_request_scope = RequestScope()


def get_singleton_scope() -> SingletonScope:
    """获取全局单例作用域实例

    Returns:
        SingletonScope 实例
    """
    return _singleton_scope


def get_transient_scope() -> TransientScope:
    """获取全局瞬时作用域实例

    Returns:
        TransientScope 实例
    """
    return _transient_scope


def get_request_scope() -> RequestScope:
    """获取全局请求作用域实例

    Returns:
        RequestScope 实例
    """
    return _request_scope


__all__ = [
    'Scope',
    'SingletonScope',
    'TransientScope',
    'RequestScope',
    'get_singleton_scope',
    'get_transient_scope',
    'get_request_scope',
]

