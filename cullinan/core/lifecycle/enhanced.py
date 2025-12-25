# -*- coding: utf-8 -*-
"""Complete Lifecycle Management System for Cullinan Framework

Inspired by Spring Boot's lifecycle management, providing:
- Multiple lifecycle phases (like Spring's @PostConstruct, @PreDestroy, etc.)
- Dependency-based initialization order
- Async and sync support
- Phase control (startup priority)
- Graceful shutdown with timeout

Lifecycle Flow:
1. CREATED - Bean instantiated, dependencies injected
2. INITIALIZING - @PostConstruct equivalent (on_post_construct)
3. STARTING - SmartLifecycle.start equivalent (on_startup)
4. RUNNING - Fully initialized and ready
5. STOPPING - SmartLifecycle.stop equivalent (on_shutdown)
6. DESTROYED - @PreDestroy equivalent (on_pre_destroy)
"""

from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
import logging
import asyncio
import inspect
from abc import ABC, abstractmethod

from .exceptions import LifecycleError

logger = logging.getLogger(__name__)


# ============================================================================
# Lifecycle States
# ============================================================================

class LifecyclePhase(Enum):
    """Service lifecycle phases (matches Spring Boot lifecycle)"""
    CREATED = "created"                    # Instance created, dependencies injected
    POST_CONSTRUCT = "post_construct"      # @PostConstruct phase
    STARTING = "starting"                  # SmartLifecycle.start phase
    RUNNING = "running"                    # Fully running
    STOPPING = "stopping"                  # SmartLifecycle.stop phase
    PRE_DESTROY = "pre_destroy"           # @PreDestroy phase
    DESTROYED = "destroyed"                # Completely destroyed


# ============================================================================
# Lifecycle Interfaces (Like Spring's interfaces)
# ============================================================================

class LifecycleAware(ABC):
    """Base interface for components with lifecycle awareness

    Similar to Spring's InitializingBean and DisposableBean combined.
    Subclasses can implement any/all of these methods.
    """

    def on_post_construct(self) -> None:
        """Called after construction and dependency injection.

        Equivalent to @PostConstruct in Spring.
        Use for: Quick initialization, validation, setting up non-blocking resources.
        """
        pass

    def on_startup(self) -> None:
        """Called during application startup (before accepting requests).

        Equivalent to SmartLifecycle.start() in Spring.
        Use for: Starting background tasks, warming up caches, connecting to services.
        """
        pass

    def on_pre_destroy(self) -> None:
        """Called before destruction (during shutdown).

        Equivalent to @PreDestroy in Spring.
        Use for: Quick cleanup, saving state.
        """
        pass

    def on_shutdown(self) -> None:
        """Called during application shutdown.

        Equivalent to SmartLifecycle.stop() in Spring.
        Use for: Graceful shutdown, flushing buffers, closing connections.
        """
        pass

    # Async versions
    async def on_post_construct_async(self) -> None:
        """Async version of on_post_construct"""
        pass

    async def on_startup_async(self) -> None:
        """Async version of on_startup"""
        pass

    async def on_pre_destroy_async(self) -> None:
        """Async version of on_pre_destroy"""
        pass

    async def on_shutdown_async(self) -> None:
        """Async version of on_shutdown"""
        pass


class SmartLifecycle(LifecycleAware):
    """Extended lifecycle with phase control (like Spring's SmartLifecycle)

    Allows controlling startup/shutdown order through phase numbers.
    Lower phase = starts earlier, stops later.
    """

    def get_phase(self) -> int:
        """Return the phase value for this component.

        Default is 0. Lower values start earlier and stop later.

        Examples:
        - Database: -100 (starts very early)
        - Cache: -50
        - Business services: 0 (default)
        - Web controllers: 50 (starts late)
        """
        return 0

    def is_auto_startup(self) -> bool:
        """Whether this component should auto-start.

        Returns:
            True to auto-start (default), False to require manual start
        """
        return True


# ============================================================================
# Lifecycle Manager
# ============================================================================

class LifecycleManager:
    """Manages component lifecycle with Spring Boot-like semantics.

    Features:
    - Dependency-ordered initialization
    - Phase-controlled startup order
    - Async and sync method support
    - Graceful shutdown with timeout
    - Error handling and rollback

    Usage:
        manager = LifecycleManager()

        # Register components
        manager.register(database_service, dependencies=[])
        manager.register(cache_service, dependencies=['DatabaseService'])
        manager.register(bot_service, dependencies=['DatabaseService', 'CacheService'])

        # Startup
        await manager.startup()

        # Shutdown
        await manager.shutdown(timeout=30)
    """

    def __init__(self, shutdown_timeout: int = 30):
        """Initialize lifecycle manager.

        Args:
            shutdown_timeout: Default shutdown timeout in seconds
        """
        self._components: Dict[str, Any] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._phases: Dict[str, LifecyclePhase] = {}
        self._startup_order: List[str] = []
        self._shutdown_timeout = shutdown_timeout

    def register(self, component: Any, name: Optional[str] = None,
                 dependencies: Optional[List[str]] = None) -> None:
        """Register a component for lifecycle management.

        Args:
            component: The component instance
            name: Component name (defaults to class name)
            dependencies: List of dependency component names
        """
        if name is None:
            name = component.__class__.__name__

        self._components[name] = component
        self._dependencies[name] = dependencies or []
        self._phases[name] = LifecyclePhase.CREATED

        logger.debug(f"Registered lifecycle component: {name}")

    def _topological_sort(self) -> List[str]:
        """Sort components by dependency order (topological sort).

        Returns:
            List of component names in dependency order

        Raises:
            LifecycleError: If circular dependency detected
        """
        # Build adjacency graph
        # graph[A] = [B, C] means A depends on B and C
        graph = {name: deps[:] for name, deps in self._dependencies.items()}

        # Calculate in-degree: how many components depend on each component
        in_degree = {name: 0 for name in self._components}

        for name, deps in graph.items():
            # name depends on deps, so increment in_degree for name
            in_degree[name] = len([d for d in deps if d in self._components])

        # Kahn's algorithm: start with nodes that have no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort by phase for stable ordering
            queue.sort(key=lambda n: self._get_component_phase(n))
            node = queue.pop(0)
            result.append(node)

            # For each component that depends on 'node'
            for name, deps in graph.items():
                if node in deps:
                    deps.remove(node)
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        if len(result) != len(self._components):
            raise LifecycleError("Circular dependency detected in lifecycle components")

        return result

    def _get_component_phase(self, name: str) -> int:
        """Get the phase number for a component."""
        component = self._components[name]
        if isinstance(component, SmartLifecycle):
            return component.get_phase()
        return 0

    async def startup(self) -> None:
        """Execute startup lifecycle for all registered components.

        Phases:
        1. POST_CONSTRUCT - Quick initialization after injection
        2. STARTING - Start background tasks, connect to services
        3. RUNNING - Mark as fully running
        """
        logger.info("=" * 70)
        logger.info("Starting application lifecycle...")
        logger.info("=" * 70)

        # Determine startup order
        self._startup_order = self._topological_sort()
        logger.info(f"Startup order: {' -> '.join(self._startup_order)}")

        try:
            # Phase 1: POST_CONSTRUCT
            await self._execute_phase(
                LifecyclePhase.POST_CONSTRUCT,
                sync_method='on_post_construct',
                async_method='on_post_construct_async'
            )

            # Phase 2: STARTING
            await self._execute_phase(
                LifecyclePhase.STARTING,
                sync_method='on_startup',
                async_method='on_startup_async'
            )

            # Phase 3: RUNNING
            for name in self._startup_order:
                self._phases[name] = LifecyclePhase.RUNNING

            logger.info("=" * 70)
            logger.info("Application startup completed successfully")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            logger.info("Rolling back startup...")
            await self.shutdown(force=True)
            raise

    async def shutdown(self, timeout: Optional[int] = None, force: bool = False) -> None:
        """Execute shutdown lifecycle for all registered components.

        Phases:
        1. STOPPING - Stop background tasks, close connections
        2. PRE_DESTROY - Quick cleanup, save state
        3. DESTROYED - Mark as destroyed

        Args:
            timeout: Shutdown timeout in seconds (default: constructor value)
            force: If True, continue shutdown even if errors occur
        """
        timeout = timeout or self._shutdown_timeout
        logger.info("=" * 70)
        logger.info(f"Shutting down application (timeout: {timeout}s)...")
        logger.info("=" * 70)

        try:
            # Shutdown in reverse order
            shutdown_order = list(reversed(self._startup_order))
            logger.info(f"Shutdown order: {' -> '.join(shutdown_order)}")

            # Execute with timeout
            await asyncio.wait_for(
                self._execute_shutdown(shutdown_order, force),
                timeout=timeout
            )

            logger.info("=" * 70)
            logger.info("Application shutdown completed successfully")
            logger.info("=" * 70)

        except asyncio.TimeoutError:
            logger.error(f"Shutdown timeout after {timeout}s")
            if not force:
                raise
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            if not force:
                raise

    async def _execute_shutdown(self, order: List[str], force: bool) -> None:
        """Execute shutdown phases."""
        # Phase 1: STOPPING
        await self._execute_phase(
            LifecyclePhase.STOPPING,
            sync_method='on_shutdown',
            async_method='on_shutdown_async',
            order=order,
            force=force
        )

        # Phase 2: PRE_DESTROY
        await self._execute_phase(
            LifecyclePhase.PRE_DESTROY,
            sync_method='on_pre_destroy',
            async_method='on_pre_destroy_async',
            order=order,
            force=force
        )

        # Phase 3: DESTROYED
        for name in order:
            self._phases[name] = LifecyclePhase.DESTROYED

    async def _execute_phase(
        self,
        phase: LifecyclePhase,
        sync_method: str,
        async_method: str,
        order: Optional[List[str]] = None,
        force: bool = False
    ) -> None:
        """Execute a lifecycle phase for all components.

        Args:
            phase: The lifecycle phase
            sync_method: Name of sync method to call
            async_method: Name of async method to call
            order: Component order (default: startup order)
            force: Continue on errors
        """
        order = order or self._startup_order
        logger.info(f"Executing phase: {phase.value}")

        for name in order:
            component = self._components[name]

            # Skip if component doesn't support this phase
            if not isinstance(component, LifecycleAware):
                continue

            # Update phase
            self._phases[name] = phase

            try:
                # Execute async method first (if exists and not default)
                async_func = getattr(component, async_method, None)
                if async_func and self._is_overridden(component, async_method):
                    logger.debug(f"  {name}.{async_method}()")
                    await async_func()

                # Execute sync method (if exists and not default)
                sync_func = getattr(component, sync_method, None)
                if sync_func and self._is_overridden(component, sync_method):
                    logger.debug(f"  {name}.{sync_method}()")
                    result = sync_func()
                    # Handle if sync method returns awaitable
                    if inspect.isawaitable(result):
                        await result

                logger.info(f"  [OK] {name}")

            except Exception as e:
                logger.error(f"  [FAIL] {name}: {e}")
                if not force:
                    raise LifecycleError(
                        f"Error in {name}.{phase.value}: {e}"
                    ) from e

    def _is_overridden(self, component: Any, method_name: str) -> bool:
        """Check if a method is overridden (not the default implementation)."""
        method = getattr(component, method_name, None)
        if not method or not callable(method):
            return False

        # Check if method is from LifecycleAware base class
        base_method = getattr(LifecycleAware, method_name, None)
        if not base_method:
            return True

        # Compare methods - handle both bound and unbound methods
        try:
            component_func = method.__func__ if hasattr(method, '__func__') else method
            base_func = base_method.__func__ if hasattr(base_method, '__func__') else base_method
            return component_func is not base_func
        except AttributeError:
            # If we can't compare, assume it's overridden
            return True

    def get_phase(self, name: str) -> Optional[LifecyclePhase]:
        """Get current lifecycle phase of a component."""
        return self._phases.get(name)

    def is_running(self, name: str) -> bool:
        """Check if a component is in RUNNING phase."""
        return self._phases.get(name) == LifecyclePhase.RUNNING


# ============================================================================
# Global Lifecycle Manager
# ============================================================================

_global_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get the global lifecycle manager instance."""
    global _global_lifecycle_manager
    if _global_lifecycle_manager is None:
        _global_lifecycle_manager = LifecycleManager()
    return _global_lifecycle_manager


def reset_lifecycle_manager() -> None:
    """Reset the global lifecycle manager (for testing)."""
    global _global_lifecycle_manager
    _global_lifecycle_manager = None


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    'LifecyclePhase',
    'LifecycleAware',
    'SmartLifecycle',
    'LifecycleManager',
    'get_lifecycle_manager',
    'reset_lifecycle_manager',
]

