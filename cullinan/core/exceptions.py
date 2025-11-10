# -*- coding: utf-8 -*-
"""Core exceptions for the Cullinan framework.

This module defines the exception hierarchy for the core module,
providing specific error types for registry, dependency injection,
and lifecycle management operations.
"""


class CullinanCoreError(Exception):
    """Base exception for all core module errors."""
    pass


class RegistryError(CullinanCoreError):
    """Exception raised for registry-related errors."""
    pass


class DependencyResolutionError(CullinanCoreError):
    """Exception raised when dependencies cannot be resolved."""
    pass


class CircularDependencyError(DependencyResolutionError):
    """Exception raised when circular dependencies are detected."""
    pass


class LifecycleError(CullinanCoreError):
    """Exception raised for lifecycle management errors."""
    pass
