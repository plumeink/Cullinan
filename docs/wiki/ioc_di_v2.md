# IoC/DI 2.0 Architecture

> **Version**: v0.90  
> **Author**: Plumeink

> This document describes the new IoC/DI 2.0 architecture introduced in Cullinan 0.90.
> For migration from previous versions, see [Import Migration Guide](../import_migration_090.md).

## Overview

Cullinan 0.90 introduces a completely redesigned IoC/DI system with the following key improvements:

- **Single Entry Point**: `ApplicationContext` as the only container entry point
- **Definition/Factory Separation**: Clear separation between definition and instance creation
- **Freeze-After-Startup**: Registry is frozen after refresh, preventing runtime modifications
- **Scope Contracts**: Strict scope enforcement (singleton/prototype/request)
- **Structured Diagnostics**: Stable, reproducible error messages with dependency chains

## Core Components

### ApplicationContext

The single entry point for all container operations:

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

# Create context
ctx = ApplicationContext()

# Register definitions
ctx.register(Definition(
    name='UserService',
    factory=lambda c: UserService(c.get('UserRepository')),
    scope=ScopeType.SINGLETON,
    source='service:UserService'
))

# Refresh (freezes registry, initializes eager beans)
ctx.refresh()

# Resolve dependencies
user_service = ctx.get('UserService')

# Shutdown
ctx.shutdown()
```

### Definition

Immutable dependency definition (frozen after creation):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Unique identifier |
| `factory` | `Callable[[ApplicationContext], Any]` | Yes | Instance creation function |
| `scope` | `ScopeType` | Yes | Scope type (SINGLETON/PROTOTYPE/REQUEST) |
| `source` | `str` | Yes | Source description for diagnostics |
| `type_` | `type` | No | Type for type inference |
| `eager` | `bool` | No | Pre-create on refresh (default: False) |
| `conditions` | `list[Callable]` | No | Conditional registration |
| `dependencies` | `list[str]` | No | Explicit dependencies for ordering |
| `optional` | `bool` | No | Allow missing (for try_get only) |

### ScopeType

```python
from cullinan.core.container import ScopeType

ScopeType.SINGLETON   # Application-level singleton (thread-safe)
ScopeType.PROTOTYPE   # New instance per resolution
ScopeType.REQUEST     # Request-scoped (requires RequestContext)
```

## Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Create    │────▶│  Register   │────▶│   Refresh   │────▶│    Use      │
│   Context   │     │ Definitions │     │  (Freeze)   │     │  (Resolve)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Shutdown   │
                                        └─────────────┘
```

### Freeze Mechanism

After `refresh()`:
- All definitions are frozen
- No new registrations allowed
- Any modification attempt raises `RegistryFrozenError`

```python
ctx.refresh()

# This will raise RegistryFrozenError
ctx.register(Definition(...))  # Error!
```

## Request Scope

Request-scoped dependencies require an active `RequestContext`:

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

ctx = ApplicationContext()
ctx.register(Definition(
    name='RequestData',
    factory=lambda c: RequestData(),
    scope=ScopeType.REQUEST,
    source='request:RequestData'
))
ctx.refresh()

# Without context - raises ScopeNotActiveError
ctx.get('RequestData')  # Error!

# With context - works
ctx.enter_request_context()
try:
    data = ctx.get('RequestData')
finally:
    ctx.exit_request_context()
```

## Error Handling

All exceptions are structured with diagnostic fields:

| Exception | When |
|-----------|------|
| `RegistryFrozenError` | Modification after freeze |
| `DependencyNotFoundError` | Missing dependency |
| `CircularDependencyError` | Circular reference detected |
| `ScopeNotActiveError` | Request scope without context |
| `ConditionNotMetError` | Condition check failed |
| `CreationError` | Factory execution failed |

### Dependency Chain

Circular dependency errors include stable, ordered chains:

```
CircularDependencyError: Circular dependency detected: ServiceA -> ServiceB -> ServiceC -> ServiceA
```

## Best Practices

1. **Always use `refresh()` before resolving**
2. **Use `try_get()` for optional dependencies**
3. **Enter request context before using request-scoped beans**
4. **Register shutdown handlers for cleanup**
5. **Use `eager=True` for critical services**

## Testing

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

def test_my_service():
    ctx = ApplicationContext()
    ctx.register(Definition(
        name='MockRepository',
        factory=lambda c: MockRepository(),
        scope=ScopeType.SINGLETON,
        source='test:MockRepository'
    ))
    ctx.register(Definition(
        name='MyService',
        factory=lambda c: MyService(c.get('MockRepository')),
        scope=ScopeType.SINGLETON,
        source='test:MyService'
    ))
    ctx.refresh()
    
    service = ctx.get('MyService')
    assert service is not None
```

## Related Documentation

- [Import Migration Guide](../import_migration_090.md)
- [API Reference](../api_reference.md)
- [Architecture Overview](architecture.md)
