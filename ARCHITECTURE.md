# Cullinan Framework - New Architecture (v0.8.0)

## Overview

Cullinan v0.8.0 introduces a completely refactored architecture based on modular design principles, dependency injection, and lifecycle management. This document describes the new architecture and how to use it.

## Architecture Principles

### 1. **Modular Design**
All components are organized into clearly separated modules with well-defined responsibilities.

### 2. **Unified Registry Pattern**
All subsystems (services, handlers) use a common base `Registry` class from `cullinan.core`.

### 3. **Dependency Injection**
Optional dependency injection for services, making testing and composition easier.

### 4. **Lifecycle Management**
Components can implement `on_init()` and `on_destroy()` hooks for proper initialization and cleanup.

### 5. **100% Backward Compatible**
All existing code continues to work without modification. New features are opt-in.

## Module Structure

```
cullinan/
├── core/                    # Foundation: Registry, DI, Lifecycle
│   ├── registry.py         # Base Registry class
│   ├── injection.py        # DependencyInjector
│   ├── lifecycle.py        # LifecycleManager
│   ├── types.py            # Common types
│   └── exceptions.py       # Core exceptions
│
├── service/            # Enhanced service layer
│   ├── base.py            # Service base class
│   ├── registry.py        # ServiceRegistry
│   └── decorators.py      # @service decorator
│
├── handler/               # Handler management
│   ├── base.py            # BaseHandler class
│   └── registry.py        # HandlerRegistry
│
├── middleware/            # Request/Response middleware
│   └── base.py            # Middleware & MiddlewareChain
│
├── monitoring/            # Monitoring & observability
│   └── hooks.py           # MonitoringHook & Manager
│
└── testing/               # Testing utilities
    ├── fixtures.py        # Test fixtures
    ├── mocks.py           # Mock objects
    └── registry.py        # Test registries
```

## Dependency Flow

```
┌──────────┐
│   core   │  ← Foundation (no dependencies)
└────┬─────┘
     │
     ├─────→ service       ← Uses core.Registry
     ├─────→ handler       ← Uses core.Registry
     ├─────→ middleware    ← Standalone
     ├─────→ monitoring    ← Standalone
     └─────→ testing       ← Uses core & service
```

**Rule**: Core module has no dependencies. All other modules may depend on core.

## Core Module

### Registry Base Class

All registries inherit from `cullinan.core.Registry`:

```python
from cullinan.core import Registry

class MyRegistry(Registry[MyType]):
    def register(self, name: str, item: MyType, **metadata):
        # Implementation
        pass
    
    def get(self, name: str) -> Optional[MyType]:
        # Implementation
        pass
```

### Dependency Injection

The `DependencyInjector` resolves dependencies:

```python
from cullinan.core import DependencyInjector

injector = DependencyInjector()
injector.register_provider('service_a', ServiceA)
injector.register_provider('service_b', ServiceB, dependencies=['service_a'])

instance = injector.resolve('service_b')
# service_b will have service_a injected
```

### Lifecycle Management

The `LifecycleManager` handles component initialization and cleanup:

```python
from cullinan.core import LifecycleManager

manager = LifecycleManager()
manager.register_component('service_a', service_a)
manager.register_component('service_b', service_b, dependencies=['service_a'])

manager.initialize_all()  # Initializes in dependency order
# ... use services ...
manager.destroy_all()     # Destroys in reverse order
```

## Service Layer

### Basic Service (No Dependencies)

```python
from cullinan import service, Service

@service
class EmailService(Service):
    def send_email(self, to, subject, body):
        print(f"Sending email to {to}")
```

### Service with Dependencies

```python
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        # Access injected dependencies
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name):
        user = {'name': name}
        self.email.send_email(name, "Welcome", "Welcome!")
        return user
```

### Lifecycle Hooks

```python
@service
class DatabaseService(Service):
    def on_init(self):
        # Called after dependencies are injected
        self.connection = create_connection()
    
    def on_destroy(self):
        # Called during shutdown
        self.connection.close()
```

## Handler Module

### HandlerRegistry

The `HandlerRegistry` now uses `core.Registry`:

```python
from cullinan import HandlerRegistry, get_handler_registry

# Get global registry
registry = get_handler_registry()

# Register handlers
registry.register('/api/users', UserHandler)
registry.register('/api/posts/([a-zA-Z0-9-]+)', PostHandler)

# Sort by priority (static before dynamic)
registry.sort()

# Get all handlers
handlers = registry.get_handlers()
```

### BaseHandler

Handlers can implement lifecycle hooks:

```python
from cullinan.handler import BaseHandler

class MyHandler(BaseHandler):
    def on_init(self):
        # Initialize resources
        pass
    
    def on_destroy(self):
        # Cleanup resources
        pass
```

## Middleware

### Creating Middleware

```python
from cullinan import Middleware

class LoggingMiddleware(Middleware):
    def process_request(self, request):
        print(f"Request: {request.method} {request.path}")
        return request  # Continue processing
    
    def process_response(self, request, response):
        print(f"Response: {response.status_code}")
        return response
```

### Middleware Chain

```python
from cullinan import MiddlewareChain

chain = MiddlewareChain()
chain.add(AuthMiddleware())
chain.add(LoggingMiddleware())

# Process request (forward order)
request = chain.process_request(request)

# ... handle request ...

# Process response (reverse order)
response = chain.process_response(request, response)
```

### Short-Circuit

Return `None` to stop processing:

```python
class AuthMiddleware(Middleware):
    def process_request(self, request):
        if not request.has_valid_token():
            # Short-circuit: return None
            return None
        return request
```

## Monitoring

### Creating Monitoring Hooks

```python
from cullinan import MonitoringHook

class MetricsHook(MonitoringHook):
    def on_request_start(self, context):
        context['start_time'] = time.time()
    
    def on_request_end(self, context):
        duration = time.time() - context['start_time']
        self.metrics.record('request_duration', duration)
    
    def on_error(self, error, context):
        self.metrics.increment('errors')
```

### Monitoring Manager

```python
from cullinan import MonitoringManager, get_monitoring_manager

manager = get_monitoring_manager()
manager.register(MetricsHook())
manager.register(LoggingHook())

# Events are dispatched to all hooks
manager.on_request_start({'path': '/api/users'})
manager.on_request_end({'path': '/api/users', 'status': 200})
```

## Testing

### Service Testing

```python
from cullinan import ServiceTestCase, MockService

class TestUserService(ServiceTestCase):
    def test_create_user(self):
        # Use isolated test registry
        mock_email = MockService()
        self.registry.register_mock('EmailService', mock_email)
        self.registry.register('UserService', UserService, 
                              dependencies=['EmailService'])
        
        service = self.registry.get('UserService')
        user = service.create_user('John')
        
        # Verify mock was called
        self.assertTrue(mock_email.was_called('send_email'))
```

### Mock Services

```python
class MockEmailService(MockService):
    def send_email(self, to, subject, body):
        self.record_call('send_email', to=to, subject=subject, body=body)
        return True

# Check call history
mock.was_called('send_email')
mock.get_call_args('send_email')
mock.get_all_calls()
mock.reset_calls()
```

## Migration Guide

### For Existing Code

**No changes required!** All existing code continues to work:

```python
# Old code (v0.7.x) - Still works in v0.8+
@service
class UserService(Service):
    pass
```

### Adopting New Features

Gradually adopt new features:

```python
# Step 1: Add lifecycle hooks
@service
class UserService(Service):
    def on_init(self):
        print("Service initialized")

# Step 2: Add dependencies
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
```

## API Reference

### Core Module

- `Registry[T]` - Abstract base class for registries
- `SimpleRegistry[T]` - Concrete registry implementation
- `DependencyInjector` - Dependency injection engine
- `LifecycleManager` - Lifecycle management
- `LifecycleState` - Enum for lifecycle states
- `LifecycleAware` - Protocol for lifecycle-aware components

### Service Module

- `Service` - Base class for services
- `ServiceRegistry` - Registry for services
- `@service` - Decorator for registering services
- `get_service_registry()` - Get global service registry
- `reset_service_registry()` - Reset for testing

### Handler Module

- `HandlerRegistry` - Registry for HTTP handlers
- `BaseHandler` - Base class for handlers
- `get_handler_registry()` - Get global handler registry
- `reset_handler_registry()` - Reset for testing

### Middleware Module

- `Middleware` - Base class for middleware
- `MiddlewareChain` - Chain of middleware processors

### Monitoring Module

- `MonitoringHook` - Base class for monitoring hooks
- `MonitoringManager` - Manager for monitoring hooks
- `get_monitoring_manager()` - Get global monitoring manager
- `reset_monitoring_manager()` - Reset for testing

### Testing Module

- `ServiceTestCase` - Base class for service tests
- `MockService` - Mock service implementation
- `TestRegistry` - Isolated test registry

## Best Practices

### 1. Service Design

- Keep services focused on a single responsibility
- Declare dependencies explicitly
- Use lifecycle hooks for resource management

### 2. Dependency Injection

- Use DI for testing and composition
- Keep simple cases simple (no DI required)
- Avoid circular dependencies

### 3. Middleware

- Keep middleware focused and composable
- Order matters: auth before logging, etc.
- Use short-circuit sparingly

### 4. Monitoring

- Hook into key events only
- Handle errors gracefully in hooks
- Keep hook processing fast

### 5. Testing

- Use isolated test registries
- Mock external dependencies
- Test services in isolation

## Performance

The new architecture maintains excellent performance:

- Registry lookup: < 1μs (dictionary access)
- DI resolution: < 100μs (typical dependency tree)
- No overhead for non-DI code paths
- Middleware chain: minimal overhead

## Version History

- **v0.8.0-alpha**: New modular architecture
  - Core module with unified registry
  - Enhanced service layer with DI
  - Handler module refactoring
  - Middleware support
  - Monitoring hooks
  - 100% backward compatible

## Further Reading

- `next_docs/` - Detailed architecture analysis and design
- `tests/` - Comprehensive test examples
- `examples/` - Example applications

## Support

- GitHub Issues: Report bugs or request features
- Documentation: See `next_docs/` for detailed guides
- Examples: See `examples/` for usage patterns
