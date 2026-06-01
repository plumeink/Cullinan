# -*- coding: utf-8 -*-
"""Core module for Cullinan framework.

This module provides foundational components for the Cullinan framework:
- ApplicationContext: Single entry point for IoC/DI (0.93)
- Decorators: @service, @controller, @component
- Dependency Injection: Inject, InjectByName, Lazy
- Unified lifecycle management (all components share same lifecycle)
- Core exceptions and types

Version: 0.90
"""

from .registry import Registry, SimpleRegistry
from .container_manager import ContainerManager, get_container_manager
# Import unified lifecycle from lifecycle_enhanced (the single source of truth)
from .lifecycle_enhanced import (
    LifecycleAware,
    SmartLifecycle,
    LifecyclePhase,
    LifecycleManager,
    get_lifecycle_manager,
    reset_lifecycle_manager,
)
# Keep LifecycleState for backward compatibility
from .types import LifecycleState
from .context import (
    RequestContext,
    get_current_context,
    set_current_context,
    create_context,
    destroy_context,
    ContextManager,
    get_context_value,
    set_context_value
)
from .exceptions import (
    CullinanCoreError,
    RegistryError,
    RegistryFrozenError,
    DependencyResolutionError,
    DependencyNotFoundError,
    DependencyTypeResolutionError,
    CircularDependencyError,
    ScopeNotActiveError,
    ConditionNotMetError,
    CreationError,
    LifecycleError
)

# ============================================================================
# IoC/DI 2.0 System
# ============================================================================

# ApplicationContext - Single Entry Point
from .application_context import ApplicationContext, ContainerState

# Definitions and Scope
from .definitions import Definition, ScopeType
from .scope_manager import ScopeManager
from .factory import Factory

# Diagnostics
from .diagnostics import (
    render_resolution_path,
    render_injection_point,
    render_candidate_sources,
    format_circular_dependency_error,
    format_missing_dependency_error,
)
from .injection_types import Provider
from .semantic_rules import (
    CompatibilitySemanticWarning,
    ComponentDiscoveryWarning,
    CullinanSemanticWarning,
    InjectionSemanticWarning,
    PublicAPISemanticWarning,
    warn_semantic_once,
)

# Decorators - Primary Registration API
from .decorators import (
    service,
    controller,
    component,
    provider as provider_decorator,
    Inject,
    InjectByName,
    Lazy,
    get_injection_markers,
)

# Conditional Decorators
from .conditions import (
    ConditionalOnProperty,
    ConditionalOnClass,
    ConditionalOnMissingBean,
    ConditionalOnBean,
    Conditional,
)

# Pending Registry (for two-phase registration)
from .pending import PendingRegistry, PendingRegistration, ComponentType

# ============================================================================
# Compatibility Aliases (for backward compatibility)
# ============================================================================

# injectable is now a no-op, classes are automatically injectable
def injectable(cls):
    """Compatibility decorator - no longer needed in 0.93.

    In 0.93, all classes decorated with @service, @controller, or @component
    are automatically injectable. This function is kept for backward compatibility.
    """
    warn_semantic_once(
        key="compatibility:injectable",
        rule_key="compatibility-api",
        problem="@injectable 只是兼容入口，不再承担新的注册或注入语义。",
        guidance="改用 @service、@component 或 @controller 作为主入口。",
        category=CompatibilitySemanticWarning,
        stacklevel=2,
    )
    return cls

def inject_constructor(cls):
    """Compatibility decorator - no longer needed in 0.93."""
    warn_semantic_once(
        key="compatibility:inject_constructor",
        rule_key="compatibility-api",
        problem="@inject_constructor 只是兼容入口，不再改变构造器注入行为。",
        guidance="依赖注入由 ApplicationContext.refresh() 统一处理，不需要额外装饰器。",
        category=CompatibilitySemanticWarning,
        stacklevel=2,
    )
    return cls

# ============================================================================
# Global ApplicationContext Access
# ============================================================================

def get_application_context():
    """获取当前活动根容器。"""
    return get_container_manager().get_active_root()


def set_application_context(ctx) -> None:
    """设置或清除当前全局根容器引用。"""
    manager = get_container_manager()
    if ctx is None:
        manager.clear()
        return
    manager.bind(ctx)


# Provide dummy registry functions for compatibility
_dummy_registry = None

def get_injection_registry():
    """Compatibility function - returns None in 0.93.

    Use ApplicationContext instead.
    """
    warn_semantic_once(
        key="compatibility:get_injection_registry",
        rule_key="compatibility-api",
        problem="get_injection_registry() 仅保留兼容外形，当前不会返回可用注册中心。",
        guidance="改用 ApplicationContext / get_application_context()。",
        category=CompatibilitySemanticWarning,
        stacklevel=2,
    )
    return _dummy_registry

def reset_injection_registry():
    """Compatibility function - no-op in 0.93."""
    warn_semantic_once(
        key="compatibility:reset_injection_registry",
        rule_key="compatibility-api",
        problem="reset_injection_registry() 在 0.93 中不再重置真实容器。",
        guidance="如需重建容器，请显式创建新的 ApplicationContext。",
        category=CompatibilitySemanticWarning,
        stacklevel=2,
    )

# InjectionRegistry compatibility class
class InjectionRegistry:
    """Compatibility class - use ApplicationContext instead."""
    pass

__version__ = "0.93a6.post1"

__all__ = [
    # ========================================================================
    # IoC/DI 2.0 System
    # ========================================================================

    # Application Context (Single Entry Point)
    'ApplicationContext',
    'ContainerState',
    'ContainerManager',
    'get_container_manager',
    'get_application_context',
    'set_application_context',
    'Definition',
    'ScopeType',
    'ScopeManager',
    'Factory',

    # Diagnostics
    'render_resolution_path',
    'render_injection_point',
    'render_candidate_sources',
    'format_circular_dependency_error',
    'format_missing_dependency_error',

    # Exceptions
    'CullinanCoreError',
    'RegistryError',
    'RegistryFrozenError',
    'DependencyResolutionError',
    'DependencyNotFoundError',
    'DependencyTypeResolutionError',
    'CircularDependencyError',
    'ScopeNotActiveError',
    'ConditionNotMetError',
    'CreationError',
    'LifecycleError',

    # Decorators (Primary API)
    'service',
    'controller',
    'component',
    'provider_decorator',
    'Provider',
    'Inject',
    'InjectByName',
    'Lazy',
    'get_injection_markers',
    'CullinanSemanticWarning',
    'ComponentDiscoveryWarning',
    'CompatibilitySemanticWarning',
    'InjectionSemanticWarning',
    'PublicAPISemanticWarning',

    # Conditional Decorators
    'ConditionalOnProperty',
    'ConditionalOnClass',
    'ConditionalOnMissingBean',
    'ConditionalOnBean',
    'Conditional',

    # Pending Registry
    'PendingRegistry',
    'PendingRegistration',
    'ComponentType',

    # ========================================================================
    # Core Infrastructure
    # ========================================================================

    # Registry
    'Registry',
    'SimpleRegistry',

    # Lifecycle Management (Unified)
    'LifecycleManager',
    'LifecycleState',
    'LifecycleAware',
    'SmartLifecycle',
    'LifecyclePhase',
    'get_lifecycle_manager',
    'reset_lifecycle_manager',

    # Request Context
    'RequestContext',
    'get_current_context',
    'set_current_context',
    'create_context',
    'destroy_context',
    'ContextManager',
    'get_context_value',
    'set_context_value',

    # ========================================================================
    # Compatibility (kept for backward compatibility)
    # ========================================================================
    'injectable',
    'inject_constructor',
    'InjectionRegistry',
    'get_injection_registry',
    'reset_injection_registry',
]
