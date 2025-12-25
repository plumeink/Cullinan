# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - ScopeManager 作用域管理器

作者：Plumeink

本模块实现 2.0 架构的作用域管理：
- SingletonScope: 应用级单例缓存（线程安全）
- PrototypeScope: 每次创建新实例
- RequestScope: 基于 RequestContext 的请求级缓存
- ScopeManager: 统一的作用域入口
"""

import threading
from typing import Any, Callable, Dict, Optional
from contextvars import ContextVar

from .definitions import ScopeType
from .exceptions import ScopeNotActiveError


# 请求上下文存储（使用 ContextVar 支持异步）
_request_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    '_request_context', default=None
)


class SingletonScope:
    """单例作用域 - 应用级缓存（线程安全）

    在整个应用生命周期内，每个 name 只创建一个实例。
    """

    __slots__ = ('_instances', '_lock')

    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def get(self, name: str, factory: Callable[[], Any]) -> Any:
        """获取或创建单例实例

        Args:
            name: 实例标识
            factory: 工厂函数（无参数）

        Returns:
            单例实例
        """
        # 快速路径：已存在时无需加锁
        if name in self._instances:
            return self._instances[name]

        with self._lock:
            # 双重检查
            if name not in self._instances:
                self._instances[name] = factory()
            return self._instances[name]

    def has(self, name: str) -> bool:
        """检查是否存在实例"""
        return name in self._instances

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._instances.clear()


class PrototypeScope:
    """原型作用域 - 每次创建新实例

    每次调用 get() 都会创建新的实例，不进行任何缓存。
    """

    __slots__ = ()

    def get(self, name: str, factory: Callable[[], Any]) -> Any:
        """每次都创建新实例

        Args:
            name: 实例标识（在原型作用域中仅用于诊断）
            factory: 工厂函数

        Returns:
            新创建的实例
        """
        return factory()

    def has(self, name: str) -> bool:
        """原型作用域永远返回 False（无缓存）"""
        return False

    def clear(self) -> None:
        """原型作用域无需清理"""
        pass


class RequestScope:
    """请求作用域 - 基于 RequestContext 的请求级缓存

    在同一个请求上下文中，每个 name 只创建一个实例。
    不同请求之间的实例是完全隔离的。
    """

    __slots__ = ()

    def get(self, name: str, factory: Callable[[], Any]) -> Any:
        """获取或创建请求范围的实例

        Args:
            name: 实例标识
            factory: 工厂函数

        Returns:
            请求范围内的实例

        Raises:
            ScopeNotActiveError: 如果没有活动的请求上下文
        """
        ctx = _request_context.get()
        if ctx is None:
            raise ScopeNotActiveError(
                scope_type="REQUEST",
                dependency_name=name,
                message=f"无法解析 request-scoped 依赖 '{name}'：当前没有活动的请求上下文。"
                        f"请确保在请求处理流程中使用 RequestScope.enter_context()。"
            )

        if name not in ctx:
            ctx[name] = factory()
        return ctx[name]

    def has(self, name: str) -> bool:
        """检查当前请求上下文中是否存在实例"""
        ctx = _request_context.get()
        if ctx is None:
            return False
        return name in ctx

    def clear(self) -> None:
        """清空当前请求上下文（通常由 exit_context 自动处理）"""
        ctx = _request_context.get()
        if ctx is not None:
            ctx.clear()

    @staticmethod
    def enter_context() -> Dict[str, Any]:
        """进入请求上下文

        Returns:
            新创建的请求上下文字典
        """
        ctx: Dict[str, Any] = {}
        _request_context.set(ctx)
        return ctx

    @staticmethod
    def exit_context() -> None:
        """退出请求上下文"""
        _request_context.set(None)

    @staticmethod
    def is_active() -> bool:
        """检查是否有活动的请求上下文"""
        return _request_context.get() is not None


class ScopeManager:
    """统一的作用域管理器

    作为 2.0 架构中作用域的统一入口，负责：
    - 管理不同类型的 Scope 实例
    - 根据 ScopeType 路由到对应的 Scope
    - 提供请求上下文的 enter/exit 接口
    """

    __slots__ = ('_singleton', '_prototype', '_request')

    def __init__(self):
        self._singleton = SingletonScope()
        self._prototype = PrototypeScope()
        self._request = RequestScope()

    def get(self, scope_type: ScopeType, name: str, factory: Callable[[], Any]) -> Any:
        """根据作用域类型获取或创建实例

        Args:
            scope_type: 作用域类型
            name: 实例标识
            factory: 工厂函数

        Returns:
            实例对象

        Raises:
            ScopeNotActiveError: 如果请求作用域不活跃
            ValueError: 如果 scope_type 无效
        """
        if scope_type == ScopeType.SINGLETON:
            return self._singleton.get(name, factory)
        elif scope_type == ScopeType.PROTOTYPE:
            return self._prototype.get(name, factory)
        elif scope_type == ScopeType.REQUEST:
            return self._request.get(name, factory)
        else:
            raise ValueError(f"未知的作用域类型: {scope_type}")

    def has(self, scope_type: ScopeType, name: str) -> bool:
        """检查指定作用域中是否存在实例"""
        if scope_type == ScopeType.SINGLETON:
            return self._singleton.has(name)
        elif scope_type == ScopeType.PROTOTYPE:
            return self._prototype.has(name)
        elif scope_type == ScopeType.REQUEST:
            return self._request.has(name)
        return False

    def clear_all(self) -> None:
        """清空所有作用域的缓存"""
        self._singleton.clear()
        self._prototype.clear()
        self._request.clear()

    def enter_request_context(self) -> Dict[str, Any]:
        """进入请求上下文"""
        return self._request.enter_context()

    def exit_request_context(self) -> None:
        """退出请求上下文"""
        self._request.exit_context()

    def is_request_active(self) -> bool:
        """检查请求上下文是否活跃"""
        return self._request.is_active()


__all__ = [
    'ScopeType',
    'SingletonScope',
    'PrototypeScope',
    'RequestScope',
    'ScopeManager',
]

