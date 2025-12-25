# -*- coding: utf-8 -*-
"""Legacy dependency injector for backward compatibility.

.. deprecated:: 2.0
    This module is deprecated. Use ApplicationContext and Definition instead.
    See docs/wiki/ioc_di_v2.md and docs/migration_guide_v2.md.

This module provides the old DependencyInjector class for backward compatibility
with ServiceRegistry. New code should use the new injection system in injection.py.
"""

import warnings

# Deprecation warning
warnings.warn(
    "cullinan.core.legacy_injection is deprecated since 2.0. "
    "Migrate to cullinan.core.application_context.ApplicationContext. "
    "See docs/migration_guide_v2.md",
    DeprecationWarning,
    stacklevel=2
)

from typing import Type, Dict, Optional, List, Any, Set
import logging

logger = logging.getLogger(__name__)


class DependencyInjector:
    """Legacy dependency injector - for backward compatibility only.

    This is used by ServiceRegistry to support the old dependencies parameter.
    New code should use the new Inject-based injection system.
    """

    __slots__ = ('_providers', '_dependencies', '_singletons', '_resolving')

    def __init__(self):
        self._providers: Dict[str, Type] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._singletons: Dict[str, Any] = {}
        # Track currently resolving dependencies to detect cycles
        self._resolving: Set[str] = set()

    def register_provider(self, name: str, provider_class: Type,
                         dependencies: Optional[List[str]] = None,
                         singleton: bool = True):
        """Register a provider class

        Args:
            name: Provider name
            provider_class: The class to instantiate
            dependencies: List of dependency names
            singleton: Whether to cache instances
        """
        self._providers[name] = provider_class
        if dependencies:
            self._dependencies[name] = dependencies
        logger.debug(f"Registered provider: {name}")

    def resolve(self, name: str) -> Optional[Any]:
        """Resolve and instantiate a provider

        Args:
            name: Provider name

        Returns:
            Instance of the provider, or None if not found

        Raises:
            RecursionError: If circular dependency detected
        """
        # Check singleton cache
        if name in self._singletons:
            return self._singletons[name]

        # Get provider class
        provider_class = self._providers.get(name)
        if not provider_class:
            logger.warning(f"Provider not found: {name}")
            return None

        # Check for circular dependency
        if name in self._resolving:
            cycle_path = ' -> '.join(list(self._resolving) + [name])
            raise RecursionError(f"Circular dependency detected: {cycle_path}")

        # Mark as resolving
        self._resolving.add(name)

        try:
            # Resolve dependencies
            deps = self._dependencies.get(name, [])
            dep_instances = {}
            for dep_name in deps:
                dep_instance = self.resolve(dep_name)
                if dep_instance:
                    dep_instances[dep_name] = dep_instance

            # Instantiate
            instance = provider_class()

            # Set dependencies
            if hasattr(instance, 'dependencies'):
                instance.dependencies = dep_instances

            # Cache if singleton
            self._singletons[name] = instance

            return instance
        finally:
            # Remove from resolving set
            self._resolving.discard(name)

    def clear(self):
        """Clear all registered providers and cached instances"""
        self._providers.clear()
        self._dependencies.clear()
        self._singletons.clear()
        self._resolving.clear()

    def get_dependency_order(self, names: List[str]) -> List[str]:
        """Get dependency-sorted order of names (topological sort)

        Args:
            names: List of provider names

        Returns:
            Sorted list (dependencies first)
        """
        # Simple topological sort
        visited = set()
        order = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            # Visit dependencies first
            for dep in self._dependencies.get(name, []):
                if dep in names:
                    visit(dep)
            order.append(name)

        for name in names:
            visit(name)

        return order

