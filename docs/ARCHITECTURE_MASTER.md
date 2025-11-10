# Cullinan v0.7x Architecture Guide

**[English](ARCHITECTURE_MASTER.md)** | [中文](zh/ARCHITECTURE_MASTER.md)

**Version**: 0.7x  
**Purpose**: Complete guide to Cullinan's architecture, features, and best practices

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Service Layer](#service-layer)
3. [Registry Pattern](#registry-pattern)
4. [Core Module Design](#core-module-design)
5. [Implementation Details](#implementation-details)
6. [Testing Strategy](#testing-strategy)
7. [Migration Guide](#migration-guide)

---

## Executive Summary

### Framework Overview

Cullinan v0.7x is a complete architectural redesign featuring:

**Core Module** (`cullinan.core`):
- ✅ Base `Registry[T]` pattern with type safety
- ✅ `DependencyInjector` for optional dependency management
- ✅ `LifecycleManager` with initialization/cleanup hooks
- ✅ `RequestContext` for thread-safe request-scoped data

**Enhanced Service Layer** (`cullinan.service`):
- ✅ `Service` base class with lifecycle hooks (`on_init`, `on_destroy`)
- ✅ `ServiceRegistry` with dependency injection
- ✅ `@service` decorator with dependency specification
- ✅ 100% backward compatible transition

**WebSocket Integration** (`cullinan.websocket_registry`):
- ✅ `WebSocketRegistry` with unified pattern
- ✅ `@websocket_handler` decorator
- ✅ Lifecycle support for WebSocket handlers
- ✅ Backward compatible with old `@websocket`

**Documentation & Examples**:
- ✅ Comprehensive README and documentation
- ✅ Migration guide in CHANGELOG.md
- ✅ Complete example: `v070_demo.py` showcasing all features

### Design Philosophy

1. **Lightweight + Progressive Enhancement**: Simple by default, powerful when needed
2. **Explicit over Implicit**: Clear registration and dependency declaration
3. **Modular Design**: Each module has clear boundaries and responsibilities
4. **Production-Ready**: Not just proof-of-concept, ready for real applications
5. **Test-Friendly**: Easy to mock and isolate components

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| **Keep Service Layer** | Provides clear separation of concerns and testability |
| **Unified Registry** | Consistent pattern across all components |
| **Optional DI** | Available for complex scenarios but not required |
| **Lifecycle Hooks** | Proper resource management (init/cleanup) |
| **No Backward Compat** | Clean break allows better architecture |

---

## Service Layer

### Why Use the Service Layer?

The service layer provides clear separation of concerns:

#### 1. Clear Separation of Concerns

```
Controller (HTTP) → Service (Business Logic) → DAO/Model (Data Access)
```

**Benefits**:
- Controllers focus on HTTP concerns (routing, validation, response formatting)
- Services contain reusable business logic
- Clear boundaries make code easier to understand and maintain

#### 2. Enhanced Testability

Without service layer:
```python
# Hard to test - tightly coupled to HTTP
@controller(url='/api')
class UserController:
    @post_api(url='/users')
    def create_user(self, body_params):
        # Business logic mixed with HTTP handling
        user = validate_user_data(body_params)
        send_welcome_email(user['email'])
        save_to_database(user)
        return self.response_build(...)
```

With service layer:
```python
# Easy to test - pure business logic
@service
class UserService(Service):
    def create_user(self, name, email):
        user = {'name': name, 'email': email}
        self.email_service.send_welcome(email)
        return user

# Test without HTTP layer
def test_create_user():
    service = UserService()
    user = service.create_user('John', 'john@example.com')
    assert user['name'] == 'John'
```

#### 3. Dependency Injection

Services can declare dependencies explicitly:

```python
@service(dependencies=['EmailService', 'DatabaseService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
        self.db = self.dependencies['DatabaseService']
```

**Benefits**:
- Clear dependency declaration
- Easier to mock for testing
- Automatic dependency resolution
- Prevents circular dependencies

#### 4. Lifecycle Management

Services can manage resources properly:

```python
@service
class DatabaseService(Service):
    def on_init(self):
        self.pool = create_connection_pool()
        print("Database pool created")
    
    def on_destroy(self):
        self.pool.close()
        print("Database pool closed")
```

**Benefits**:
- Proper resource initialization
- Automatic cleanup on shutdown
- Connection pooling
- Cache warming

#### 5. Code Reusability

Services can be used from multiple controllers:

```python
@controller(url='/api/users')
class UserController:
    def create_user(self, body_params):
        return self.service['UserService'].create_user(...)

@controller(url='/api/admin')
class AdminController:
    def bulk_create_users(self, body_params):
        # Reuse same service logic
        for user in body_params['users']:
            self.service['UserService'].create_user(...)
```

---

## Registry Pattern

### Unified Registry Design

The registry pattern provides consistent component management across the framework:

#### Base Registry Pattern

```python
class Registry(ABC, Generic[T]):
    """Abstract base for all registries."""
    def register(self, name: str, item: T, **metadata) -> None: ...
    def get(self, name: str) -> Optional[T]: ...
    def has(self, name: str) -> bool: ...
    def list_all(self) -> Dict[str, T]: ...
```

#### Benefits

1. **Consistency**: Same pattern for services, handlers, WebSockets
2. **Type Safety**: Generic type parameter ensures correctness
3. **Metadata**: Extensible metadata storage for each component
4. **Testability**: Easy to create isolated test registries
5. **Introspection**: Can query what's registered at runtime

#### Implementation Hierarchy

```
Registry[T] (abstract base)
├── SimpleRegistry[T] (concrete, general use)
├── ServiceRegistry (services + DI)
├── HandlerRegistry (HTTP handlers)
└── WebSocketRegistry (WebSocket handlers)
```

Each specialized registry extends the base with domain-specific features while maintaining the core interface.

---

## Core Module Design

### Architecture Overview

```
cullinan/
├── core/                      # Foundation
│   ├── __init__.py
│   ├── registry.py            # Base Registry[T]
│   ├── injection.py           # DependencyInjector
│   ├── lifecycle.py           # LifecycleManager
│   ├── context.py             # RequestContext
│   ├── types.py               # LifecycleState, LifecycleAware
│   └── exceptions.py          # Core exceptions
│
├── service/                   # Service Layer
│   ├── __init__.py
│   ├── base.py                # Service base class
│   ├── registry.py            # ServiceRegistry
│   └── decorators.py          # @service decorator
│
├── handler/                   # HTTP Handlers
│   ├── __init__.py
│   ├── base.py                # BaseHandler
│   └── registry.py            # HandlerRegistry
│
├── websocket_registry.py      # WebSocket Support
│
├── middleware/                # Middleware Chain
│   ├── __init__.py
│   ├── base.py
│   └── builtin/
│
├── monitoring/                # Monitoring Hooks
│   ├── __init__.py
│   └── hooks.py
│
└── testing/                   # Testing Utilities
    ├── __init__.py
    ├── fixtures.py
    └── mocks.py
```

### Core Components

#### 1. Registry (`core/registry.py`)

**Purpose**: Base pattern for all registries

**Key Features**:
- Type-safe registration with `Generic[T]`
- Metadata storage for extensibility
- Query methods: `get()`, `has()`, `list_all()`
- Abstract base for consistency

**Usage**:
```python
class ServiceRegistry(Registry[Type[Service]]):
    def register(self, name: str, service_class: Type[Service], **metadata):
        # Service-specific registration logic
        pass
```

#### 2. Dependency Injector (`core/injection.py`)

**Purpose**: Optional dependency management

**Key Features**:
- Provider-based dependency resolution
- Singleton management
- Circular dependency detection
- Lazy instantiation

**Usage**:
```python
injector = DependencyInjector()
injector.register_singleton('config', config_instance)
injector.register_provider('logger', lambda: create_logger())
dependencies = injector.resolve(['config', 'logger'])
```

#### 3. Lifecycle Manager (`core/lifecycle.py`)

**Purpose**: Component lifecycle management

**Key Features**:
- State tracking (UNINITIALIZED → INITIALIZED → DESTROYED)
- Initialization hooks (`on_init`)
- Cleanup hooks (`on_destroy`)
- Automatic state transitions

**Usage**:
```python
manager = LifecycleManager()
manager.register_component('service', service_instance)
manager.initialize_all()  # Calls on_init() on all
# ... application runs ...
manager.shutdown_all()    # Calls on_destroy() on all
```

#### 4. Request Context (`core/context.py`)

**Purpose**: Thread-safe request-scoped data

**Key Features**:
- Context variables for thread safety
- Request-scoped data storage
- Cleanup callbacks
- Metadata support

**Usage**:
```python
with ContextManager():
    ctx = get_current_context()
    ctx.set('user_id', 123)
    ctx.set('request_id', 'abc-123')
    # Context automatically cleaned up on exit
```

---

## Implementation Details

### Service Registration Flow

1. **Decorator Applied**:
   ```python
   @service(dependencies=['EmailService'])
   class UserService(Service):
       pass
   ```

2. **Registration**:
   - Service class registered in ServiceRegistry
   - Dependencies stored in metadata
   - Name derived from class name

3. **First Access**:
   - ServiceRegistry creates singleton instance
   - Dependencies resolved from registry
   - `on_init()` called with resolved dependencies

4. **Usage**:
   ```python
   user_service = registry.get('UserService')
   user_service.create_user(...)
   ```

5. **Shutdown**:
   - `on_destroy()` called on all services
   - Resources cleaned up

### WebSocket Integration

WebSocket handlers follow the same registry pattern:

```python
@websocket_handler(url='/ws/chat')
class ChatHandler:
    def on_init(self):
        # Called when handler is registered
        self.connections = set()
    
    def on_open(self):
        # Called when connection opens
        self.connections.add(self)
    
    def on_message(self, message):
        # Handle incoming message
        pass
    
    def on_close(self):
        # Called when connection closes
        self.connections.remove(self)
```

**Integration**:
- Registered in `WebSocketRegistry`
- URL mapping maintained
- Lifecycle hooks supported
- Can access services via registry

---

## Testing Strategy

### Unit Testing Services

```python
from cullinan.testing import TestRegistry, MockService

def test_user_service():
    # Create isolated test registry
    registry = TestRegistry()
    
    # Register mock dependencies
    email_mock = MockService()
    registry.register_mock('EmailService', email_mock)
    
    # Test service with mocked dependencies
    user_service = UserService()
    registry.inject_dependencies(user_service, ['EmailService'])
    
    # Run test
    user = user_service.create_user('John', 'john@example.com')
    
    # Verify
    assert user['name'] == 'John'
    assert email_mock.send_welcome.called
```

### Integration Testing

```python
def test_full_flow():
    # Use real registry
    from cullinan import get_service_registry
    
    registry = get_service_registry()
    user_service = registry.get('UserService')
    
    # Test with real dependencies
    user = user_service.create_user('Jane', 'jane@example.com')
    assert user is not None
```

### Test Utilities

- `TestRegistry`: Isolated registry for testing
- `MockService`: Mock service implementation
- `ServiceTestCase`: Base test class with setup/teardown
- Helper functions for common testing scenarios

---

## Migration Guide

### From v0.6x to v0.7x

#### 1. Update Service Imports

**Before (v0.6x)**:
```python
from cullinan.service import service, Service
```

**After (v0.7x)**:
```python
from cullinan import service, Service
```

#### 2. Add Lifecycle Hooks (Optional)

```python
@service
class MyService(Service):
    def on_init(self):
        # Initialize resources
        self.pool = create_pool()
    
    def on_destroy(self):
        # Cleanup
        self.pool.close()
```

#### 3. Use Dependency Injection (Optional)

**Before**:
```python
@service
class UserService(Service):
    def __init__(self):
        # Manual dependency management
        self.email = get_email_service()
```

**After**:
```python
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        # Dependencies injected automatically
        self.email = self.dependencies['EmailService']
```

#### 4. Update WebSocket Handlers (Recommended)

**Before**:
```python
from cullinan.websocket import websocket

@websocket(url='/ws/chat')
class ChatHandler:
    pass
```

**After** (preferred):
```python
from cullinan import websocket_handler

@websocket_handler(url='/ws/chat')
class ChatHandler:
    def on_init(self):
        # Lifecycle hook
        pass
```

Both styles work, but new style provides lifecycle hooks.

#### 5. Breaking Changes

- Old `cullinan.service` module is deprecated
- Import from `cullinan` instead
- Deprecation warnings added, will be removed in v0.8.0

---

## Conclusion

### What We Achieved

1. ✅ **Core Module**: Foundation for unified architecture
2. ✅ **Enhanced Services**: DI + lifecycle management
3. ✅ **WebSocket Integration**: Consistent with services
4. ✅ **Request Context**: Thread-safe data management
5. ✅ **Testing Utilities**: Mock support + test registry
6. ✅ **Documentation**: Comprehensive guides + examples
7. ✅ **Migration Path**: Clear upgrade instructions

### Design Principles Validated

- ✅ Lightweight by default, powerful when needed
- ✅ Explicit over implicit
- ✅ Modular and testable
- ✅ Production-ready patterns
- ✅ Progressive enhancement

---

## References

### Related Documents (Archived)

The following detailed analysis documents were consolidated into this master document:

- `01-service-layer-analysis.md` - Service layer value analysis
- `02-registry-pattern-evaluation.md` - Registry pattern deep dive
- `03-architecture-comparison.md` - Framework comparison study
- `04-core-module-design.md` - Core module specifications
- `05-implementation-plan.md` - Implementation roadmap
- `06-migration-guide.md` - Detailed migration instructions
- `07-api-specifications.md` - Complete API reference
- `08-testing-strategy.md` - Testing approach and utilities
- `09-code-examples.md` - Comprehensive code examples
- `10-backward-compatibility.md` - Compatibility analysis

These documents remain available in `next_docs/` for historical reference.

### Key Resources

- **Main Documentation**: `docs/README.md`
- **Quick Reference**: `docs/04-quick-reference.md`
- **Example Application**: `examples/v070_demo.py`
- **CHANGELOG**: `CHANGELOG.md`

---

**Document Version**: 1.0  
**Last Updated**: November 10, 2025  
**Maintained By**: Cullinan Development Team
