# Unified Registration System Migration Guide

## Overview

The Cullinan framework has been refactored to use a **unified registration system** based on `cullinan.core.Registry`. Both **services** and **controllers** now use this consistent pattern, abandoning their own separate registration logic.

## What Changed

### Before (Old System)

**Services:** Used their own `ServiceRegistry` with custom logic
**Controllers:** Used global lists like `controller_func_list` for method collection

### After (New System)

**Both services and controllers** now extend `cullinan.core.Registry`:
- `ServiceRegistry(Registry[Type[Service]])` - Manages service classes
- `ControllerRegistry(Registry[Type[Any]])` - Manages controller classes

## Architecture

```
cullinan.core.Registry (Base Pattern)
    ├── ServiceRegistry (Service Management)
    │   ├── Dependency injection support
    │   ├── Lifecycle management (on_init/on_destroy)
    │   └── Singleton instance caching
    │
    └── ControllerRegistry (Controller Management)
        ├── URL prefix management
        ├── Method registration (GET, POST, etc.)
        └── Handler servlet generation
```

## Key Benefits

1. **Consistency**: Single pattern for all registrations
2. **Maintainability**: Shared base implementation reduces code duplication
3. **Type Safety**: Generic typing with `Registry[T]`
4. **Testability**: Unified testing approach, easy to mock and reset
5. **Extensibility**: Easy to add new registry types

## API Reference

### ServiceRegistry

```python
from cullinan.service import ServiceRegistry, get_service_registry, service

# Get global registry
registry = get_service_registry()

# Register a service
@service
class EmailService(Service):
    def send_email(self, to, subject, body):
        print(f"Sending to {to}")

# Register with dependencies
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name):
        self.email.send_email(name, "Welcome", "Welcome!")

# Manual registration
registry.register('CustomService', CustomService, dependencies=['OtherService'])

# Get service instance
user_service = registry.get_instance('UserService')

# Initialize all services
registry.initialize_all()

# Cleanup
registry.destroy_all()
```

### ControllerRegistry

```python
from cullinan.controller import ControllerRegistry, get_controller_registry, controller, get_api

# Get global registry
registry = get_controller_registry()

# Register a controller using decorator
@controller(url='/api/users')
class UserController:
    @get_api('')
    def list_users(self):
        return {'users': []}
    
    @post_api('')
    def create_user(self, body_params):
        return {'created': True}

# Manual registration
registry.register('CustomController', CustomController, url_prefix='/api/custom')

# Register methods manually
registry.register_method('CustomController', '/items', 'get', handler_func)

# Get controller class
controller_class = registry.get('UserController')

# Get URL prefix
prefix = registry.get_url_prefix('UserController')

# Get all methods
methods = registry.get_methods('UserController')
```

## Core Registry Methods

All registries inherit these methods from `cullinan.core.Registry`:

```python
# Registration
registry.register(name, item, **metadata)

# Retrieval
item = registry.get(name)
all_items = registry.list_all()
metadata = registry.get_metadata(name)

# Checking
exists = registry.has(name)
count = registry.count()

# Management
registry.clear()  # Clear all items
```

## Migration Guide

### For Existing Code

**No changes required!** The new system is fully backward compatible.

All existing decorators and APIs work exactly as before:
- `@service` decorator
- `@controller` decorator  
- `@get_api`, `@post_api`, etc.
- `get_service_registry()`
- Service lifecycle hooks (`on_init`, `on_destroy`)

### For New Code

Use the unified registry pattern:

```python
# Services
from cullinan.service import get_service_registry

registry = get_service_registry()
registry.register('MyService', MyService)

# Controllers
from cullinan.controller import get_controller_registry

registry = get_controller_registry()
registry.register('MyController', MyController, url_prefix='/api')
```

## Implementation Details

### Controller Registration Flow

1. **Decorator Application**: `@controller(url='/api')` is applied to class
2. **Context Setup**: Context variable created to collect methods
3. **Method Collection**: Method decorators (`@get_api`, etc.) add to context
4. **Registry Registration**: 
   - Controller class registered in `ControllerRegistry`
   - Methods registered via `register_method()`
   - Handlers created and registered in `HandlerRegistry`

### Service Registration Flow

1. **Decorator Application**: `@service` or `@service(dependencies=[...])` applied
2. **Registry Registration**: Service class registered in `ServiceRegistry`
3. **Dependency Tracking**: Dependencies stored in metadata
4. **Lazy Instantiation**: Instances created on first access via `get_instance()`
5. **Lifecycle Management**: `on_init()` called after dependency injection

## Testing

### Reset Registries Between Tests

```python
from cullinan.service import reset_service_registry
from cullinan.controller import reset_controller_registry

def setUp(self):
    reset_service_registry()
    reset_controller_registry()
```

### Verify Registration

```python
from cullinan.service import get_service_registry
from cullinan.controller import get_controller_registry

service_registry = get_service_registry()
controller_registry = get_controller_registry()

# Check registration
assert service_registry.has('MyService')
assert controller_registry.has('MyController')

# Check counts
assert service_registry.count() == 1
assert controller_registry.count() == 1
```

### Test Inheritance

```python
from cullinan.core import Registry
from cullinan.service import ServiceRegistry
from cullinan.controller import ControllerRegistry

# Verify they extend core.Registry
assert isinstance(get_service_registry(), Registry)
assert isinstance(get_controller_registry(), Registry)
```

## File Structure

```
cullinan/
├── core/
│   ├── registry.py          # Base Registry pattern
│   ├── injection.py         # Dependency injection
│   └── lifecycle.py         # Lifecycle management
│
├── service/
│   ├── registry.py          # ServiceRegistry(Registry)
│   ├── decorators.py        # @service decorator
│   └── base.py              # Service base class
│
├── controller/
│   ├── __init__.py          # Re-exports from controller.py
│   └── registry.py          # ControllerRegistry(Registry)
│
└── controller.py            # Controller decorators & utilities
```

## Advanced Usage

### Custom Registry

Create your own registry by extending `Registry`:

```python
from cullinan.core import Registry
from typing import Type

class MiddlewareRegistry(Registry[Type[Middleware]]):
    def register(self, name: str, middleware_class: Type[Middleware], 
                 priority: int = 0, **metadata):
        self._validate_name(name)
        self._items[name] = middleware_class
        meta = metadata.copy()
        meta['priority'] = priority
        self._metadata[name] = meta
    
    def get_by_priority(self):
        items = []
        for name, cls in self._items.items():
            priority = self._metadata.get(name, {}).get('priority', 0)
            items.append((priority, name, cls))
        return sorted(items, key=lambda x: x[0])
```

### Accessing Registry Internals

```python
# Get all items (dict copy)
all_services = service_registry.list_all()

# Get metadata
meta = service_registry.get_metadata('MyService')
dependencies = meta.get('dependencies', [])

# Check instances
instances = service_registry.list_instances()
has_instance = service_registry.has_instance('MyService')
```

## Troubleshooting

### ImportError: cannot import ControllerRegistry

Make sure you're importing from the correct location:

```python
# Correct
from cullinan.controller import ControllerRegistry, get_controller_registry

# Also correct (package re-exports)
from cullinan import get_controller_registry
```

### Controller decorator not working

The `@controller` decorator requires method decorators to be applied first:

```python
@controller(url='/api')
class MyController:
    @get_api('/items')  # Method decorator BEFORE controller decorator
    def list_items(self):
        return []
```

### Service dependencies not resolving

Ensure services are registered before initialization:

```python
# Register all services first
@service
class ServiceA(Service):
    pass

@service(dependencies=['ServiceA'])
class ServiceB(Service):
    pass

# Then initialize
get_service_registry().initialize_all()
```

## Performance Notes

- **Registration**: O(1) for both service and controller registration
- **Lookup**: O(1) for get operations (hash-based)
- **Sorting**: Handler sorting is O(n log n) where n = number of handlers
- **Memory**: Registries use dictionaries for efficient storage

## Future Enhancements

Planned improvements leveraging the unified registry:
- Cross-registry dependency injection
- Registry middleware hooks
- Registry events/observers
- Distributed registry support
- Registry serialization/deserialization

## See Also

- [Core Module Documentation](./CORE_MODULE.md)
- [Service Layer Guide](./SERVICE_GUIDE.md)
- [Controller Guide](./CONTROLLER_GUIDE.md)
- [Architecture Overview](./ARCHITECTURE_MASTER.md)

