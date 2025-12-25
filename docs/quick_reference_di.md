# Cullinan Dependency Injection Quick Reference

> **Version**: v0.90  
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
from cullinan.core import Inject, InjectByName

@controller(url='/api')
class UserController:
    # Method 1: Type annotation (Recommended)
    user_service: UserService = Inject()
    
    # Method 2: Explicit name
    auth_service = InjectByName('AuthService')
    
    # Method 3: Optional dependency
    cache_service = InjectByName('CacheService', required=False)
```

### 3. Use Injected Service

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject

@controller(url='/api')
class UserController:
    user_service: UserService = Inject()
    
    @get_api(url='/users/<user_id>')
    async def get_user(self, url_param):
        user_id = url_param.get('user_id')
        user = self.user_service.get_user(user_id)
        return user
```

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
| Circular dependency | Use `InjectByName()` for lazy resolution |
| Injection not working | Ensure class extends `Service` or `Controller` |

## See Also

- [Dependency Injection Guide](dependency_injection_guide.md) - Complete DI documentation
- [Architecture](architecture.md) - System architecture overview
- [Migration Guide](migration_guide.md) - Migration from older versions
