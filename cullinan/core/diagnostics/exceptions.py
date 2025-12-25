# -*- coding: utf-8 -*-
"""Core exceptions for the Cullinan framework.

This module defines the exception hierarchy for the core module,
providing specific error types for registry, dependency injection,
and lifecycle management operations.

2.0 新增：结构化异常体系，支持诊断渲染。
"""


from typing import Optional, List, Dict, Any


class CullinanCoreError(Exception):
    """Base exception for all core module errors."""
    pass


class RegistryError(CullinanCoreError):
    """Exception raised for registry-related errors."""
    pass


class RegistryFrozenError(RegistryError):
    """Exception raised when attempting to modify a frozen registry.

    2.0 新增：refresh 后任何结构性写入必须抛出此异常。
    """

    def __init__(self, message: str = "Registry 已冻结，禁止修改"):
        super().__init__(message)
        self.message = message


class DependencyResolutionError(CullinanCoreError):
    """Exception raised when dependencies cannot be resolved.

    2.0 增强：携带结构化诊断字段。
    """

    def __init__(
        self,
        message: str,
        dependency_name: Optional[str] = None,
        injection_point: Optional[str] = None,
        resolution_path: Optional[List[str]] = None,
        candidate_sources: Optional[List[Dict[str, Any]]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.dependency_name = dependency_name
        self.injection_point = injection_point
        self.resolution_path = resolution_path or []
        self.candidate_sources = candidate_sources or []
        self.cause = cause

        # 保留原始异常链
        if cause is not None:
            self.__cause__ = cause


class DependencyNotFoundError(DependencyResolutionError):
    """Exception raised when a required dependency is not found.

    2.0 新增：明确的"依赖缺失"异常类型。
    """
    pass


class ConditionNotMetError(DependencyResolutionError):
    """Exception raised when dependency conditions are not met.

    2.0 新增：条件不满足时的异常类型。
    """

    def __init__(
        self,
        message: str,
        dependency_name: Optional[str] = None,
        failed_conditions: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(message, dependency_name=dependency_name, **kwargs)
        self.failed_conditions = failed_conditions or []


class CircularDependencyError(DependencyResolutionError):
    """Exception raised when circular dependencies are detected.

    2.0 增强：链路必须稳定有序。
    """

    def __init__(
        self,
        message: str,
        dependency_chain: Optional[List[str]] = None,
        **kwargs
    ):
        # 将 dependency_chain 作为 resolution_path
        super().__init__(
            message,
            resolution_path=dependency_chain,
            **kwargs
        )
        self.dependency_chain = dependency_chain or []


class ScopeNotActiveError(DependencyResolutionError):
    """Exception raised when required scope is not active.

    2.0 新增：request scope 在无 RequestContext 时必须抛出此异常。
    """

    def __init__(
        self,
        scope_type: str,
        dependency_name: Optional[str] = None,
        message: Optional[str] = None,
        **kwargs
    ):
        if message is None:
            message = f"Scope '{scope_type}' 不活跃，无法解析依赖 '{dependency_name}'"
        super().__init__(message, dependency_name=dependency_name, **kwargs)
        self.scope_type = scope_type


class CreationError(DependencyResolutionError):
    """Exception raised when instance creation fails.

    2.0 新增：实例创建失败的异常类型，必须保留原始异常。
    """

    def __init__(
        self,
        message: str,
        dependency_name: Optional[str] = None,
        cause: Optional[Exception] = None,
        **kwargs
    ):
        super().__init__(message, dependency_name=dependency_name, cause=cause, **kwargs)


class LifecycleError(CullinanCoreError):
    """Exception raised for lifecycle management errors."""
    pass
