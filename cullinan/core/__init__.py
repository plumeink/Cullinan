# -*- coding: utf-8 -*-
"""Core module for Cullinan framework.

This module provides foundational components for the Cullinan framework:
- ApplicationContext: Single entry point for IoC/DI (2.0)
- Decorators: @service, @controller, @component
- Dependency Injection: Inject, InjectByName, Lazy
- Lifecycle management
- Core exceptions and types

Version: 0.90
"""

from .registry import Registry, SimpleRegistry
from .lifecycle import LifecycleManager
from .types import LifecycleState, LifecycleAware
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
from .application_context import ApplicationContext

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
    """Compatibility decorator - no longer needed in 2.0.

    In 2.0, all classes decorated with @service, @controller, or @component
    are automatically injectable. This function is kept for backward compatibility.
    """
    return cls

def inject_constructor(cls):
    """Compatibility decorator - no longer needed in 2.0."""
    return cls

# Provide dummy registry functions for compatibility
_dummy_registry = None

def get_injection_registry():
    """Compatibility function - returns None in 2.0.

    Use ApplicationContext instead.
    """
    return _dummy_registry

def reset_injection_registry():
    """Compatibility function - no-op in 2.0."""
    pass

# InjectionRegistry compatibility class
class InjectionRegistry:
    """Compatibility class - use ApplicationContext instead."""
    pass

__version__ = "0.90"

__all__ = [
    # ========================================================================
    # IoC/DI 2.0 System
    # ========================================================================

    # Application Context (Single Entry Point)
    'ApplicationContext',
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
    'Inject',
    'InjectByName',
    'Lazy',
    'get_injection_markers',

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

    # Lifecycle Management
    'LifecycleManager',
    'LifecycleState',
    'LifecycleAware',
    
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
