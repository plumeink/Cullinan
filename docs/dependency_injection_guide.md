# Cullinan Dependency Injection Guide

> **Version**: 0.93a4  
> **Last Updated**: 2026-06-01  
> **Status**: Updated

## Overview

Cullinan's current DI model is centered on `ApplicationContext` and exposed publicly through `cullinan.core`. Decorators remain the recommended authoring surface, while legacy registry-style APIs are kept only for compatibility.

Before choosing an injection primitive, read [Framework Semantics](framework_semantics.md). That page defines the hard rules behind `Inject()`, `InjectByName()`, `refresh()`, and compatibility APIs.

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

`Inject()` now uses a strict, typed resolution pipeline:

- direct runtime types still work as before
- `TYPE_CHECKING` + forward references are supported when Cullinan can map the annotation to a **single** registered target
- common wrappers such as `Optional[T]`, `Annotated[T, ...]`, `Final[T]`, `Provider[T]`, `list[T]`, `set[T]`, `tuple[T, ...]`, and `Union[A, B]` are supported
- Cullinan still refuses attribute-name guesses such as `session_provider -> SessionProvider`
- if the annotation is ambiguous or cannot be normalized safely, startup fails with `DependencyTypeResolutionError`

Use it when you want typed wiring and the annotation can be normalized into a unique dependency contract.

### `InjectByName()` — name-based fallback

Use `InjectByName()` when the dependency is more naturally resolved by name or when importing the type would create an undesirable dependency edge.

```python
from cullinan.core import InjectByName

class ReportController:
    report_service = InjectByName("ReportService")
```

Cullinan now treats `InjectByName("ExactComponentName")` as the recommended form. `InjectByName()` without an explicit name is kept only as a compatibility fallback and now emits a warning.

This is the correct choice when you intentionally do **not** want to import the target type at runtime.

### `Lazy()` — deferred lookup

Use `Lazy()` when the dependency should be resolved on first access rather than during eager instance wiring.

```python
from cullinan.core import Lazy

class AuditService:
    report_service = Lazy("ReportService")
```

`Lazy()` follows the same naming rules as `Inject()` / `InjectByName()`:

- prefer an explicit name when you want late lookup without importing the target type
- if you rely on type-driven resolution, the type still needs to be resolvable at runtime

## How to choose

| Need | Recommended primitive |
| --- | --- |
| Runtime type is available and you want refactor-friendly injection | `Inject()` |
| `TYPE_CHECKING` / forward-reference type is unique and still should be type-driven | `Inject()` |
| Runtime type is intentionally unavailable or awkward to import | `InjectByName("Name")` |
| Lookup should be deferred until first use | `Lazy("Name")` or `Lazy()` with a runtime-resolvable type |
| Optional dependency | `Inject(required=False)` or `InjectByName("Name", required=False)` |
| Deferred provider object | `Inject()` with `Provider[T]` |
| Multiple implementations of one contract | `Inject()` with `list[T]`, `set[T]`, or `tuple[T, ...]` |

## `TYPE_CHECKING` and forward-reference rules

`Inject()` can now work with `TYPE_CHECKING` and forward references, but only when the final binding is still uniquely decidable.

### Supported: single target forward reference

```python
from typing import TYPE_CHECKING

from cullinan.core import Inject
from cullinan.service import service

if TYPE_CHECKING:
    from .providers import DatabaseSessionProvider

@service
class ChannelBindingRepository:
    session_provider: "DatabaseSessionProvider" = Inject()
```

As long as `DatabaseSessionProvider` is the only matching registered component, startup succeeds.

### Supported wrappers

```python
from typing import TYPE_CHECKING, Optional

from cullinan.core import Inject, Provider
from cullinan.service import service

if TYPE_CHECKING:
    from .contracts import Hook
    from .providers import DatabaseSessionProvider, PrimarySessionProvider, SecondarySessionProvider

@service
class ChannelBindingRepository:
    session_provider: Provider["DatabaseSessionProvider"] = Inject()
    hooks: list["Hook"] = Inject(required=False)
    fallback_cache: Optional["CacheService"] = Inject()
    preferred_provider: "PrimarySessionProvider | SecondarySessionProvider" = Inject()
```

Rules:

- `Optional[T]` allows `None` when `T` is missing
- `Provider[T]` injects a deferred provider object instead of `T` directly
- collection wrappers inject all matching implementations
- `Union[A, B]` works only when exactly one branch is bindable

### Still rejected: ambiguous or unsupported combinations

- multiple `Union` branches are available at the same time
- nested combinations such as `list[Union[A, B]]`
- anything that would require fuzzy guessing or attribute-name fallback

Use `InjectByName("Name")` or `Lazy("Name")` when you intentionally want explicit, name-based control.

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
| `DependencyTypeResolutionError` on startup | The annotation is ambiguous, unsupported, or cannot be normalized safely; narrow the type contract or switch to `InjectByName()` / `Lazy("Name")` |
| Optional dependency is missing | Use `required=False` and handle `None` explicitly |
| Lifecycle hooks do not run | Ensure the component is managed and `ApplicationContext.refresh()` has executed |
| Advanced registration behaves differently than expected | Verify the `Definition` scope and factory source |

## Related documents

- [Architecture](architecture.md)
- [Runtime consolidation overview](runtime_updates_v093.md)
- [IoC & DI wiki](wiki/injection.md)
- [Application Lifecycle](wiki/lifecycle.md)
