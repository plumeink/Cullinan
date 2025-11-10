# Core Module Design Specification

## Executive Summary

This document provides detailed technical design for Cullinan's new `core` module, which will serve as the foundation for dependency injection, lifecycle management, and unified registry patterns across the framework.

## 1. Module Structure

### 1.1 Directory Layout

```
cullinan/
├── core/                    # NEW: Core module
│   ├── __init__.py         # Public API exports
│   ├── registry.py         # Base Registry class
│   ├── injection.py        # Dependency injection engine
│   ├── lifecycle.py        # Lifecycle management
│   ├── context.py          # Request/application context
│   ├── exceptions.py       # Core-specific exceptions
│   └── types.py            # Type definitions
│
├── service/                # ENHANCED: Service layer
│   ├── __init__.py
│   ├── base.py            # Service base class
│   ├── registry.py        # ServiceRegistry (uses core)
│   └── decorators.py      # @service decorator
│
├── handler/               # ENHANCED: Handler layer
│   ├── __init__.py
│   ├── controller.py      # Controller base
│   ├── registry.py        # HandlerRegistry (uses core)
│   └── routing.py         # Route parsing
│
├── testing/               # NEW: Testing utilities
│   ├── __init__.py
│   ├── fixtures.py        # Test fixtures
│   ├── mocks.py           # Mock objects
│   └── registry.py        # Test registries
│
└── [existing modules...]
```

### 1.2 Dependency Graph

```
┌─────────────────────────────────────────┐
│           cullinan.core                  │
│  (Base classes, no dependencies)         │
└────────────┬────────────────────────────┘
             │
             ├──────────────┬──────────────┐
             ↓              ↓              ↓
      ┌──────────┐   ┌──────────┐  ┌──────────┐
      │ service  │   │ handler  │  │ testing  │
      └──────────┘   └──────────┘  └──────────┘
```

**Design Principle**: Core module has no dependencies on other Cullinan modules.

## 2. Core Registry (core/registry.py)

### 2.1 Base Registry Class

```python
# cullinan/core/registry.py
"""Base registry pattern for Cullinan framework.

Provides a generic, type-safe registry that can be extended for
specific use cases (services, handlers, etc.).
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, Optional, Any, List
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Type of items being registered


class Registry(ABC, Generic[T]):
    """Abstract base class for all registries in Cullinan.
    
    Provides common functionality for registration, retrieval, and
    management of framework components.
    
    Type Parameters:
        T: The type of items this registry manages
    
    Usage:
        class MyRegistry(Registry[MyType]):
            def register(self, name: str, item: MyType, **metadata):
                # Implementation
                pass
    """
    
    def __init__(self):
        """Initialize an empty registry."""
        self._items: Dict[str, T] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._initialized: bool = False
    
    @abstractmethod
    def register(self, name: str, item: T, **metadata) -> None:
        """Register an item with optional metadata.
        
        Args:
            name: Unique identifier for the item
            item: The item to register
            **metadata: Additional metadata (implementation-specific)
        
        Raises:
            ValueError: If name already registered
        """
        pass
    
    @abstractmethod
    def get(self, name: str) -> Optional[T]:
        """Retrieve a registered item by name.
        
        Args:
            name: Identifier of the item to retrieve
        
        Returns:
            The registered item, or None if not found
        """
        pass
    
    def has(self, name: str) -> bool:
        """Check if an item is registered.
        
        Args:
            name: Identifier to check
        
        Returns:
            True if item is registered, False otherwise
        """
        return name in self._items
    
    def list_all(self) -> Dict[str, T]:
        """Get all registered items.
        
        Returns:
            Dictionary mapping names to items
        """
        return self._items.copy()
    
    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a registered item.
        
        Args:
            name: Identifier of the item
        
        Returns:
            Metadata dictionary, or None if not found
        """
        return self._metadata.get(name)
    
    def clear(self) -> None:
        """Clear all registered items.
        
        Warning:
            This should primarily be used in testing. Clearing a
            registry in production code may lead to unexpected behavior.
        """
        self._items.clear()
        self._metadata.clear()
        self._initialized = False
        logger.warning(f"{self.__class__.__name__} cleared")
    
    def count(self) -> int:
        """Get the number of registered items.
        
        Returns:
            Number of items in the registry
        """
        return len(self._items)
    
    def _validate_name(self, name: str) -> None:
        """Validate that a name is acceptable.
        
        Args:
            name: Name to validate
        
        Raises:
            ValueError: If name is invalid
        """
        if not name:
            raise ValueError("Name cannot be empty")
        if not isinstance(name, str):
            raise ValueError(f"Name must be string, got {type(name)}")
    
    def _check_duplicate(self, name: str, allow_override: bool = False) -> None:
        """Check if name is already registered.
        
        Args:
            name: Name to check
            allow_override: If True, don't raise error on duplicate
        
        Raises:
            ValueError: If name already exists and override not allowed
        """
        if name in self._items and not allow_override:
            raise ValueError(
                f"Item '{name}' already registered in {self.__class__.__name__}"
            )


class SimpleRegistry(Registry[Any]):
    """Concrete implementation for simple use cases.
    
    Usage:
        registry = SimpleRegistry()
        registry.register('my_item', some_object)
        item = registry.get('my_item')
    """
    
    def register(self, name: str, item: Any, **metadata) -> None:
        """Register an item."""
        self._validate_name(name)
        self._check_duplicate(name)
        
        self._items[name] = item
        self._metadata[name] = metadata
        
        logger.debug(f"Registered '{name}' in {self.__class__.__name__}")
    
    def get(self, name: str) -> Optional[Any]:
        """Get a registered item."""
        return self._items.get(name)
```

### 2.2 Design Rationale

**Why Generic?**
- Type safety with TypeVar
- Static analysis support
- IDE autocomplete

**Why Abstract?**
- Forces implementation to define registration logic
- Allows customization per use case
- Maintains common interface

**Why Metadata?**
- Extensibility for dependencies, tags, etc.
- No need to modify base class
- Implementation-specific data

## 3. Dependency Injection (core/injection.py)

### 3.1 Dependency Injector

```python
# cullinan/core/injection.py
"""Dependency injection engine for Cullinan framework.

Provides lightweight dependency resolution with circular dependency
detection and lazy instantiation.
"""

from typing import Dict, List, Set, Callable, Any, Optional
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class DependencyResolutionError(Exception):
    """Raised when dependencies cannot be resolved."""
    pass


class CircularDependencyError(DependencyResolutionError):
    """Raised when circular dependencies are detected."""
    pass


class DependencyInjector:
    """Lightweight dependency injection engine.
    
    Manages service providers and resolves dependencies with
    circular dependency detection.
    
    Usage:
        injector = DependencyInjector()
        injector.register_provider('EmailService', lambda: EmailService())
        injector.register_provider('UserService', 
            lambda: UserService(), 
            dependencies=['EmailService'])
        
        services = injector.resolve(['UserService'])
        # Returns: {'UserService': <UserService instance>}
    """
    
    def __init__(self):
        """Initialize the dependency injector."""
        self._providers: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._dependencies: Dict[str, List[str]] = defaultdict(list)
        self._resolved: Set[str] = set()
    
    def register_provider(
        self,
        name: str,
        provider: Callable,
        dependencies: Optional[List[str]] = None,
        singleton: bool = True
    ) -> None:
        """Register a dependency provider.
        
        Args:
            name: Unique identifier for the dependency
            provider: Callable that returns an instance
            dependencies: List of dependency names required
            singleton: If True, provider called once and cached
        
        Example:
            injector.register_provider(
                'EmailService',
                lambda: EmailService(config),
                dependencies=[],
                singleton=True
            )
        """
        if name in self._providers:
            logger.warning(f"Overriding provider for '{name}'")
        
        self._providers[name] = provider
        self._dependencies[name] = dependencies or []
        
        if singleton:
            # Mark as singleton by adding to singletons dict with None
            # Will be populated on first resolve
            pass
        
        logger.debug(f"Registered provider for '{name}' with deps: {dependencies}")
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance directly.
        
        Args:
            name: Unique identifier
            instance: The singleton instance
        
        Example:
            injector.register_singleton('Config', config_instance)
        """
        if name in self._singletons:
            logger.warning(f"Overriding singleton '{name}'")
        
        self._singletons[name] = instance
        self._resolved.add(name)
        logger.debug(f"Registered singleton '{name}'")
    
    def resolve(self, dependencies: List[str]) -> Dict[str, Any]:
        """Resolve a list of dependencies.
        
        Args:
            dependencies: List of dependency names to resolve
        
        Returns:
            Dictionary mapping names to resolved instances
        
        Raises:
            DependencyResolutionError: If dependency not found
            CircularDependencyError: If circular dependency detected
        
        Example:
            deps = injector.resolve(['UserService', 'EmailService'])
            user_service = deps['UserService']
        """
        resolved = {}
        
        # Check for circular dependencies first
        for dep_name in dependencies:
            self._check_circular_dependency(dep_name)
        
        # Resolve in topological order
        order = self._topological_sort(dependencies)
        
        for dep_name in order:
            if dep_name in self._singletons:
                resolved[dep_name] = self._singletons[dep_name]
            elif dep_name in self._providers:
                instance = self._resolve_provider(dep_name, resolved)
                resolved[dep_name] = instance
            else:
                raise DependencyResolutionError(
                    f"No provider found for dependency: {dep_name}"
                )
        
        return {name: resolved[name] for name in dependencies}
    
    def _resolve_provider(
        self,
        name: str,
        already_resolved: Dict[str, Any]
    ) -> Any:
        """Resolve a single provider with its dependencies.
        
        Args:
            name: Name of the dependency to resolve
            already_resolved: Already resolved dependencies
        
        Returns:
            Instance from the provider
        """
        # Check if already a singleton
        if name in self._singletons:
            return self._singletons[name]
        
        provider = self._providers[name]
        instance = provider()
        
        # Store as singleton for reuse
        self._singletons[name] = instance
        self._resolved.add(name)
        
        logger.debug(f"Resolved '{name}'")
        return instance
    
    def _check_circular_dependency(
        self,
        start: str,
        visited: Optional[Set[str]] = None,
        path: Optional[List[str]] = None
    ) -> None:
        """Check for circular dependencies using DFS.
        
        Args:
            start: Starting dependency name
            visited: Set of visited nodes
            path: Current path (for error reporting)
        
        Raises:
            CircularDependencyError: If cycle detected
        """
        if visited is None:
            visited = set()
        if path is None:
            path = []
        
        if start in path:
            cycle = ' -> '.join(path + [start])
            raise CircularDependencyError(
                f"Circular dependency detected: {cycle}"
            )
        
        if start in visited:
            return
        
        visited.add(start)
        path.append(start)
        
        for dep in self._dependencies.get(start, []):
            self._check_circular_dependency(dep, visited, path.copy())
    
    def _topological_sort(self, dependencies: List[str]) -> List[str]:
        """Sort dependencies in resolution order using Kahn's algorithm.
        
        Args:
            dependencies: List of dependency names
        
        Returns:
            Sorted list (dependencies resolved before dependents)
        """
        # Build graph and in-degree count
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Collect all nodes (dependencies + their dependencies)
        all_nodes = set(dependencies)
        for dep in dependencies:
            all_nodes.update(self._get_all_dependencies(dep))
        
        # Build adjacency list
        for node in all_nodes:
            deps = self._dependencies.get(node, [])
            for dep in deps:
                graph[dep].append(node)
                in_degree[node] += 1
        
        # Kahn's algorithm
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(all_nodes):
            raise CircularDependencyError(
                "Circular dependency detected during topological sort"
            )
        
        return result
    
    def _get_all_dependencies(self, name: str) -> Set[str]:
        """Get all transitive dependencies for a name.
        
        Args:
            name: Dependency name
        
        Returns:
            Set of all dependency names (direct and transitive)
        """
        all_deps = set()
        to_process = deque([name])
        
        while to_process:
            current = to_process.popleft()
            deps = self._dependencies.get(current, [])
            
            for dep in deps:
                if dep not in all_deps:
                    all_deps.add(dep)
                    to_process.append(dep)
        
        return all_deps
    
    def clear(self) -> None:
        """Clear all registered providers and singletons.
        
        Warning:
            Use primarily for testing.
        """
        self._providers.clear()
        self._singletons.clear()
        self._dependencies.clear()
        self._resolved.clear()
        logger.debug("Dependency injector cleared")
```

### 3.2 Design Rationale

**Topological Sort**:
- Ensures dependencies resolved before dependents
- Handles complex dependency graphs
- Efficient O(V + E) complexity

**Circular Dependency Detection**:
- Early detection prevents runtime errors
- Clear error messages with cycle path
- DFS-based algorithm

**Singleton Pattern**:
- Lazy instantiation (created on first use)
- Cached for reuse
- Memory efficient

## 4. Lifecycle Management (core/lifecycle.py)

### 4.1 Lifecycle Manager

```python
# cullinan/core/lifecycle.py
"""Component lifecycle management for Cullinan framework.

Manages initialization and destruction of framework components
with proper ordering and error handling.
"""

from enum import Enum
from typing import Any, Dict, List, Callable, Optional
from collections import OrderedDict
import logging
import asyncio

logger = logging.getLogger(__name__)


class LifecycleState(Enum):
    """Component lifecycle states."""
    CREATED = "created"          # Component registered
    INITIALIZING = "initializing"  # on_init() running
    INITIALIZED = "initialized"    # on_init() complete
    RUNNING = "running"           # Component active
    STOPPING = "stopping"         # on_destroy() running
    STOPPED = "stopped"           # on_destroy() complete
    FAILED = "failed"             # Initialization failed


class LifecycleError(Exception):
    """Raised when lifecycle operation fails."""
    pass


class LifecycleManager:
    """Manages component lifecycle (initialization and destruction).
    
    Ensures components are initialized in correct order (dependencies first)
    and destroyed in reverse order.
    
    Usage:
        manager = LifecycleManager()
        manager.register_component('db', database_service)
        manager.register_component('user', user_service, dependencies=['db'])
        
        # Initialize all
        manager.initialize_all()
        
        # Later, during shutdown
        manager.shutdown_all()
    """
    
    def __init__(self):
        """Initialize the lifecycle manager."""
        self._components: OrderedDict[str, Any] = OrderedDict()
        self._states: Dict[str, LifecycleState] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._init_order: List[str] = []
    
    def register_component(
        self,
        name: str,
        component: Any,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """Register a component for lifecycle management.
        
        Args:
            name: Unique identifier
            component: Component instance (must have on_init/on_destroy methods)
            dependencies: List of component names this depends on
        
        Example:
            manager.register_component(
                'EmailService',
                email_service,
                dependencies=['ConfigService']
            )
        """
        if name in self._components:
            logger.warning(f"Overriding component '{name}'")
        
        self._components[name] = component
        self._states[name] = LifecycleState.CREATED
        self._dependencies[name] = dependencies or []
        
        logger.debug(f"Registered component '{name}' with deps: {dependencies}")
    
    def initialize_all(self) -> None:
        """Initialize all registered components in dependency order.
        
        Components are initialized in topological order (dependencies first).
        If a component's on_init() raises an exception, initialization stops
        and the error is propagated.
        
        Raises:
            LifecycleError: If initialization fails
        """
        logger.info("Initializing all components...")
        
        # Determine initialization order
        self._init_order = self._get_initialization_order()
        
        # Initialize in order
        for name in self._init_order:
            self._initialize_component(name)
        
        logger.info(f"Initialized {len(self._init_order)} components")
    
    async def initialize_all_async(self) -> None:
        """Async version of initialize_all().
        
        Calls async on_init() if available, falls back to sync.
        """
        logger.info("Initializing all components (async)...")
        
        self._init_order = self._get_initialization_order()
        
        for name in self._init_order:
            await self._initialize_component_async(name)
        
        logger.info(f"Initialized {len(self._init_order)} components (async)")
    
    def shutdown_all(self) -> None:
        """Shutdown all components in reverse initialization order.
        
        Components are destroyed in reverse order (dependents first).
        Errors during shutdown are logged but don't stop the process.
        """
        logger.info("Shutting down all components...")
        
        # Shutdown in reverse order
        for name in reversed(self._init_order):
            try:
                self._destroy_component(name)
            except Exception as e:
                # Log but continue shutdown
                logger.error(f"Error destroying component '{name}': {e}")
        
        logger.info("Shutdown complete")
    
    async def shutdown_all_async(self) -> None:
        """Async version of shutdown_all()."""
        logger.info("Shutting down all components (async)...")
        
        for name in reversed(self._init_order):
            try:
                await self._destroy_component_async(name)
            except Exception as e:
                logger.error(f"Error destroying component '{name}': {e}")
        
        logger.info("Shutdown complete (async)")
    
    def get_state(self, name: str) -> Optional[LifecycleState]:
        """Get the current state of a component.
        
        Args:
            name: Component name
        
        Returns:
            Current state, or None if not registered
        """
        return self._states.get(name)
    
    def _initialize_component(self, name: str) -> None:
        """Initialize a single component.
        
        Args:
            name: Component name
        
        Raises:
            LifecycleError: If initialization fails
        """
        component = self._components[name]
        self._states[name] = LifecycleState.INITIALIZING
        
        try:
            if hasattr(component, 'on_init'):
                logger.debug(f"Calling on_init() for '{name}'")
                component.on_init()
            
            self._states[name] = LifecycleState.INITIALIZED
            logger.debug(f"Initialized '{name}'")
        
        except Exception as e:
            self._states[name] = LifecycleState.FAILED
            raise LifecycleError(
                f"Failed to initialize component '{name}': {e}"
            ) from e
    
    async def _initialize_component_async(self, name: str) -> None:
        """Async version of _initialize_component()."""
        component = self._components[name]
        self._states[name] = LifecycleState.INITIALIZING
        
        try:
            if hasattr(component, 'on_init_async'):
                logger.debug(f"Calling on_init_async() for '{name}'")
                await component.on_init_async()
            elif hasattr(component, 'on_init'):
                logger.debug(f"Calling on_init() for '{name}'")
                component.on_init()
            
            self._states[name] = LifecycleState.INITIALIZED
            logger.debug(f"Initialized '{name}' (async)")
        
        except Exception as e:
            self._states[name] = LifecycleState.FAILED
            raise LifecycleError(
                f"Failed to initialize component '{name}': {e}"
            ) from e
    
    def _destroy_component(self, name: str) -> None:
        """Destroy a single component."""
        component = self._components[name]
        self._states[name] = LifecycleState.STOPPING
        
        try:
            if hasattr(component, 'on_destroy'):
                logger.debug(f"Calling on_destroy() for '{name}'")
                component.on_destroy()
            
            self._states[name] = LifecycleState.STOPPED
            logger.debug(f"Destroyed '{name}'")
        
        except Exception as e:
            logger.error(f"Error in on_destroy() for '{name}': {e}")
            # Don't raise - continue shutdown
    
    async def _destroy_component_async(self, name: str) -> None:
        """Async version of _destroy_component()."""
        component = self._components[name]
        self._states[name] = LifecycleState.STOPPING
        
        try:
            if hasattr(component, 'on_destroy_async'):
                logger.debug(f"Calling on_destroy_async() for '{name}'")
                await component.on_destroy_async()
            elif hasattr(component, 'on_destroy'):
                logger.debug(f"Calling on_destroy() for '{name}'")
                component.on_destroy()
            
            self._states[name] = LifecycleState.STOPPED
            logger.debug(f"Destroyed '{name}' (async)")
        
        except Exception as e:
            logger.error(f"Error in on_destroy() for '{name}': {e}")
    
    def _get_initialization_order(self) -> List[str]:
        """Determine initialization order using topological sort.
        
        Returns:
            List of component names in initialization order
        """
        # Simple topological sort
        from collections import deque
        
        in_degree = {name: 0 for name in self._components}
        graph = {name: [] for name in self._components}
        
        # Build graph
        for name, deps in self._dependencies.items():
            for dep in deps:
                if dep in self._components:
                    graph[dep].append(name)
                    in_degree[name] += 1
        
        # Kahn's algorithm
        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(self._components):
            raise LifecycleError("Circular dependency detected in components")
        
        return result
```

### 4.2 Usage Example

```python
# Service with lifecycle hooks
@service
class DatabaseService(Service):
    def on_init(self):
        """Called during initialization phase."""
        self.pool = create_connection_pool(
            host='localhost',
            port=5432,
            max_connections=10
        )
        logger.info("Database connection pool created")
    
    def on_destroy(self):
        """Called during shutdown phase."""
        self.pool.close()
        logger.info("Database connection pool closed")
    
    def query(self, sql):
        with self.pool.get_connection() as conn:
            return conn.execute(sql)


@service(dependencies=['DatabaseService'])
class UserService(Service):
    def on_init(self):
        """Initialize with database dependency."""
        self.db = self.dependencies['DatabaseService']
        logger.info("UserService initialized")
    
    def create_user(self, name, email):
        return self.db.query(
            f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')"
        )
```

## 5. Service Registry Integration

### 5.1 Enhanced ServiceRegistry

```python
# cullinan/service/registry.py
"""Service registry with dependency injection and lifecycle management."""

from typing import Type, Optional, List, Any
from cullinan.core.registry import Registry
from cullinan.core.injection import DependencyInjector
from cullinan.core.lifecycle import LifecycleManager
from cullinan.service.base import Service


class ServiceNotFoundError(Exception):
    """Raised when a requested service is not registered."""
    pass


class ServiceRegistry(Registry[Type[Service]]):
    """Registry for services with DI and lifecycle support.
    
    Extends the base Registry class to provide service-specific
    functionality including dependency injection and lifecycle management.
    
    Usage:
        registry = ServiceRegistry()
        registry.register('EmailService', EmailService)
        registry.register('UserService', UserService, 
                         dependencies=['EmailService'])
        
        # Get service instance (with DI)
        user_service = registry.get('UserService')
    """
    
    def __init__(self):
        """Initialize the service registry."""
        super().__init__()
        self._injector = DependencyInjector()
        self._lifecycle = LifecycleManager()
        self._instances: Dict[str, Service] = {}
    
    def register(
        self,
        name: str,
        service_class: Type[Service],
        dependencies: Optional[List[str]] = None
    ) -> None:
        """Register a service class.
        
        Args:
            name: Service name (usually class name)
            service_class: Service class (not instance)
            dependencies: List of dependency service names
        """
        self._validate_name(name)
        self._check_duplicate(name)
        
        # Store class
        self._items[name] = service_class
        self._metadata[name] = {
            'dependencies': dependencies or [],
            'singleton': True,
            'class': service_class
        }
        
        # Register with dependency injector
        self._injector.register_provider(
            name,
            lambda: service_class(),
            dependencies=dependencies,
            singleton=True
        )
        
        logger.debug(f"Registered service '{name}' with deps: {dependencies}")
    
    def get(self, name: str) -> Service:
        """Get a service instance with dependency injection.
        
        Args:
            name: Service name
        
        Returns:
            Service instance with dependencies injected
        
        Raises:
            ServiceNotFoundError: If service not registered
        """
        if name not in self._items:
            raise ServiceNotFoundError(
                f"Service '{name}' not registered. "
                f"Available services: {list(self._items.keys())}"
            )
        
        # Return cached instance if exists
        if name in self._instances:
            return self._instances[name]
        
        # Resolve dependencies
        metadata = self._metadata[name]
        dep_names = metadata['dependencies']
        
        if dep_names:
            # Resolve all dependencies
            resolved = self._injector.resolve([name] + dep_names)
            instance = resolved[name]
            
            # Inject dependencies into instance
            instance.dependencies = {
                dep_name: resolved[dep_name]
                for dep_name in dep_names
            }
        else:
            # No dependencies, just instantiate
            service_class = self._items[name]
            instance = service_class()
            instance.dependencies = {}
        
        # Cache instance
        self._instances[name] = instance
        
        # Register with lifecycle manager
        self._lifecycle.register_component(name, instance, dep_names)
        
        return instance
    
    def initialize_all(self) -> None:
        """Initialize all registered services."""
        self._lifecycle.initialize_all()
    
    def shutdown_all(self) -> None:
        """Shutdown all services."""
        self._lifecycle.shutdown_all()
    
    def clear(self) -> None:
        """Clear registry (for testing)."""
        super().clear()
        self._instances.clear()
        self._injector.clear()
        # Don't clear lifecycle manager - might be shutting down
```

## 6. Testing Utilities

### 6.1 Mock Service Helper

```python
# cullinan/testing/mocks.py
"""Mock objects for testing Cullinan applications."""

from typing import Any, Dict, List
from unittest.mock import Mock


class MockService:
    """Base class for mock services.
    
    Provides call tracking and assertion utilities.
    
    Usage:
        class MockEmailService(MockService):
            def send_email(self, to, subject, body):
                self.record_call('send_email', to=to, subject=subject)
                return True
        
        # In test
        mock = MockEmailService()
        mock.send_email('test@example.com', 'Hello', 'Body')
        assert mock.was_called('send_email')
        assert mock.call_count('send_email') == 1
    """
    
    def __init__(self):
        """Initialize the mock service."""
        self._calls: Dict[str, List[Dict[str, Any]]] = {}
        self.dependencies = {}
    
    def record_call(self, method_name: str, **kwargs) -> None:
        """Record a method call.
        
        Args:
            method_name: Name of the method called
            **kwargs: Arguments passed to the method
        """
        if method_name not in self._calls:
            self._calls[method_name] = []
        self._calls[method_name].append(kwargs)
    
    def was_called(self, method_name: str) -> bool:
        """Check if a method was called.
        
        Args:
            method_name: Method name to check
        
        Returns:
            True if method was called at least once
        """
        return method_name in self._calls and len(self._calls[method_name]) > 0
    
    def call_count(self, method_name: str) -> int:
        """Get the number of times a method was called.
        
        Args:
            method_name: Method name
        
        Returns:
            Number of calls
        """
        return len(self._calls.get(method_name, []))
    
    def get_call_args(self, method_name: str, call_index: int = 0) -> Dict[str, Any]:
        """Get arguments from a specific call.
        
        Args:
            method_name: Method name
            call_index: Index of the call (0 = first call)
        
        Returns:
            Dictionary of keyword arguments
        """
        calls = self._calls.get(method_name, [])
        if call_index < len(calls):
            return calls[call_index]
        return {}
    
    def reset(self) -> None:
        """Reset all call records."""
        self._calls.clear()
    
    def on_init(self) -> None:
        """Lifecycle hook (no-op for mocks)."""
        pass
    
    def on_destroy(self) -> None:
        """Lifecycle hook (no-op for mocks)."""
        pass
```

### 6.2 Test Registry Fixture

```python
# cullinan/testing/registry.py
"""Test registry utilities for isolated testing."""

from cullinan.service.registry import ServiceRegistry
from typing import Any, Type, Dict


class TestRegistry(ServiceRegistry):
    """Service registry for testing with enhanced features.
    
    Provides easy mock registration and automatic cleanup.
    
    Usage:
        def test_user_service():
            registry = TestRegistry()
            
            # Register mock
            mock_email = MockEmailService()
            registry.register_mock('EmailService', mock_email)
            
            # Register service under test
            registry.register('UserService', UserService,
                            dependencies=['EmailService'])
            
            # Test
            service = registry.get('UserService')
            service.create_user('John', 'john@example.com')
            
            assert mock_email.was_called('send_email')
    """
    
    def __init__(self):
        """Initialize test registry."""
        super().__init__()
        self._mocks: Dict[str, Any] = {}
    
    def register_mock(self, name: str, mock_instance: Any) -> None:
        """Register a mock instance directly.
        
        Args:
            name: Service name
            mock_instance: Mock object (e.g., MockService instance)
        """
        # Register the type
        self.register(name, type(mock_instance))
        
        # Store instance directly
        self._instances[name] = mock_instance
        self._mocks[name] = mock_instance
        
        # Register with injector
        self._injector.register_singleton(name, mock_instance)
    
    def get_mock(self, name: str) -> Any:
        """Get a registered mock.
        
        Args:
            name: Service name
        
        Returns:
            Mock instance
        """
        return self._mocks.get(name)
    
    def clear(self) -> None:
        """Clear registry and mocks."""
        super().clear()
        self._mocks.clear()
```

## 7. Migration Strategy

### 7.1 Backward Compatibility

**Guarantee**: All existing code works without changes.

```python
# OLD CODE (continues to work)
from cullinan.service import service, Service

@service
class UserService(Service):
    pass

# Access via global dict (legacy)
from cullinan.service import service_list
user_service = service_list['UserService']
```

### 7.2 New Code (Opt-in)

```python
# NEW CODE (with DI)
from cullinan.service import service, Service

@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name, email):
        self.email.send(email, 'Welcome')
```

## 8. Implementation Checklist

### Phase 1: Core Module (Week 1-2)
- [ ] Create `cullinan/core/` directory
- [ ] Implement `Registry` base class
- [ ] Implement `DependencyInjector`
- [ ] Implement `LifecycleManager`
- [ ] Write unit tests (100% coverage target)
- [ ] Write API documentation

### Phase 2: Service Integration (Week 3)
- [ ] Refactor `ServiceRegistry` to use core
- [ ] Update `@service` decorator for DI support
- [ ] Maintain backward compatibility
- [ ] Add integration tests
- [ ] Update examples

### Phase 3: Testing Utilities (Week 4)
- [ ] Create `cullinan/testing/` module
- [ ] Implement `MockService`
- [ ] Implement `TestRegistry`
- [ ] Write testing guide
- [ ] Add test examples

### Phase 4: Documentation (Week 5)
- [ ] API reference documentation
- [ ] Migration guide
- [ ] Best practices guide
- [ ] Example projects
- [ ] Tutorial

## 9. Success Criteria

**Technical**:
- ✅ All existing tests pass
- ✅ 90%+ test coverage on new code
- ✅ No performance regression
- ✅ Zero breaking changes

**Functional**:
- ✅ Dependency injection works correctly
- ✅ Circular dependencies detected
- ✅ Lifecycle hooks called in order
- ✅ Easy to test with mocks

**Documentation**:
- ✅ Complete API documentation
- ✅ Migration guide published
- ✅ 10+ working examples
- ✅ Tutorial for beginners

---

**Document Version**: 1.0  
**Author**: Cullinan Framework Team  
**Date**: 2025-11-10  
**Status**: Final Draft  
**Related**: All previous analysis documents
