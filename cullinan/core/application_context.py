# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - ApplicationContext 唯一容器入口

作者：Plumeink

本模块实现 2.0 架构的核心：ApplicationContext。

职责（按 2.6.3 Contract）：
- register(definition): refresh 前允许，refresh 后抛 RegistryFrozenError
- refresh(): 构建管线，末尾 freeze
- get(name): 严格语义，失败必抛结构化异常
- try_get(name): 缺失/条件不满足返回 None，系统错误仍抛异常
- shutdown(): 统一调度 on_shutdown
"""

import threading
import logging
from typing import Dict, Optional, List, Any, Set

from .definitions import Definition
from .scope_manager import ScopeManager
from .exceptions import (
    RegistryFrozenError,
    DependencyNotFoundError,
    CircularDependencyError,
    CreationError,
    ConditionNotMetError,
)
from .diagnostics import (
    format_circular_dependency_error,
    format_missing_dependency_error,
)

logger = logging.getLogger(__name__)


class ApplicationContext:
    """2.0 唯一容器入口

    所有注册、刷新、冻结、解析都必须通过此对象进行。

    Usage:
        ctx = ApplicationContext()
        ctx.register(Definition(name='UserService', ...))
        ctx.refresh()

        user_service = ctx.get('UserService')

        ctx.shutdown()
    """

    __slots__ = (
        '_definitions',
        '_frozen',
        '_refreshed',
        '_scope_manager',
        '_lock',
        '_resolving_stack',
        '_shutdown_handlers',
    )

    def __init__(self):
        """初始化 ApplicationContext"""
        self._definitions: Dict[str, Definition] = {}
        self._frozen: bool = False
        self._refreshed: bool = False
        self._scope_manager: ScopeManager = ScopeManager()
        self._lock = threading.RLock()
        # 用于循环依赖检测的线程本地栈（使用 list 保证有序）
        self._resolving_stack: List[str] = []
        # shutdown 回调
        self._shutdown_handlers: List[Any] = []

    # ========================================================================
    # 注册 API
    # ========================================================================

    def register(self, definition: Definition) -> None:
        """注册 Definition

        Args:
            definition: 要注册的定义

        Raises:
            RegistryFrozenError: 如果 registry 已冻结
            ValueError: 如果 name 重复
        """
        with self._lock:
            if self._frozen:
                raise RegistryFrozenError(
                    f"无法注册 '{definition.name}'：Registry 已冻结（refresh 后禁止修改）"
                )

            if definition.name in self._definitions:
                raise ValueError(f"Definition '{definition.name}' 已存在，禁止重复注册")

            self._definitions[definition.name] = definition
            logger.debug(f"注册 Definition: {definition.name} (scope={definition.scope.name}, source={definition.source})")

    def register_all(self, definitions: List[Definition]) -> None:
        """批量注册 Definitions

        Args:
            definitions: 要注册的定义列表
        """
        for definition in definitions:
            self.register(definition)

    # ========================================================================
    # 生命周期 API
    # ========================================================================

    def refresh(self) -> None:
        """刷新容器：构建管线、初始化 eager 实例、冻结 registry

        调用后：
        - registry 被冻结，禁止任何结构性写入
        - eager=True 的 definition 会被预创建
        """
        with self._lock:
            if self._refreshed:
                logger.warning("ApplicationContext.refresh() 已被调用过，跳过")
                return

            logger.info("ApplicationContext.refresh() 开始")

            # 1. 验证 dependencies 是否存在环（eager 初始化排序）
            self._validate_dependencies()

            # 2. 预创建 eager 实例
            self._initialize_eager_definitions()

            # 3. 冻结 registry
            self._frozen = True
            self._refreshed = True

            logger.info(f"ApplicationContext.refresh() 完成，共注册 {len(self._definitions)} 个 Definition")

    def shutdown(self) -> None:
        """关闭容器：调用所有 shutdown 回调，清理资源"""
        logger.info("ApplicationContext.shutdown() 开始")

        for handler in self._shutdown_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Shutdown handler 执行失败: {e}")

        # 清理 scope 缓存
        self._scope_manager.clear_all()

        logger.info("ApplicationContext.shutdown() 完成")

    def add_shutdown_handler(self, handler) -> None:
        """添加 shutdown 回调"""
        self._shutdown_handlers.append(handler)

    # ========================================================================
    # 解析 API
    # ========================================================================

    def get(self, name: str) -> Any:
        """解析依赖（严格语义）

        Args:
            name: 依赖名称

        Returns:
            解析得到的实例

        Raises:
            DependencyNotFoundError: 依赖不存在
            ConditionNotMetError: 条件不满足
            CircularDependencyError: 循环依赖
            CreationError: 创建失败
        """
        definition = self._definitions.get(name)
        if definition is None:
            raise DependencyNotFoundError(
                message=format_missing_dependency_error(
                    dependency_name=name,
                    available_sources=list(self._definitions.keys())
                ),
                dependency_name=name,
                candidate_sources=[
                    {'source': n, 'reason': 'name_mismatch'}
                    for n in self._definitions.keys()
                ]
            )

        return self._resolve(definition)

    def try_get(self, name: str) -> Optional[Any]:
        """尝试解析依赖（可选语义）

        Args:
            name: 依赖名称

        Returns:
            解析得到的实例，或 None（如果不存在或条件不满足）

        Raises:
            CircularDependencyError: 循环依赖（系统错误，仍抛出）
            CreationError: 创建失败（系统错误，仍抛出）
        """
        definition = self._definitions.get(name)
        if definition is None:
            return None

        # 检查条件
        if not definition.check_conditions(self):
            logger.debug(f"try_get('{name}'): 条件不满足，返回 None")
            return None

        # 系统错误仍然抛出
        return self._resolve(definition)

    def has(self, name: str) -> bool:
        """检查是否存在指定的 Definition"""
        return name in self._definitions

    def get_definition(self, name: str) -> Optional[Definition]:
        """获取 Definition（不解析实例）"""
        return self._definitions.get(name)

    def list_definitions(self) -> List[str]:
        """列出所有已注册的 Definition 名称"""
        return list(self._definitions.keys())

    # ========================================================================
    # Request Context 代理
    # ========================================================================

    def enter_request_context(self) -> Dict[str, Any]:
        """进入请求上下文"""
        return self._scope_manager.enter_request_context()

    def exit_request_context(self) -> None:
        """退出请求上下文"""
        self._scope_manager.exit_request_context()

    def is_request_active(self) -> bool:
        """检查请求上下文是否活跃"""
        return self._scope_manager.is_request_active()

    # ========================================================================
    # 状态查询
    # ========================================================================

    @property
    def is_frozen(self) -> bool:
        """Registry 是否已冻结"""
        return self._frozen

    @property
    def is_refreshed(self) -> bool:
        """是否已 refresh"""
        return self._refreshed

    @property
    def definition_count(self) -> int:
        """已注册的 Definition 数量"""
        return len(self._definitions)

    # ========================================================================
    # 内部方法
    # ========================================================================

    def _resolve(self, definition: Definition) -> Any:
        """内部解析方法

        Args:
            definition: 要解析的定义

        Returns:
            实例对象
        """
        name = definition.name

        # 1. 循环依赖检测（有序链）
        if name in self._resolving_stack:
            # 构建循环链路
            cycle_start = self._resolving_stack.index(name)
            chain = self._resolving_stack[cycle_start:] + [name]
            raise CircularDependencyError(
                message=format_circular_dependency_error(chain),
                dependency_chain=chain,
                dependency_name=name
            )

        # 2. 条件检查
        if not definition.check_conditions(self):
            failed = [f"condition_{i}" for i in range(len(definition.conditions))]
            raise ConditionNotMetError(
                message=f"依赖 '{name}' 的条件不满足",
                dependency_name=name,
                failed_conditions=failed
            )

        # 3. 通过 ScopeManager 获取/创建实例
        self._resolving_stack.append(name)
        try:
            instance = self._scope_manager.get(
                scope_type=definition.scope,
                name=name,
                factory=lambda: self._create_instance(definition)
            )
            return instance
        finally:
            self._resolving_stack.pop()

    def _create_instance(self, definition: Definition) -> Any:
        """调用 factory 创建实例

        Args:
            definition: 定义

        Returns:
            创建的实例

        Raises:
            CreationError: 创建失败
            CircularDependencyError: 循环依赖（直接传播，不包装）
        """
        try:
            instance = definition.factory(self)
            if instance is None:
                raise CreationError(
                    message=f"依赖 '{definition.name}' 的 factory 返回了 None",
                    dependency_name=definition.name
                )
            logger.debug(f"创建实例: {definition.name} (scope={definition.scope.name})")
            return instance
        except (CreationError, CircularDependencyError, ConditionNotMetError):
            # 这些异常直接传播，不包装
            raise
        except Exception as e:
            raise CreationError(
                message=f"创建依赖 '{definition.name}' 失败: {e}",
                dependency_name=definition.name,
                cause=e
            )

    def _validate_dependencies(self) -> None:
        """验证 dependencies 是否存在环"""
        # 简单拓扑排序检测
        visited: Set[str] = set()
        path: List[str] = []

        def visit(name: str) -> None:
            if name in path:
                cycle_start = path.index(name)
                chain = path[cycle_start:] + [name]
                raise CircularDependencyError(
                    message=format_circular_dependency_error(chain),
                    dependency_chain=chain,
                    dependency_name=name
                )

            if name in visited:
                return

            definition = self._definitions.get(name)
            if definition is None:
                return

            path.append(name)
            if definition.dependencies:
                for dep in definition.dependencies:
                    visit(dep)
            path.pop()
            visited.add(name)

        for name in self._definitions:
            visit(name)

    def _initialize_eager_definitions(self) -> None:
        """初始化 eager=True 的 Definition"""
        eager_definitions = [
            d for d in self._definitions.values() if d.eager
        ]

        if not eager_definitions:
            return

        logger.info(f"预创建 {len(eager_definitions)} 个 eager Definition")

        for definition in eager_definitions:
            try:
                self._resolve(definition)
            except Exception as e:
                logger.error(f"预创建 '{definition.name}' 失败: {e}")
                raise


__all__ = ['ApplicationContext']

