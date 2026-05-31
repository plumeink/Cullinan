# Cullinan Dependency Injection Guide

> **Version**: 0.93a3  
> **Last Updated**: 2026-05-31  
> **Status**: Updated

## Overview

Cullinan's current DI model is centered on `ApplicationContext` and exposed publicly through `cullinan.core`. Decorators remain the recommended authoring surface, while legacy registry-style APIs are kept only for compatibility.

## Recommended usage

### 1. Register services with decorators

```python
from cullinan.core import Inject
from cullinan.service import service

@service
class DatabaseService:
    def query(self, sql: str):
        return {"sql": sql}

@service
class UserService:
    database: DatabaseService = Inject()

    def get_user(self, user_id: int):
        return self.database.query(f"select * from users where id = {user_id}")
```

### 2. Use the same injection model in controllers

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject
from cullinan.params import Path

@controller(url="/users")
class UserController:
    user_service: UserService = Inject()

    @get_api(url="/{user_id}")
    async def get_user(self, user_id: int = Path()):
        return self.user_service.get_user(user_id)
```

## Injection primitives

### `Inject()` — preferred

Use `Inject()` when you want type-driven resolution and better refactoring support.

```python
class AuditService:
    repo: Repository = Inject()
    cache: CacheService = Inject(required=False)
```

### `InjectByName()` — name-based fallback

Use `InjectByName()` when the dependency is more naturally resolved by name or when importing the type would create an undesirable dependency edge.

```python
from cullinan.core import InjectByName

class ReportController:
    report_service = InjectByName("ReportService")
```

## ApplicationContext as the single container entrypoint

Decorator-based registration covers most application code. For advanced integration, use `ApplicationContext` directly.

```python
from cullinan.core import ApplicationContext, Definition, ScopeType

ctx = ApplicationContext()
ctx.register(Definition(
    name="CustomService",
    factory=lambda c: CustomService(),
    scope=ScopeType.SINGLETON,
    source="custom:CustomService",
))
ctx.refresh()
service = ctx.get("CustomService")
```

`cullinan.core.container.*` paths are compatibility forwards to the same public container API.

## Lifecycle integration

DI and lifecycle are part of the same runtime model. Managed components can implement:

- `on_post_construct()`
- `on_startup()`
- `on_shutdown()`
- `on_pre_destroy()`

Async variants with `_async` are also supported. Use `get_phase()` if startup/shutdown ordering matters.

## Compatibility notes

Cullinan still exports some legacy names, but they should not be used as the primary programming model:

- `injectable` is currently a **no-op compatibility decorator**
- `inject_constructor` is currently a **no-op compatibility decorator**
- `get_injection_registry()` currently returns `None`
- `reset_injection_registry()` is a safe compatibility no-op

Those names are kept so older code paths fail less abruptly, but new code should rely on `@service`, `@controller`, `Inject`, `InjectByName`, and `ApplicationContext`.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Dependency cannot be resolved | Confirm the type or dependency name matches the registered component |
| Optional dependency is missing | Use `required=False` and handle `None` explicitly |
| Lifecycle hooks do not run | Ensure the component is managed and `ApplicationContext.refresh()` has executed |
| Advanced registration behaves differently than expected | Verify the `Definition` scope and factory source |

## Related documents

- [Architecture](architecture.md)
- [Runtime consolidation overview](runtime_updates_v093.md)
- [IoC & DI wiki](wiki/injection.md)
- [Application Lifecycle](wiki/lifecycle.md)
