title: "IoC & DI (Injection)"
slug: "injection"
module: ["cullinan.core"]
tags: ["ioc", "di", "injection"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/wiki/injection.md"
related_tests: ["tests/test_core_injection.py"]
related_examples: ["examples/ioc_facade_demo.py"]
estimate_pd: 2.0
last_updated: "2025-12-26T00:00:00Z"
pr_links: []

# IoC & DI (Injection)

> **Version**: v0.90  
> **Author**: Plumeink

This page documents the IoC (Inversion of Control) and DI (Dependency Injection) system used by Cullinan. For the complete architecture overview, see [Architecture](../architecture.md). For migration from previous versions, see [Migration Guide](../migration_guide.md).

## Key Concepts

### Inversion of Control (IoC)

IoC is a design principle where the control of object creation and lifecycle is transferred from the application code to a framework or container.

### Dependency Injection (DI)

DI is a technique for achieving IoC. Dependencies are "injected" into a class rather than being created by the class itself.

## Recommended Usage (Decorator-Based)

### 1. Define a Service

```python
from cullinan.service import service, Service

@service
class DatabaseService(Service):
    def __init__(self):
        super().__init__()
        self.connection = None
    
    def on_init(self):
        """Called during service initialization"""
        self.connection = create_connection()
    
    def on_shutdown(self):
        """Called during service shutdown"""
        if self.connection:
            self.connection.close()
    
    def query(self, sql: str):
        return self.connection.execute(sql)
```

### 2. Inject Dependencies

```python
from cullinan.service import service, Service
from cullinan.core import Inject

@service
class UserService(Service):
    # Automatic injection via type annotation
    database: DatabaseService = Inject()
    
    def get_user(self, user_id: int):
        return self.database.query(f"SELECT * FROM users WHERE id={user_id}")
```

### 3. Use in Controllers

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject
from cullinan.params import Path

@controller(url='/api/users')
class UserController:
    user_service: UserService = Inject()
    
    @get_api(url='/{user_id}')
    async def get_user(self, user_id: Path(int)):
        return self.user_service.get_user(user_id)
```

## Injection Methods

### Inject() - Type Annotation Injection (Recommended)

Best IDE support and type safety.

```python
from cullinan.core import Inject

@service
class MyService(Service):
    # Infers dependency name from type annotation
    database: DatabaseService = Inject()
    
    # Optional dependency
    cache: CacheService = Inject(required=False)
```

### InjectByName() - String Name Injection

No need to import dependency classes, avoids circular imports.

```python
from cullinan.controller import controller
from cullinan.core import InjectByName

@controller(url='/api')
class MyController:
    # Explicit name
    user_service = InjectByName('UserService')
    
    # Auto-infer name (snake_case -> PascalCase)
    email_service = InjectByName()  # -> EmailService
```

## Lifecycle Hooks

Services support lifecycle hooks for initialization and cleanup:

```python
@service
class MyService(Service):
    def get_phase(self) -> int:
        """Initialization order (lower = earlier)"""
        return 0
    
    def on_init(self):
        """Called after all services are registered"""
        pass
    
    def on_startup(self):
        """Called before the server starts accepting requests"""
        pass
    
    def on_shutdown(self):
        """Called when the server is shutting down"""
        pass
```

## Advanced: ApplicationContext (For Complex Scenarios)

For advanced use cases like third-party integration or custom factories:

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

ctx = ApplicationContext()

ctx.register(Definition(
    name='CustomService',
    factory=lambda c: CustomService(c.get('Dependency')),
    scope=ScopeType.SINGLETON,
    source='custom:CustomService'
))

ctx.refresh()  # Freeze registry
service = ctx.get('CustomService')
```

## Best Practices

1. **Use decorators for services and controllers** - Let the framework handle registration
2. **Use `Inject()` for type-safe injection** - Better IDE support and refactoring
3. **Use `InjectByName()` to avoid circular imports** - When you can't import the type
4. **Implement lifecycle hooks properly** - Clean initialization and shutdown
5. **Keep services focused** - Single responsibility principle

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Dependency is None | Ensure the service is decorated with `@service` |
| Service not found | Check the service name matches (case-sensitive) |
| Circular dependency | Use `InjectByName()` with lazy resolution |
| Injection not working | Ensure the class extends `Service` or `Controller` |

## See Also

- [Architecture](../architecture.md) - System architecture overview
- [Decorators](decorators.md) - All available decorators
- [Lifecycle](lifecycle.md) - Service lifecycle management
- [Migration Guide](../migration_guide.md) - Migrating from older versions
