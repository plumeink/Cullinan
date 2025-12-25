# -*- coding: utf-8 -*-
"""Core module for Cullinan framework.

This module provides foundational components for the Cullinan framework:
- Base registry pattern
- Dependency injection
- Lifecycle management
- Core exceptions and types

These components serve as building blocks for the service and handler layers.

2.0 New Components:
- ApplicationContext: Single entry point for IoC/DI
- Definition: Immutable dependency definition
- ScopeType: Scope enumeration
- ScopeManager: Unified scope management
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
# 2.0 New IoC/DI System (Recommended)
# ============================================================================
from .application_context import ApplicationContext
from .definitions import Definition, ScopeType
from .scope_manager import ScopeManager
from .factory import Factory
from .diagnostics import (
    render_resolution_path,
    render_injection_point,
    render_candidate_sources,
    format_circular_dependency_error,
    format_missing_dependency_error,
)

# ============================================================================
# Legacy IoC/DI System (Deprecated - will be removed in 3.0)
# ============================================================================

# Type-based Dependency Injection
from .injection import (
    Inject,
    InjectByName,
    injectable,
    inject_constructor,
    InjectionRegistry,
    get_injection_registry,
    reset_injection_registry,
)

# Task-3.4: Injection utilities
from .injection_utils import (
    resolve_dependency_name_from_annotation,
    convert_snake_to_pascal,
)

# Unified Injection Model (Task-3.3)
from .injection_model import (
    InjectionPoint,
    UnifiedInjectionMetadata,
    ResolveStrategy,
    infer_dependency_name
)

# Unified Injection Executor (Task-3.3)
from .injection_executor import (
    InjectionExecutor,
    get_injection_executor,
    set_injection_executor,
    reset_injection_executor,
    has_injection_executor
)

# Provider System
from .provider import (
    Provider,
    InstanceProvider,
    ClassProvider,
    FactoryProvider,
    ScopedProvider,
    ProviderRegistry
)

# Provider Source Interface (Task-1.3)
from .provider_source import (
    ProviderSource,
    SimpleProviderSource
)

# Scope System
from .scope import (
    Scope,
    SingletonScope,
    TransientScope,
    RequestScope,
    get_singleton_scope,
    get_transient_scope,
    get_request_scope
)

# IoC/DI Facade (Unified dependency resolution interface)
from .facade import (
    IoCFacade,
    get_ioc_facade,
    reset_ioc_facade,
    resolve_dependency,
    resolve_dependency_by_name,
    has_dependency,
    DependencyResolutionError as FacadeDependencyResolutionError
)

__version__ = "0.90"

__all__ = [
    # ========================================================================
    # 2.0 New IoC/DI System (Recommended)
    # ========================================================================
    'ApplicationContext',
    'Definition',
    'ScopeType',
    'ScopeManager',
    'Factory',

    # 2.0 Diagnostics
    'render_resolution_path',
    'render_injection_point',
    'render_candidate_sources',
    'format_circular_dependency_error',
    'format_missing_dependency_error',

    # 2.0 Exceptions
    'RegistryFrozenError',
    'DependencyNotFoundError',
    'ScopeNotActiveError',
    'ConditionNotMetError',
    'CreationError',

    # ========================================================================
    # Legacy System (Deprecated - will be removed in 3.0)
    # ========================================================================

    # Registry
    'Registry',
    'SimpleRegistry',

    # Provider System
    'Provider',
    'InstanceProvider',
    'ClassProvider',
    'FactoryProvider',
    'ScopedProvider',
    'ProviderRegistry',

    # Provider Source Interface (Task-1.3)
    'ProviderSource',
    'SimpleProviderSource',

    # Scope System
    'Scope',
    'SingletonScope',
    'TransientScope',
    'RequestScope',
    'get_singleton_scope',
    'get_transient_scope',
    'get_request_scope',

    # Lifecycle Management
    # Type-based Dependency Injection
    'Inject',
    'InjectByName',
    'inject_constructor',
    'injectable',
    'InjectionRegistry',
    'get_injection_registry',
    'reset_injection_registry',

    # Unified Injection Model (Task-3.3)
    'InjectionPoint',
    'UnifiedInjectionMetadata',
    'ResolveStrategy',
    'infer_dependency_name',
    'InjectionExecutor',
    'get_injection_executor',
    'set_injection_executor',
    'reset_injection_executor',
    'has_injection_executor',

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
    
    # Exceptions
    'CullinanCoreError',
    'RegistryError',
    'DependencyResolutionError',
    'CircularDependencyError',
    'LifecycleError',

    # IoC/DI Facade
    'IoCFacade',
    'get_ioc_facade',
    'reset_ioc_facade',
    'resolve_dependency',
    'resolve_dependency_by_name',
    'has_dependency',
]
