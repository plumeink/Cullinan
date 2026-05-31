# Cullinan Dependency Injection Quick Reference

> **Version**: 0.93a4  
> **Author**: Plumeink

## Basic Usage

### 1. Define a Service

```python
from cullinan.service import service, Service

@service
class UserService(Service):
    def __init__(self):
        super().__init__()
        self.name = "UserService"
    
    def get_user(self, user_id):
        return {"id": user_id, "name": "John"}
```

### 2. Inject Service into Controller

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject, InjectByName, Lazy, Provider

@controller(url='/api')
class UserController:
    # Method 1: Type annotation (Recommended)
    user_service: UserService = Inject()
    
    # Method 2: Explicit name
    auth_service = InjectByName('AuthService')
    
    # Method 3: Optional dependency
    cache_service = InjectByName('CacheService', required=False)

    # Method 4: Lazy lookup
    report_service = Lazy('ReportService')
```

### 3. Use Injected Service

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject
from cullinan.params import Path

@controller(url='/api')
class UserController:
    user_service: UserService = Inject()
    
    @get_api(url='/users/{user_id}')
    async def get_user(self, user_id: int = Path()):
        user = self.user_service.get_user(user_id)
        return user
```

## Which injection primitive to use

| Case | Use |
| --- | --- |
| Type is importable at runtime | `Inject()` |
| `TYPE_CHECKING` / forward reference still maps to one unique target | `Inject()` |
| Type should not be imported at runtime | `InjectByName("Name")` |
| Lookup should happen on first access | `Lazy("Name")` |
| Optional dependency | `required=False` |
| Deferred provider object | `Provider[T] = Inject()` |
| Multiple implementations of one contract | `list[T] = Inject()` / `set[T] = Inject()` / `tuple[T, ...] = Inject()` |

## `TYPE_CHECKING` rule

`Inject()` now supports `TYPE_CHECKING` forward references when the binding result is unique:

```python
from typing import TYPE_CHECKING
from cullinan.core import Inject, Provider

if TYPE_CHECKING:
    from .contracts import Hook
    from .providers import DatabaseSessionProvider

class Repo:
    session_provider: Provider["DatabaseSessionProvider"] = Inject()
    hooks: list["Hook"] = Inject(required=False)
```

Startup still fails fast when:

- the annotation is ambiguous, such as `Union[A, B]` with multiple live candidates
- the combination is unsupported, such as `list[Union[A, B]]`
- the framework would need name guessing instead of exact resolution

## Packaging Configuration

### Using Explicit Registration (Recommended)

```python
from cullinan import configure
from my_app.service.user_service import UserService
from my_app.service.auth_service import AuthService
from my_app.controller.user_controller import UserController

# Configure before run()
configure(
    explicit_services=[
        UserService,
        AuthService,
    ],
    explicit_controllers=[
        UserController,
    ]
)

from cullinan.application import run
run()
```

### PyInstaller Configuration

```python
# your_app.spec
hiddenimports=[
    'my_app.service.user_service',
    'my_app.service.auth_service',
],
datas=[
    ('my_app', 'my_app'),
],
```

### Nuitka Configuration

```bash
nuitka --include-package=my_app \
       --include-module=my_app.service.user_service \
       your_app.py
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Dependency is None | Ensure service uses `@service` decorator |
| Service not found | Check service name matches (case-sensitive) |
| Circular dependency or runtime-only import edge | Use `InjectByName()` or `Lazy("Name")` |
| `DependencyTypeResolutionError` | Annotation is ambiguous, unsupported, or cannot be normalized safely; narrow the type contract or use `InjectByName()` |
| Injection not working | Ensure the component is registered with `@service` / `@controller` and available to `ApplicationContext` |

## See Also

- [Dependency Injection Guide](dependency_injection_guide.md) - Complete DI documentation
- [Architecture](architecture.md) - System architecture overview
- [Migration Guide](migration_guide.md) - Migration from older versions
