# -*- coding: utf-8 -*-
"""Cullinan Core Module (0.90)

This module provides foundational components for the Cullinan framework.

Structure:
- container/: IoC/DI container (ApplicationContext, Definition, Scope)
- diagnostics/: Exceptions and diagnostic rendering
- lifecycle/: Lifecycle management
- request/: Request context management
- legacy/: Deprecated components (will be removed in 1.0.0)
- extensions.py: Extension point registry

Author: Plumeink
"""

# ============================================================================
# 2.0 IoC/DI Container (Primary API)
# ============================================================================
from .container import (
    ApplicationContext,
    Definition,
    ScopeType,
    ScopeManager,
    SingletonScope,
    PrototypeScope,
    RequestScope,
    Factory,
)

# ============================================================================
# Diagnostics & Exceptions
# ============================================================================
from .diagnostics import (
    # Exceptions
    CullinanCoreError,
    RegistryError,
    RegistryFrozenError,
    DependencyResolutionError,
    DependencyNotFoundError,
    CircularDependencyError,
    ScopeNotActiveError,
    ConditionNotMetError,
    CreationError,
    LifecycleError,
    
    # Rendering
    render_resolution_path,
    render_injection_point,
    render_candidate_sources,
    format_circular_dependency_error,
    format_missing_dependency_error,
    
    # Types
    LifecycleState,
    LifecycleAware,
)

# ============================================================================
# Lifecycle Management
# ============================================================================
from .lifecycle import (
    LifecycleManager,
    LifecycleEvent,
    LifecycleHookManager,
    get_lifecycle_hooks,
)

# ============================================================================
# Request Context
# ============================================================================
from .request import (
    RequestContext,
    get_current_context,
    set_current_context,
    create_context,
    destroy_context,
    ContextManager,
    get_context_value,
    set_context_value,
)

# ============================================================================
# Extensions
# ============================================================================
from .extensions import (
    ExtensionCategory,
    ExtensionPoint,
    ExtensionRegistry,
    get_extension_registry,
)

__version__ = "0.90"

__all__ = [
    # Container (2.0 Primary API)
    'ApplicationContext',
    'Definition',
    'ScopeType',
    'ScopeManager',
    'SingletonScope',
    'PrototypeScope',
    'RequestScope',
    'Factory',
    
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
    
    # Diagnostics
    'render_resolution_path',
    'render_injection_point',
    'render_candidate_sources',
    'format_circular_dependency_error',
    'format_missing_dependency_error',
    
    # Types
    'LifecycleState',
    'LifecycleAware',
    
    # Lifecycle
    'LifecycleManager',
    'LifecycleEvent',
    'LifecycleHookManager',
    'get_lifecycle_hooks',
    
    # Request Context
    'RequestContext',
    'get_current_context',
    'set_current_context',
    'create_context',
    'destroy_context',
    'ContextManager',
    'get_context_value',
    'set_context_value',
    
    # Extensions
    'ExtensionCategory',
    'ExtensionPoint',
    'ExtensionRegistry',
    'get_extension_registry',
]

