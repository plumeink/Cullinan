# -*- coding: utf-8 -*-
"""Core module for Cullinan framework.

This module provides foundational components for the Cullinan framework:
- Base registry pattern
- Dependency injection
- Lifecycle management
- Core exceptions and types

These components serve as building blocks for the service and handler layers.
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
    DependencyResolutionError,
    CircularDependencyError,
    LifecycleError
)

# Legacy dependency injector (for backward compatibility)
from .legacy_injection import DependencyInjector

# Type-based Dependency Injection System
from .injection import (
    Inject,
    InjectByName,
    injectable,
    inject_constructor,
    InjectionRegistry,
    get_injection_registry,
    reset_injection_registry
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

__version__ = "0.80"

__all__ = [
    # Registry
    'Registry',
    'SimpleRegistry',
    
    # Legacy Dependency Injector
    'DependencyInjector',
    # Provider System
    'Provider',
    'InstanceProvider',
    'ClassProvider',
    'FactoryProvider',
    'ScopedProvider',
    'ProviderRegistry',

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
]
