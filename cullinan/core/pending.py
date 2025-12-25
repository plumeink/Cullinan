# -*- coding: utf-8 -*-
"""Pending registration system for decorator-based component registration.

This module provides a two-phase registration mechanism:
1. Module loading phase: Decorators collect metadata to PendingRegistry
2. ApplicationContext.refresh() phase: Process all registrations uniformly

Author: Plumeink
"""

from dataclasses import dataclass, field
from typing import Type, Optional, List, Callable, Any
from enum import Enum
import threading


class ComponentType(Enum):
    """Component type enumeration."""
    SERVICE = "service"
    CONTROLLER = "controller"
    COMPONENT = "component"
    PROVIDER = "provider"


@dataclass
class PendingRegistration:
    """Pending registration metadata.

    Stores all information needed to register a component
    when ApplicationContext.refresh() is called.

    Attributes:
        cls: The class to be registered
        name: Component name (unique identifier)
        component_type: Type of component (SERVICE, CONTROLLER, etc.)
        scope: Lifecycle scope (singleton, prototype, request)
        url_prefix: URL prefix for controllers
        routes: Route definitions for controllers
        dependencies: Explicit dependency names
        conditions: Conditional registration functions
        source_file: Source file path (for diagnostics)
        source_line: Source line number (for diagnostics)
    """
    cls: Type
    name: str
    component_type: ComponentType
    scope: str = "singleton"

    # Controller specific
    url_prefix: Optional[str] = None
    routes: List[Any] = field(default_factory=list)

    # Service specific
    dependencies: Optional[List[str]] = None

    # Conditional decorators
    conditions: List[Callable] = field(default_factory=list)

    # Source information (for diagnostics)
    source_file: Optional[str] = None
    source_line: Optional[int] = None

    def get_source_location(self) -> str:
        """Get formatted source location string."""
        if self.source_file and self.source_line:
            return f"{self.source_file}:{self.source_line}"
        elif self.source_file:
            return self.source_file
        return "<unknown>"


class PendingRegistry:
    """Global pending registration collector.

    Singleton pattern - collects all decorator-marked components
    before ApplicationContext.refresh() processes them.

    Thread-safe implementation for concurrent module loading.

    Usage:
        # Decorator adds registration
        PendingRegistry.get_instance().add(registration)

        # ApplicationContext processes all
        for reg in PendingRegistry.get_instance().get_all():
            context.register(reg)

        # Freeze after refresh
        PendingRegistry.get_instance().freeze()
    """

    _instance: Optional['PendingRegistry'] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self):
        self._registrations: List[PendingRegistration] = []
        self._frozen = False
        self._registration_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> 'PendingRegistry':
        """Get singleton instance (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton instance (for testing only).

        WARNING: Only use in test teardown, never in production code.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance._registrations.clear()
                cls._instance._frozen = False
            cls._instance = None

    def add(self, registration: PendingRegistration) -> None:
        """Add a pending registration.

        Args:
            registration: The registration metadata to add

        Raises:
            RuntimeError: If registry is frozen (after refresh)
        """
        with self._registration_lock:
            if self._frozen:
                raise RuntimeError(
                    f"Cannot register '{registration.name}' after ApplicationContext.refresh(). "
                    f"Ensure all decorated classes are imported before calling refresh(). "
                    f"Source: {registration.get_source_location()}"
                )
            self._registrations.append(registration)

    def get_all(self) -> List[PendingRegistration]:
        """Get all pending registrations.

        Returns:
            A copy of the registrations list
        """
        with self._registration_lock:
            return self._registrations.copy()

    def get_by_type(self, component_type: ComponentType) -> List[PendingRegistration]:
        """Get registrations filtered by component type.

        Args:
            component_type: The type to filter by

        Returns:
            List of matching registrations
        """
        with self._registration_lock:
            return [r for r in self._registrations if r.component_type == component_type]

    def get_by_name(self, name: str) -> Optional[PendingRegistration]:
        """Get registration by name.

        Args:
            name: Component name to find

        Returns:
            The registration if found, None otherwise
        """
        with self._registration_lock:
            for reg in self._registrations:
                if reg.name == name:
                    return reg
            return None

    def contains(self, name: str) -> bool:
        """Check if a registration with the given name exists.

        Args:
            name: Component name to check

        Returns:
            True if exists, False otherwise
        """
        return self.get_by_name(name) is not None

    def clear(self) -> None:
        """Clear all registrations.

        Called after ApplicationContext processes all registrations.
        """
        with self._registration_lock:
            self._registrations.clear()

    def freeze(self) -> None:
        """Freeze the registry, preventing further additions.

        Called after ApplicationContext.refresh() completes.
        """
        with self._registration_lock:
            self._frozen = True

    def unfreeze(self) -> None:
        """Unfreeze the registry (for testing only).

        WARNING: Only use in test setup, never in production code.
        """
        with self._registration_lock:
            self._frozen = False

    @property
    def is_frozen(self) -> bool:
        """Check if registry is frozen."""
        return self._frozen

    @property
    def count(self) -> int:
        """Get total number of registrations."""
        with self._registration_lock:
            return len(self._registrations)

    def __len__(self) -> int:
        """Support len() builtin."""
        return self.count

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"PendingRegistry(count={self.count}, "
            f"frozen={self._frozen})"
        )

