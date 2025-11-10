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
    
    # Exceptions
    'CullinanCoreError',
    'RegistryError',
    'DependencyResolutionError',
    'CircularDependencyError',
    'LifecycleError',
]
