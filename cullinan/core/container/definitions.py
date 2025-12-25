# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - Definition 数据模型与 Scope 枚举

作者：Plumeink

本模块定义 2.0 架构的核心数据结构：
- ScopeType：作用域枚举（SINGLETON/PROTOTYPE/REQUEST）
- Definition：依赖定义（refresh 后不可变）
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Any, Optional, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .context import ApplicationContext


class ScopeType(Enum):
    """作用域类型枚举

    - SINGLETON: 应用级单例缓存（线程安全）
    - PROTOTYPE: 每次解析创建新实例
    - REQUEST: 基于 RequestContext 的请求级缓存
    """
    SINGLETON = auto()
    PROTOTYPE = auto()
    REQUEST = auto()


@dataclass(frozen=True)
class Definition:
    """依赖定义（2.0 核心数据结构）

    refresh 后必须不可变（使用 frozen=True 强制）。

    Attributes:
        name: 全局唯一标识，用于明确解析与诊断输出
        factory: 统一的实例创建入口，接收 ApplicationContext 返回实例
        scope: 作用域类型（必填）
        source: 来源描述，用于候选来源展示（例如 "service:UserService"）
        type_: 可选，用于类型推断、诊断输出与注入点匹配
        eager: 是否在 refresh/start 阶段预创建（默认 False）
        conditions: 条件列表，不满足时不参与候选
        dependencies: 显式声明的硬依赖（用于启动排序与诊断）
        optional: 是否允许缺失时返回 None（仅影响 try_get）
        tags: 可选标签，用于诊断与扩展
    """
    name: str
    factory: Callable[['ApplicationContext'], Any]
    scope: ScopeType
    source: str
    type_: Optional[type] = None
    eager: bool = False
    conditions: List[Callable[['ApplicationContext'], bool]] = field(default_factory=list)
    dependencies: Optional[List[str]] = None
    optional: bool = False
    tags: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """验证必填字段"""
        if not self.name:
            raise ValueError("Definition.name 不能为空")
        if not callable(self.factory):
            raise ValueError("Definition.factory 必须是可调用对象")
        if not isinstance(self.scope, ScopeType):
            raise ValueError("Definition.scope 必须是 ScopeType 枚举")
        if not self.source:
            raise ValueError("Definition.source 不能为空")

    def check_conditions(self, ctx: 'ApplicationContext') -> bool:
        """检查所有条件是否满足

        Args:
            ctx: ApplicationContext 实例

        Returns:
            True 如果所有条件满足，否则 False
        """
        for condition in self.conditions:
            if not condition(ctx):
                return False
        return True


__all__ = ['ScopeType', 'Definition']

