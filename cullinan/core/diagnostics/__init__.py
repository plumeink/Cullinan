# -*- coding: utf-8 -*-
"""Cullinan Diagnostics Module

This module provides diagnostic and exception handling:
- Structured exception hierarchy
- Diagnostic rendering for error messages
- Type definitions

Author: Plumeink
"""

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
    LifecycleError,
)

from .renderer import (
    render_resolution_path,
    render_injection_point,
    render_candidate_sources,
    render_dependency_error,
    format_circular_dependency_error,
    format_missing_dependency_error,
)

from .types import LifecycleState, LifecycleAware

__all__ = [
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

    # Rendering
    'render_resolution_path',
    'render_injection_point',
    'render_candidate_sources',
    'render_dependency_error',
    'format_circular_dependency_error',
    'format_missing_dependency_error',

    # Types
    'LifecycleState',
    'LifecycleAware',
]

