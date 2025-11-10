# -*- coding: utf-8 -*-
"""Lifecycle management for Cullinan framework components.

Provides lifecycle management capabilities with proper initialization
and shutdown ordering based on dependencies.
"""

from typing import Dict, List, Optional, Any
import logging
import asyncio
import inspect

from .types import LifecycleState
from .exceptions import LifecycleError

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Manages lifecycle of framework components.
    
    Ensures components are initialized in dependency order and
    destroyed in reverse order. Supports both sync and async
    lifecycle methods.
    
    Usage:
        manager = LifecycleManager()
        manager.register_component('service_a', service_a, dependencies=[])
        manager.register_component('service_b', service_b, dependencies=['service_a'])
        
        manager.initialize_all()  # Initializes in correct order
        # ... use services ...
        manager.destroy_all()  # Destroys in reverse order
    """
    
    def __init__(self):
        """Initialize the lifecycle manager."""
        self._components: Dict[str, Any] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._states: Dict[str, LifecycleState] = {}
        self._initialization_order: List[str] = []
    
    def register_component(self, name: str, component: Any,
                          dependencies: Optional[List[str]] = None) -> None:
        """Register a component for lifecycle management.
        
        Args:
            name: Unique identifier for the component
            component: The component instance
            dependencies: List of dependency names
        
        Raises:
            LifecycleError: If name already registered
        """
        if name in self._components:
            logger.warning(f"Component already registered: {name}")
            return
        
        self._components[name] = component
        self._dependencies[name] = dependencies or []
        self._states[name] = LifecycleState.CREATED
        
        logger.debug(f"Registered component: {name}")
    
    def initialize_all(self) -> None:
        """Initialize all registered components in dependency order.
        
        Raises:
            LifecycleError: If initialization fails or circular dependency
        """
        # Calculate initialization order
        order = self._calculate_order()
        self._initialization_order = order
        
        # Initialize each component
        for name in order:
            self._initialize_component(name)
        
        logger.info(f"Initialized {len(order)} components")
    
    async def initialize_all_async(self) -> None:
        """Initialize all registered components in dependency order (async version).
        
        Raises:
            LifecycleError: If initialization fails or circular dependency
        """
        # Calculate initialization order
        order = self._calculate_order()
        self._initialization_order = order
        
        # Initialize each component
        for name in order:
            await self._initialize_component_async(name)
        
        logger.info(f"Initialized {len(order)} components (async)")
    
    def destroy_all(self) -> None:
        """Destroy all components in reverse initialization order.
        
        Continues even if individual components fail to destroy.
        """
        # Destroy in reverse order
        order = list(reversed(self._initialization_order))
        
        errors = []
        for name in order:
            try:
                self._destroy_component(name)
            except Exception as e:
                logger.error(f"Error destroying {name}: {e}", exc_info=True)
                errors.append((name, e))
        
        if errors:
            logger.warning(f"Failed to destroy {len(errors)} component(s)")
        else:
            logger.info(f"Destroyed {len(order)} components")
    
    async def destroy_all_async(self) -> None:
        """Destroy all components in reverse initialization order (async version).
        
        Continues even if individual components fail to destroy.
        """
        # Destroy in reverse order
        order = list(reversed(self._initialization_order))
        
        errors = []
        for name in order:
            try:
                await self._destroy_component_async(name)
            except Exception as e:
                logger.error(f"Error destroying {name}: {e}", exc_info=True)
                errors.append((name, e))
        
        if errors:
            logger.warning(f"Failed to destroy {len(errors)} component(s)")
        else:
            logger.info(f"Destroyed {len(order)} components (async)")
    
    def get_state(self, name: str) -> Optional[LifecycleState]:
        """Get the lifecycle state of a component.
        
        Args:
            name: Component identifier
        
        Returns:
            Current lifecycle state, or None if not registered
        """
        return self._states.get(name)
    
    def _initialize_component(self, name: str) -> None:
        """Initialize a single component.
        
        Args:
            name: Component identifier
        
        Raises:
            LifecycleError: If initialization fails
        """
        component = self._components[name]
        current_state = self._states[name]
        
        if current_state != LifecycleState.CREATED:
            logger.debug(f"Component {name} already initialized, skipping")
            return
        
        self._states[name] = LifecycleState.INITIALIZING
        
        try:
            # Call on_init if it exists
            if hasattr(component, 'on_init') and callable(component.on_init):
                logger.debug(f"Calling on_init for {name}")
                result = component.on_init()
                # If on_init returns a coroutine, it needs to be awaited
                if inspect.iscoroutine(result):
                    logger.warning(f"Component {name}.on_init() is async but called synchronously. Use initialize_all_async() instead.")
                    # Clean up the coroutine to avoid warnings
                    result.close()
            
            self._states[name] = LifecycleState.INITIALIZED
            logger.debug(f"Initialized component: {name}")
        
        except Exception as e:
            self._states[name] = LifecycleState.CREATED  # Rollback state
            logger.error(f"Failed to initialize {name}: {e}", exc_info=True)
            raise LifecycleError(f"Failed to initialize {name}: {e}") from e
    
    async def _initialize_component_async(self, name: str) -> None:
        """Initialize a single component (async version).
        
        Args:
            name: Component identifier
        
        Raises:
            LifecycleError: If initialization fails
        """
        component = self._components[name]
        current_state = self._states[name]
        
        if current_state != LifecycleState.CREATED:
            logger.debug(f"Component {name} already initialized, skipping")
            return
        
        self._states[name] = LifecycleState.INITIALIZING
        
        try:
            # Call on_init if it exists
            if hasattr(component, 'on_init') and callable(component.on_init):
                logger.debug(f"Calling on_init for {name}")
                result = component.on_init()
                # If on_init is async, await it
                if inspect.iscoroutine(result):
                    await result
            
            self._states[name] = LifecycleState.INITIALIZED
            logger.debug(f"Initialized component: {name}")
        
        except Exception as e:
            self._states[name] = LifecycleState.CREATED  # Rollback state
            logger.error(f"Failed to initialize {name}: {e}", exc_info=True)
            raise LifecycleError(f"Failed to initialize {name}: {e}") from e
    
    def _destroy_component(self, name: str) -> None:
        """Destroy a single component.
        
        Args:
            name: Component identifier
        """
        component = self._components[name]
        current_state = self._states[name]
        
        if current_state == LifecycleState.DESTROYED:
            logger.debug(f"Component {name} already destroyed, skipping")
            return
        
        self._states[name] = LifecycleState.DESTROYING
        
        try:
            # Call on_destroy if it exists
            if hasattr(component, 'on_destroy') and callable(component.on_destroy):
                logger.debug(f"Calling on_destroy for {name}")
                result = component.on_destroy()
                # If on_destroy returns a coroutine, it needs to be awaited
                if inspect.iscoroutine(result):
                    logger.warning(f"Component {name}.on_destroy() is async but called synchronously. Use destroy_all_async() instead.")
                    # Clean up the coroutine to avoid warnings
                    result.close()
            
            self._states[name] = LifecycleState.DESTROYED
            logger.debug(f"Destroyed component: {name}")
        
        except Exception as e:
            # Don't rollback state on destroy failure
            logger.error(f"Error destroying {name}: {e}", exc_info=True)
            raise
    
    async def _destroy_component_async(self, name: str) -> None:
        """Destroy a single component (async version).
        
        Args:
            name: Component identifier
        """
        component = self._components[name]
        current_state = self._states[name]
        
        if current_state == LifecycleState.DESTROYED:
            logger.debug(f"Component {name} already destroyed, skipping")
            return
        
        self._states[name] = LifecycleState.DESTROYING
        
        try:
            # Call on_destroy if it exists
            if hasattr(component, 'on_destroy') and callable(component.on_destroy):
                logger.debug(f"Calling on_destroy for {name}")
                result = component.on_destroy()
                # If on_destroy is async, await it
                if inspect.iscoroutine(result):
                    await result
            
            self._states[name] = LifecycleState.DESTROYED
            logger.debug(f"Destroyed component: {name}")
        
        except Exception as e:
            # Don't rollback state on destroy failure
            logger.error(f"Error destroying {name}: {e}", exc_info=True)
            raise
    
    def _calculate_order(self) -> List[str]:
        """Calculate initialization order using topological sort.
        
        Returns:
            List of component names in initialization order
        
        Raises:
            LifecycleError: If circular dependency detected
        """
        # Build adjacency list
        names = list(self._components.keys())
        graph: Dict[str, List[str]] = {name: [] for name in names}
        in_degree: Dict[str, int] = {name: 0 for name in names}
        
        for name in names:
            for dep in self._dependencies.get(name, []):
                if dep in names:
                    graph[dep].append(name)
                    in_degree[name] += 1
        
        # Kahn's algorithm
        queue = [name for name in names if in_degree[name] == 0]
        result = []
        
        while queue:
            # Sort for deterministic ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(names):
            unprocessed = [name for name in names if name not in result]
            raise LifecycleError(
                f"Circular dependency detected among: {unprocessed}"
            )
        
        return result
    
    def clear(self) -> None:
        """Clear all components (without destroying them).
        
        Useful for testing or reinitialization.
        """
        self._components.clear()
        self._dependencies.clear()
        self._states.clear()
        self._initialization_order.clear()
        logger.debug("Cleared lifecycle manager")
