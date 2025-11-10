# -*- coding: utf-8 -*-
"""Dependency injection engine for Cullinan framework.

Provides lightweight dependency injection capabilities with support
for providers, singletons, and dependency resolution.
"""

from typing import Dict, List, Optional, Any, Callable, Set
import logging

from .exceptions import DependencyResolutionError, CircularDependencyError

logger = logging.getLogger(__name__)


class DependencyInjector:
    """Lightweight dependency injector for Cullinan.
    
    Manages providers and singletons, resolves dependencies in correct order,
    and detects circular dependencies.
    
    Usage:
        injector = DependencyInjector()
        injector.register_provider('service_a', ServiceA)
        injector.register_provider('service_b', ServiceB, dependencies=['service_a'])
        
        instance = injector.resolve('service_b')
    """
    
    def __init__(self):
        """Initialize the dependency injector."""
        self._providers: Dict[str, Callable] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._singletons: Dict[str, Any] = {}
        self._singleton_flags: Dict[str, bool] = {}
    
    def register_provider(self, name: str, provider: Callable, 
                         dependencies: Optional[List[str]] = None,
                         singleton: bool = True) -> None:
        """Register a dependency provider.
        
        Args:
            name: Identifier for the dependency
            provider: Callable that creates the dependency (class or factory)
            dependencies: List of dependency names this provider needs
            singleton: If True, provider is called once and cached
        
        Raises:
            ValueError: If name already registered
        """
        if name in self._providers:
            logger.warning(f"Provider already registered: {name}")
            return
        
        self._providers[name] = provider
        self._dependencies[name] = dependencies or []
        self._singleton_flags[name] = singleton
        
        logger.debug(f"Registered provider: {name} (singleton={singleton})")
    
    def resolve(self, name: str, _resolving: Optional[Set[str]] = None) -> Any:
        """Resolve a dependency and its dependencies recursively.
        
        Args:
            name: Identifier of the dependency to resolve
            _resolving: Internal set to track circular dependencies
        
        Returns:
            The resolved dependency instance
        
        Raises:
            DependencyResolutionError: If dependency not found
            CircularDependencyError: If circular dependency detected
        """
        if name not in self._providers:
            raise DependencyResolutionError(f"Dependency not found: {name}")
        
        # Check for circular dependencies
        if _resolving is None:
            _resolving = set()
        
        if name in _resolving:
            chain = ' -> '.join(list(_resolving) + [name])
            raise CircularDependencyError(
                f"Circular dependency detected: {chain}"
            )
        
        # If singleton and already created, return cached instance
        if self._singleton_flags.get(name, True) and name in self._singletons:
            return self._singletons[name]
        
        # Mark as resolving
        _resolving.add(name)
        
        try:
            # Resolve dependencies first
            resolved_deps = {}
            for dep_name in self._dependencies.get(name, []):
                resolved_deps[dep_name] = self.resolve(dep_name, _resolving)
            
            # Call provider
            provider = self._providers[name]
            
            # If provider is a class, instantiate it
            if isinstance(provider, type):
                instance = provider()
            else:
                # Provider is a factory function
                instance = provider()
            
            # Inject dependencies if instance has 'dependencies' attribute
            if hasattr(instance, 'dependencies'):
                instance.dependencies = resolved_deps
            
            # Cache if singleton
            if self._singleton_flags.get(name, True):
                self._singletons[name] = instance
            
            return instance
        
        finally:
            # Unmark as resolving
            _resolving.discard(name)
    
    def resolve_all(self, names: List[str]) -> Dict[str, Any]:
        """Resolve multiple dependencies.
        
        Args:
            names: List of dependency names to resolve
        
        Returns:
            Dictionary mapping names to resolved instances
        """
        return {name: self.resolve(name) for name in names}
    
    def get_dependency_order(self, names: List[str]) -> List[str]:
        """Get the order in which dependencies should be resolved.
        
        Uses topological sort to determine correct initialization order.
        
        Args:
            names: List of dependency names
        
        Returns:
            Sorted list of names in dependency order
        
        Raises:
            CircularDependencyError: If circular dependency detected
        """
        # Build adjacency list
        graph: Dict[str, List[str]] = {name: [] for name in names}
        in_degree: Dict[str, int] = {name: 0 for name in names}
        
        for name in names:
            if name not in self._dependencies:
                continue
            
            for dep in self._dependencies[name]:
                if dep in names:
                    graph[dep].append(name)
                    in_degree[name] += 1
        
        # Kahn's algorithm for topological sort
        queue = [name for name in names if in_degree[name] == 0]
        result = []
        
        while queue:
            # Sort queue for deterministic ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If not all nodes processed, there's a cycle
        if len(result) != len(names):
            unprocessed = [name for name in names if name not in result]
            raise CircularDependencyError(
                f"Circular dependency detected among: {unprocessed}"
            )
        
        return result
    
    def clear_singletons(self) -> None:
        """Clear all singleton instances.
        
        Useful for testing or application restart.
        """
        self._singletons.clear()
        logger.debug("Cleared all singleton instances")
    
    def clear(self) -> None:
        """Clear all providers and singletons.
        
        Useful for testing or complete reinitialization.
        """
        self._providers.clear()
        self._dependencies.clear()
        self._singletons.clear()
        self._singleton_flags.clear()
        logger.debug("Cleared all providers and singletons")
    
    def has_provider(self, name: str) -> bool:
        """Check if a provider is registered.
        
        Args:
            name: Identifier to check
        
        Returns:
            True if provider exists, False otherwise
        """
        return name in self._providers
    
    def get_dependencies(self, name: str) -> List[str]:
        """Get the dependencies for a given provider.
        
        Args:
            name: Identifier of the provider
        
        Returns:
            List of dependency names
        """
        return self._dependencies.get(name, []).copy()
