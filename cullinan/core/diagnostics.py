# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - 诊断渲染器

作者：Plumeink

本模块负责将结构化异常渲染为稳定、可复现、可对比的诊断信息。

输出格式规范（按 2.6.6 Contract）：
1. 稳定依赖链路：A -> B -> C -> A
2. 注入点定位：OwnerClass.attr 或 OwnerClass.__init__(param)
3. 候选来源与过滤原因：source + reason
4. 原始异常链：保留 cause
"""

from typing import List, Dict, Any, Optional


def render_resolution_path(path: List[str]) -> str:
    """渲染解析链路为稳定格式

    Args:
        path: 解析路径列表（有序）

    Returns:
        格式化的链路字符串，例如 "A -> B -> C -> A"
    """
    if not path:
        return "(empty)"
    return " -> ".join(path)


def render_injection_point(owner: str, location: str, is_constructor: bool = False) -> str:
    """渲染注入点定位

    Args:
        owner: 拥有者类名
        location: 属性名或参数名
        is_constructor: 是否是构造参数注入

    Returns:
        格式化的注入点，例如 "UserController.user_service" 或 "UserService.__init__(repo)"
    """
    if is_constructor:
        return f"{owner}.__init__({location})"
    return f"{owner}.{location}"


def render_candidate_sources(candidates: List[Dict[str, Any]]) -> str:
    """渲染候选来源与过滤原因

    Args:
        candidates: 候选列表，每项包含 source 和 reason

    Returns:
        格式化的候选来源信息
    """
    if not candidates:
        return "  (无候选来源)"

    lines = []
    for i, candidate in enumerate(candidates, 1):
        source = candidate.get('source', 'unknown')
        reason = candidate.get('reason', 'unknown')
        lines.append(f"  [{i}] {source} - {reason}")

    return "\n".join(lines)


def render_dependency_error(
    error_type: str,
    message: str,
    dependency_name: Optional[str] = None,
    injection_point: Optional[str] = None,
    resolution_path: Optional[List[str]] = None,
    candidate_sources: Optional[List[Dict[str, Any]]] = None,
    cause: Optional[Exception] = None
) -> str:
    """渲染完整的依赖解析错误信息

    Args:
        error_type: 错误类型名称
        message: 错误消息
        dependency_name: 依赖名称
        injection_point: 注入点
        resolution_path: 解析链路
        candidate_sources: 候选来源
        cause: 原始异常

    Returns:
        完整的格式化错误信息
    """
    lines = [
        f"[{error_type}] {message}",
        ""
    ]

    if dependency_name:
        lines.append(f"依赖名称: {dependency_name}")

    if injection_point:
        lines.append(f"注入点: {injection_point}")

    if resolution_path:
        lines.append(f"解析链路: {render_resolution_path(resolution_path)}")

    if candidate_sources:
        lines.append("候选来源:")
        lines.append(render_candidate_sources(candidate_sources))

    if cause:
        lines.append("")
        lines.append(f"原始异常: {type(cause).__name__}: {cause}")

    return "\n".join(lines)


def format_circular_dependency_error(chain: List[str]) -> str:
    """格式化循环依赖错误信息

    Args:
        chain: 循环依赖链路（有序，最后一个元素应与第一个相同表示闭环）

    Returns:
        格式化的循环依赖错误信息
    """
    path_str = render_resolution_path(chain)
    return f"检测到循环依赖: {path_str}"


def format_missing_dependency_error(
    dependency_name: str,
    injection_point: Optional[str] = None,
    resolution_path: Optional[List[str]] = None,
    available_sources: Optional[List[str]] = None
) -> str:
    """格式化缺失依赖错误信息

    Args:
        dependency_name: 缺失的依赖名称
        injection_point: 注入点
        resolution_path: 解析链路
        available_sources: 可用的来源列表

    Returns:
        格式化的缺失依赖错误信息
    """
    lines = [f"依赖 '{dependency_name}' 未找到"]

    if injection_point:
        lines.append(f"注入点: {injection_point}")

    if resolution_path:
        # 链路结尾添加缺失项
        full_path = resolution_path + [f"{dependency_name} (missing)"]
        lines.append(f"解析链路: {render_resolution_path(full_path)}")

    if available_sources:
        lines.append("可用来源:")
        for source in available_sources:
            lines.append(f"  - {source}")

    return "\n".join(lines)


__all__ = [
    'render_resolution_path',
    'render_injection_point',
    'render_candidate_sources',
    'render_dependency_error',
    'format_circular_dependency_error',
    'format_missing_dependency_error',
]

