# Cullinan 2.0 Migration Guide

This guide helps you migrate from Cullinan 1.x to 2.0.

## Breaking Changes

### 1. Single Entry Point

**Before (1.x):**
```python
from cullinan.core import get_injection_registry, get_service_registry

registry = get_injection_registry()
registry.add_provider_source(my_source)
```

**After (2.0):**
```python
from cullinan.core.application_context import ApplicationContext
from cullinan.core.definitions import Definition, ScopeType

ctx = ApplicationContext()
ctx.register(Definition(
    name='MyService',
    factory=lambda c: MyService(),
    scope=ScopeType.SINGLETON,
    source='service:MyService'
))
ctx.refresh()
```

### 2. Registry Freeze

In 2.0, the registry is frozen after `refresh()`. Any attempt to register new dependencies will raise `RegistryFrozenError`.

**Before (1.x):**
```python
# Could register at any time
registry.register('NewService', NewService)
```

**After (2.0):**
```python
ctx = ApplicationContext()
ctx.register(...)  # OK before refresh
ctx.refresh()
ctx.register(...)  # RegistryFrozenError!
```

### 3. Scope Enforcement

Request-scoped dependencies now strictly require a `RequestContext`.

**Before (1.x):**
```python
# Might silently fail or return wrong instance
instance = registry.get('RequestScoped')
```

**After (2.0):**
```python
ctx.enter_request_context()
try:
    instance = ctx.get('RequestScoped')  # OK
finally:
    ctx.exit_request_context()

# Without context:
ctx.get('RequestScoped')  # ScopeNotActiveError!
```

### 4. Structured Exceptions

All exceptions now carry structured diagnostic fields.

**Before (1.x):**
```python
try:
    registry.resolve('Missing')
except Exception as e:
    print(str(e))  # Generic message
```

**After (2.0):**
```python
from cullinan.core.exceptions import DependencyNotFoundError

try:
    ctx.get('Missing')
except DependencyNotFoundError as e:
    print(e.dependency_name)      # 'Missing'
    print(e.resolution_path)      # ['ParentService', 'Missing']
    print(e.candidate_sources)    # [{'source': '...', 'reason': '...'}]
```

### 5. Circular Dependency Detection

Circular dependencies now produce stable, ordered chains.

**Before (1.x):**
```python
# Unordered, inconsistent output
CircularDependencyError: Circular dependency detected
```

**After (2.0):**
```python
# Stable, ordered chain
CircularDependencyError: Circular dependency detected: A -> B -> C -> A
```

## Migration Steps

### Step 1: Update Imports

```python
# Old imports (deprecated)
from cullinan.core import get_injection_registry, Inject, InjectByName

# New imports (2.0)
from cullinan.core.application_context import ApplicationContext
from cullinan.core.definitions import Definition, ScopeType
```

### Step 2: Convert Service Registration

```python
# Old style
@service
class UserService:
    user_repo = Inject()

# New style
ctx.register(Definition(
    name='UserService',
    factory=lambda c: UserService(user_repo=c.get('UserRepository')),
    scope=ScopeType.SINGLETON,
    source='service:UserService'
))
```

### Step 3: Update Application Startup

```python
# Old style (app.py)
from cullinan.app import CullinanApplication
app = CullinanApplication()
app.run()

# New style
from cullinan.core.application_context import ApplicationContext

ctx = ApplicationContext()
# ... register definitions ...
ctx.refresh()
# ... run tornado ...
ctx.shutdown()
```

### Step 4: Handle Request Scope

```python
# In request handler
class MyHandler(RequestHandler):
    def get(self):
        ctx.enter_request_context()
        try:
            service = ctx.get('RequestScopedService')
            # ... use service ...
        finally:
            ctx.exit_request_context()
```

## Deprecated APIs

The following APIs are deprecated in 2.0 and will be removed in 3.0:

| Deprecated API | Replacement |
|----------------|-------------|
| `get_injection_registry()` | `ApplicationContext` |
| `get_service_registry()` | `ApplicationContext.register()` |
| `@service` decorator with auto-inject | Explicit Definition registration |
| `Inject()` / `InjectByName()` | factory with `ctx.get()` |
| `DependencyInjector` | `ApplicationContext` |

## Compatibility Mode

During migration, you can enable compatibility mode (deprecated, will be removed):

```python
from cullinan.core.application_context import ApplicationContext

ctx = ApplicationContext()
ctx.set_strict_mode(False)  # Allow some legacy behaviors
```

**Warning:** Compatibility mode is for migration only. Always migrate to strict mode before production deployment.

## Testing Migration

Run all 2.0 tests to verify your migration:

```bash
python -m pytest tests/test_ioc_di_v2_*.py -v
```

## Getting Help

- [IoC/DI 2.0 Documentation](wiki/ioc_di_v2.md)
- [API Reference](api_reference.md)
- [GitHub Issues](https://github.com/your-repo/cullinan/issues)

