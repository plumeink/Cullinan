# Unified Registration Quick Reference

## For Service Registration

### Using Decorator (Recommended)
```python
from cullinan.service import service, Service

@service
class MyService(Service):
    def my_method(self):
        return "result"

# With dependencies
@service(dependencies=['OtherService'])
class MyService(Service):
    def on_init(self):
        self.other = self.dependencies['OtherService']
```

### Manual Registration
```python
from cullinan.service import get_service_registry

registry = get_service_registry()
registry.register('MyService', MyService, dependencies=['OtherService'])
```

### Common Operations
```python
# Check if registered
registry.has('MyService')  # -> bool

# Get service class
service_class = registry.get('MyService')  # -> Type[Service]

# Get service instance (lazy)
service_instance = registry.get_instance('MyService')  # -> Service

# Initialize all services
registry.initialize_all()

# Destroy all services
registry.destroy_all()

# Clear registry (testing)
registry.clear()

# Count services
count = registry.count()  # -> int
```

## For Controller Registration

### Using Decorator (Recommended)
```python
from cullinan.controller import controller, get_api, post_api

@controller(url='/api/users')
class UserController:
    @get_api('')
    def list_users(self):
        return {'users': []}
    
    @post_api('')
    def create_user(self, body_params):
        return {'created': True}
```

### Manual Registration
```python
from cullinan.controller import get_controller_registry

registry = get_controller_registry()

# Register controller
registry.register('MyController', MyController, url_prefix='/api')

# Register method
registry.register_method('MyController', '/items', 'get', handler_func)
```

### Common Operations
```python
# Check if registered
registry.has('MyController')  # -> bool

# Get controller class
controller_class = registry.get('MyController')  # -> Type

# Get URL prefix
prefix = registry.get_url_prefix('MyController')  # -> str

# Get all methods
methods = registry.get_methods('MyController')  # -> List[Tuple]

# Clear registry (testing)
registry.clear()

# Count controllers
count = registry.count()  # -> int
```

## Testing

### Reset Registries
```python
from cullinan.service import reset_service_registry
from cullinan.controller import reset_controller_registry

def setUp(self):
    reset_service_registry()
    reset_controller_registry()
```

### Verify Registration
```python
from cullinan.core import Registry

# Check inheritance
assert isinstance(get_service_registry(), Registry)
assert isinstance(get_controller_registry(), Registry)

# Check registration
assert get_service_registry().has('MyService')
assert get_controller_registry().has('MyController')
```

## Core Registry Methods (Available on All Registries)

```python
# Registration
registry.register(name: str, item: T, **metadata)

# Retrieval
item = registry.get(name: str) -> Optional[T]
all_items = registry.list_all() -> Dict[str, T]
metadata = registry.get_metadata(name: str) -> Optional[Dict]

# Checking
exists = registry.has(name: str) -> bool
count = registry.count() -> int

# Management  
registry.clear() -> None
```

## Import Cheatsheet

```python
# Core
from cullinan.core import Registry

# Services
from cullinan.service import (
    Service,
    service,
    ServiceRegistry,
    get_service_registry,
    reset_service_registry
)

# Controllers
from cullinan.controller import (
    controller,
    get_api, post_api, put_api, patch_api, delete_api,
    ControllerRegistry,
    get_controller_registry,
    reset_controller_registry,
    HeaderRegistry,
    get_header_registry
)
```

## Key Principles

1. **Single Source of Truth**: All registration goes through `cullinan.core.Registry`
2. **Type Safety**: Registries are generic `Registry[T]`
3. **Thread Safe**: Context variables, no global mutable state
4. **Backward Compatible**: All existing APIs work unchanged
5. **Testable**: Easy to reset and mock registries

