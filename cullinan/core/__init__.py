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
from .injection import DependencyInjector
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

__version__ = "0.8.0-alpha"

__all__ = [
    # Registry
    'Registry',
    'SimpleRegistry',
    
    # Dependency Injection
    'DependencyInjector',
    
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
