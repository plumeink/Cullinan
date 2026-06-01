# -*- coding: utf-8 -*-
"""Central semantic rule messages and warnings for Cullinan."""

from __future__ import annotations

import warnings
from typing import Dict


class CullinanSemanticWarning(UserWarning):
    """Base warning for semantic-rule deviations."""


class ComponentDiscoveryWarning(CullinanSemanticWarning):
    """Warning for component discovery semantics."""


class CompatibilitySemanticWarning(CullinanSemanticWarning):
    """Warning for compatibility-only APIs."""


class InjectionSemanticWarning(CullinanSemanticWarning):
    """Warning for injection semantics that are valid but discouraged."""


SEMANTIC_RULES: Dict[str, str] = {
    "component-import-execution": "组件注册依赖模块导入阶段执行装饰器，而不是静态扫描源代码。",
    "component-top-level": "自动发现/自动装配只保证模块顶层定义且在导入时执行过装饰器的组件。",
    "inject-unique-binding": "Inject() 只接受可被稳定归一化并唯一绑定到一个组件的类型契约。",
    "inject-by-name": "InjectByName() 是显式名称绑定；类型注解只用于表达语义，不参与名称解析。",
    "refresh-freeze": "ApplicationContext.refresh() 之后 PendingRegistry 与 DefinitionRegistry 都进入冻结状态；新的运行时结构边界应在此之前确定。",
    "lifecycle-request-scope": "singleton 组件不能直接依赖 request 作用域组件。",
    "compatibility-api": "兼容 API 只保证旧代码可继续运行，不代表当前推荐编程模型。",
}

_warned_keys = set()


def describe_semantic_rule(rule_key: str) -> str:
    return SEMANTIC_RULES[rule_key]


def format_semantic_message(rule_key: str, problem: str, guidance: str | None = None) -> str:
    parts = [
        f"语义规则：{describe_semantic_rule(rule_key)}",
        f"当前问题：{problem}",
    ]
    if guidance:
        parts.append(f"建议：{guidance}")
    return " ".join(parts)


def warn_semantic_once(
    *,
    key: str,
    rule_key: str,
    problem: str,
    guidance: str | None = None,
    category: type[Warning] = CullinanSemanticWarning,
    stacklevel: int = 2,
) -> None:
    if key in _warned_keys:
        return
    warnings.warn(
        format_semantic_message(rule_key, problem, guidance),
        category=category,
        stacklevel=stacklevel,
    )
    _warned_keys.add(key)


def reset_semantic_warnings() -> None:
    _warned_keys.clear()


__all__ = [
    "SEMANTIC_RULES",
    "CullinanSemanticWarning",
    "ComponentDiscoveryWarning",
    "CompatibilitySemanticWarning",
    "InjectionSemanticWarning",
    "describe_semantic_rule",
    "format_semantic_message",
    "warn_semantic_once",
    "reset_semantic_warnings",
]
