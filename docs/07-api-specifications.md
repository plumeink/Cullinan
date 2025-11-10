# API Specifications

## Executive Summary

This document provides complete API specifications for the enhanced Cullinan framework, including the new core module, enhanced service layer, and testing utilities.

## 1. Core Module API

### 1.1 cullinan.core.registry

#### Registry (Abstract Base Class)

```python
class Registry(ABC, Generic[T]):
    """Abstract base class for all registries."""
    
    def __init__(self) -> None:
        """Initialize an empty registry."""
    
    @abstractmethod
    def register(self, name: str, item: T, **metadata) -> None:
        """Register an item with optional metadata.
        
        Args:
            name: Unique identifier for the item
            item: The item to register
            **metadata: Additional metadata (implementation-specific)
        
        Raises:
            ValueError: If name already registered or invalid
        """
    
    @abstractmethod
    def get(self, name: str) -> Optional[T]:
        """Retrieve a registered item by name.
        
        Args:
            name: Identifier of the item to retrieve
        
        Returns:
            The registered item, or None if not found
        """
    
    def has(self, name: str) -> bool:
        """Check if an item is registered.
        
        Args:
            name: Identifier to check
        
        Returns:
            True if item is registered, False otherwise
        """
    
    def list_all(self) -> Dict[str, T]:
        """Get all registered items.
        
        Returns:
            Dictionary mapping names to items
        """
    
    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a registered item.
        
        Args:
            name: Identifier of the item
        
        Returns:
            Metadata dictionary, or None if not found
        """
    
    def clear(self) -> None:
        """Clear all registered items."""
    
    def count(self) -> int:
        """Get the number of registered items."""
```

#### SimpleRegistry

```python
class SimpleRegistry(Registry[Any]):
    """Concrete implementation for simple use cases.
    
    Example:
        registry = SimpleRegistry()
        registry.register('my_item', some_object)
        item = registry.get('my_item')
    """
```

### 1.2 cullinan.core.injection

#### DependencyInjector

```python
class DependencyInjector:
    """Lightweight dependency injection engine."""
    
    def __init__(self) -> None:
        """Initialize the dependency injector."""
    
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
                lambda: EmailService(),
                dependencies=[],
                singleton=True
            )
        """
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance directly.
        
        Args:
            name: Unique identifier
            instance: The singleton instance
        """
    
    def resolve(self, dependencies: List[str]) -> Dict[str, Any]:
        """Resolve a list of dependencies.
        
        Args:
            dependencies: List of dependency names to resolve
        
        Returns:
            Dictionary mapping names to resolved instances
        
        Raises:
            DependencyResolutionError: If dependency not found
            CircularDependencyError: If circular dependency detected
        """
    
    def clear(self) -> None:
        """Clear all registered providers and singletons."""
```

#### Exceptions

```python
class DependencyResolutionError(Exception):
    """Raised when dependencies cannot be resolved."""

class CircularDependencyError(DependencyResolutionError):
    """Raised when circular dependencies are detected."""
```

### 1.3 cullinan.core.lifecycle

#### LifecycleManager

```python
class LifecycleManager:
    """Manages component lifecycle (initialization and destruction)."""
    
    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
    
    def register_component(
        self,
        name: str,
        component: Any,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """Register a component for lifecycle management.
        
        Args:
            name: Unique identifier
            component: Component instance with on_init/on_destroy methods
            dependencies: List of component names this depends on
        """
    
    def initialize_all(self) -> None:
        """Initialize all registered components in dependency order.
        
        Raises:
            LifecycleError: If initialization fails
        """
    
    async def initialize_all_async(self) -> None:
        """Async version of initialize_all()."""
    
    def shutdown_all(self) -> None:
        """Shutdown all components in reverse initialization order."""
    
    async def shutdown_all_async(self) -> None:
        """Async version of shutdown_all()."""
    
    def get_state(self, name: str) -> Optional[LifecycleState]:
        """Get the current state of a component."""
```

#### LifecycleState

```python
class LifecycleState(Enum):
    """Component lifecycle states."""
    CREATED = "created"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
```

## 2. Service Layer API

### 2.1 cullinan.service

#### Service Base Class

```python
class Service:
    """Base class for all services.
    
    Attributes:
        dependencies: Dictionary of injected dependencies
    """
    
    dependencies: Dict[str, Any]
    
    def on_init(self) -> None:
        """Lifecycle hook called after dependencies are injected.
        
        Override this method to perform initialization that requires
        dependencies. This is called once at application startup.
        
        Example:
            def on_init(self):
                self.email = self.dependencies['EmailService']
                self.db = self.dependencies['DatabaseService']
        """
        pass
    
    def on_destroy(self) -> None:
        """Lifecycle hook called during application shutdown.
        
        Override this method to perform cleanup (close connections,
        release resources, etc.). This is called once at shutdown.
        
        Example:
            def on_destroy(self):
                self.connection_pool.close()
        """
        pass
    
    async def on_init_async(self) -> None:
        """Async version of on_init()."""
        pass
    
    async def on_destroy_async(self) -> None:
        """Async version of on_destroy()."""
        pass
```

#### @service Decorator

```python
def service(cls_or_dependencies=None):
    """Decorator to register a service.
    
    Can be used in two ways:
    
    1. Simple registration (no dependencies):
        @service
        class MyService(Service):
            pass
    
    2. With dependencies:
        @service(dependencies=['OtherService'])
        class MyService(Service):
            def on_init(self):
                self.other = self.dependencies['OtherService']
    
    Args:
        cls_or_dependencies: Either a class (simple usage) or a dict
            with 'dependencies' key (advanced usage)
    
    Returns:
        The decorated class (registered in global service registry)
    """
```

#### ServiceRegistry

```python
class ServiceRegistry(Registry[Type[Service]]):
    """Registry for services with DI and lifecycle support."""
    
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
    
    def get(self, name: str) -> Service:
        """Get a service instance with dependency injection.
        
        Args:
            name: Service name
        
        Returns:
            Service instance with dependencies injected
        
        Raises:
            ServiceNotFoundError: If service not registered
        """
    
    def initialize_all(self) -> None:
        """Initialize all registered services."""
    
    def shutdown_all(self) -> None:
        """Shutdown all services."""
```

#### Global Registry Access

```python
def get_service_registry() -> ServiceRegistry:
    """Get the global service registry.
    
    Returns:
        The global ServiceRegistry instance
    """

# Legacy compatibility
service_list: Dict[str, Service]  # Global service dictionary (backward compatible)
```

## 3. Testing Utilities API

### 3.1 cullinan.testing.mocks

#### MockService

```python
class MockService:
    """Base class for mock services with call tracking.
    
    Example:
        class MockEmailService(MockService):
            def send_email(self, to, subject, body):
                self.record_call('send_email', to=to, subject=subject)
                return True
        
        # In test
        mock = MockEmailService()
        mock.send_email('test@example.com', 'Hello', 'Body')
        assert mock.was_called('send_email')
    """
    
    def __init__(self) -> None:
        """Initialize the mock service."""
    
    def record_call(self, method_name: str, **kwargs) -> None:
        """Record a method call.
        
        Args:
            method_name: Name of the method called
            **kwargs: Arguments passed to the method
        """
    
    def was_called(self, method_name: str) -> bool:
        """Check if a method was called.
        
        Args:
            method_name: Method name to check
        
        Returns:
            True if method was called at least once
        """
    
    def call_count(self, method_name: str) -> int:
        """Get the number of times a method was called.
        
        Args:
            method_name: Method name
        
        Returns:
            Number of calls
        """
    
    def get_call_args(self, method_name: str, call_index: int = 0) -> Dict[str, Any]:
        """Get arguments from a specific call.
        
        Args:
            method_name: Method name
            call_index: Index of the call (0 = first call)
        
        Returns:
            Dictionary of keyword arguments
        """
    
    def reset(self) -> None:
        """Reset all call records."""
    
    def on_init(self) -> None:
        """Lifecycle hook (no-op for mocks)."""
    
    def on_destroy(self) -> None:
        """Lifecycle hook (no-op for mocks)."""
```

### 3.2 cullinan.testing.registry

#### TestRegistry

```python
class TestRegistry(ServiceRegistry):
    """Service registry for testing with enhanced features.
    
    Example:
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
            
            # Assertions
            assert mock_email.was_called('send_email')
    """
    
    def register_mock(self, name: str, mock_instance: Any) -> None:
        """Register a mock instance directly.
        
        Args:
            name: Service name
            mock_instance: Mock object (e.g., MockService instance)
        """
    
    def get_mock(self, name: str) -> Any:
        """Get a registered mock.
        
        Args:
            name: Service name
        
        Returns:
            Mock instance
        """
```

## 4. Controller Integration

### 4.1 Accessing Services in Controllers

```python
@controller(url='/api')
class UserController:
    """Controller with service access."""
    
    @post_api(url='/users', body_params=['name', 'email'])
    def create_user(self, body_params):
        """Create a user endpoint.
        
        Services are accessible via self.service dictionary.
        """
        # Access service
        user = self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
        
        return self.response_build(
            status=201,
            message="User created",
            data=user
        )
```

## 5. Configuration API

### 5.1 Application Configuration

```python
from cullinan import configure

# Configure services
configure(
    # ... existing configuration ...
    
    # New service configuration (optional)
    service_config={
        'enable_lifecycle_hooks': True,
        'enable_dependency_injection': True,
        'lazy_initialization': False,
    }
)
```

## 6. Complete Usage Example

```python
# services/email_service.py
from cullinan.service import service, Service

@service
class EmailService(Service):
    def on_init(self):
        # Initialize email client
        self.client = EmailClient()
    
    def send(self, to, subject, body):
        return self.client.send(to, subject, body)
    
    def on_destroy(self):
        self.client.close()


# services/user_service.py
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
        self.db = database.get_connection()
    
    def create_user(self, name, email):
        user = self.db.save({'name': name, 'email': email})
        self.email.send(email, 'Welcome', f'Hello {name}!')
        return user
    
    def on_destroy(self):
        self.db.close()


# controllers/user_controller.py
from cullinan.controller import controller, post_api

@controller(url='/api')
class UserController:
    @post_api(url='/users', body_params=['name', 'email'])
    def create_user(self, body_params):
        user = self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
        return self.response_build(status=201, data=user)


# tests/test_user_service.py
from cullinan.testing import TestRegistry, MockService

class MockEmailService(MockService):
    def send(self, to, subject, body):
        self.record_call('send', to=to, subject=subject, body=body)
        return True

def test_create_user():
    # Setup
    registry = TestRegistry()
    mock_email = MockEmailService()
    registry.register_mock('EmailService', mock_email)
    registry.register('UserService', UserService, dependencies=['EmailService'])
    
    # Test
    service = registry.get('UserService')
    user = service.create_user('John', 'john@example.com')
    
    # Assert
    assert user['name'] == 'John'
    assert mock_email.was_called('send')
    assert mock_email.call_count('send') == 1
    
    args = mock_email.get_call_args('send')
    assert args['to'] == 'john@example.com'
    assert 'Welcome' in args['subject']
```

## 7. Error Handling

### 7.1 Common Exceptions

```python
# Service not found
try:
    service = registry.get('NonExistentService')
except ServiceNotFoundError as e:
    print(f"Error: {e}")

# Circular dependency
try:
    registry.register('ServiceA', ServiceA, dependencies=['ServiceB'])
    registry.register('ServiceB', ServiceB, dependencies=['ServiceA'])
    registry.get('ServiceA')
except CircularDependencyError as e:
    print(f"Circular dependency: {e}")

# Initialization failure
try:
    lifecycle.initialize_all()
except LifecycleError as e:
    print(f"Initialization failed: {e}")
```

## 8. Type Hints

### 8.1 Fully Typed API

```python
from typing import Dict, List, Optional, Any, Type
from cullinan.service import Service, service

@service(dependencies=['EmailService'])
class UserService(Service):
    email: Any  # Will be EmailService after on_init
    
    def on_init(self) -> None:
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name: str, email: str) -> Dict[str, Any]:
        user: Dict[str, Any] = {'name': name, 'email': email}
        self.email.send(email, 'Welcome', f'Hello {name}!')
        return user
```

---

**Document Version**: 1.0  
**Author**: Cullinan Framework Team  
**Date**: 2025-11-10  
**Status**: Final Draft
