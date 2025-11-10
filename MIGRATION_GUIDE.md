# Migration Guide: Enhanced Service Layer

## Overview

This guide helps you migrate from the basic service layer to the enhanced service layer with dependency injection and lifecycle management.

## Key Points

✅ **100% Backward Compatible** - All existing code continues to work  
✅ **Opt-in Enhancement** - Use new features only when you need them  
✅ **No Breaking Changes** - Existing `@service` decorator still works  

## What's New?

### Core Module (`cullinan.core`)
- Base Registry pattern for all registries
- Dependency injection engine
- Lifecycle management (on_init, on_destroy)
- Type-safe exception hierarchy

### Enhanced Service Layer (`cullinan.service_new`)
- Service base class with lifecycle hooks
- ServiceRegistry with dependency injection
- Enhanced @service decorator with dependencies parameter
- Singleton instance management

### Testing Utilities (`cullinan.testing`)
- MockService for easy test mocking
- TestRegistry for isolated testing
- ServiceTestCase and IsolatedServiceTestCase fixtures

## Migration Paths

### Path 1: No Migration Needed (Keep Using Basic Services)

If your services are simple and don't need dependency injection, **no changes are required**.

```python
# Old code (still works perfectly)
from cullinan.service import service, Service

@service
class EmailService(Service):
    def send_email(self, to, subject, body):
        print(f"Sending to {to}: {subject}")
```

### Path 2: Gradual Migration (Add Enhanced Features)

Migrate service-by-service, adding new features only where beneficial.

#### Step 1: Import from new module

```python
# Before
from cullinan.service import service, Service

# After
from cullinan.service_new import service, Service
```

#### Step 2: Add dependencies (optional)

```python
# Before - manual dependency management
@service
class UserService(Service):
    def create_user(self, name):
        email_service = service_list.get('EmailService')
        email_service.send_email(name, "Welcome", "Welcome!")

# After - automatic dependency injection
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name):
        self.email.send_email(name, "Welcome", "Welcome!")
```

#### Step 3: Add lifecycle hooks (optional)

```python
@service
class DatabaseService(Service):
    def on_init(self):
        """Called after service is created"""
        self.connection = self.connect_to_database()
    
    def on_destroy(self):
        """Called when service is being shut down"""
        self.connection.close()
    
    def connect_to_database(self):
        return "DB_CONNECTION"
```

### Path 3: Full Migration (Use All Features)

For new projects or major refactoring, use all enhanced features.

```python
from cullinan.service_new import service, Service, get_service_registry

# Define services with dependencies
@service
class LogService(Service):
    def log(self, msg):
        print(f"[LOG] {msg}")

@service(dependencies=['LogService'])
class CacheService(Service):
    def on_init(self):
        self.log = self.dependencies['LogService']
        self.cache = {}
        self.log.log("Cache initialized")

@service(dependencies=['CacheService', 'LogService'])
class UserService(Service):
    def on_init(self):
        self.cache = self.dependencies['CacheService']
        self.log = self.dependencies['LogService']
    
    def get_user(self, user_id):
        self.log.log(f"Getting user {user_id}")
        # ... implementation

# Initialize all services
registry = get_service_registry()
registry.initialize_all()

# Use services
user_svc = registry.get_instance('UserService')
user = user_svc.get_user(123)

# Cleanup on shutdown
registry.destroy_all()
```

## Testing Migration

### Before (Manual Mocking)

```python
# Test without isolation
class TestUserService(unittest.TestCase):
    def test_create_user(self):
        # Hard to isolate from other services
        user_svc = service_list.get('UserService')
        result = user_svc.create_user('John')
        # ...
```

### After (Isolated Testing)

```python
from cullinan.testing import MockService, IsolatedServiceTestCase

class MockEmailService(MockService):
    def send_email(self, to, subject, body):
        self.record_call('send_email', to=to, subject=subject, body=body)
        return True

class TestUserService(IsolatedServiceTestCase):
    def test_create_user(self):
        # Use isolated registry
        self.registry.register('EmailService', MockEmailService)
        self.registry.register('UserService', UserService, dependencies=['EmailService'])
        self.registry.initialize_all()
        
        user_svc = self.registry.get_instance('UserService')
        result = user_svc.create_user('John')
        
        # Verify mock was called
        email_mock = self.registry.get_instance('EmailService')
        self.assertTrue(email_mock.was_called('send_email'))
```

## Common Patterns

### Pattern 1: Database Service with Connection Pool

```python
@service
class DatabaseService(Service):
    def on_init(self):
        self.pool = self.create_connection_pool()
    
    def on_destroy(self):
        self.pool.close_all()
    
    def query(self, sql):
        with self.pool.get_connection() as conn:
            return conn.execute(sql)
```

### Pattern 2: Service with Multiple Dependencies

```python
@service(dependencies=['DatabaseService', 'CacheService', 'LogService'])
class ProductService(Service):
    def on_init(self):
        self.db = self.dependencies['DatabaseService']
        self.cache = self.dependencies['CacheService']
        self.log = self.dependencies['LogService']
    
    def get_product(self, product_id):
        # Try cache first
        cached = self.cache.get(f'product:{product_id}')
        if cached:
            return cached
        
        # Fetch from database
        product = self.db.query(f"SELECT * FROM products WHERE id={product_id}")
        self.cache.set(f'product:{product_id}', product)
        
        return product
```

### Pattern 3: Async Service (Future Enhancement)

```python
@service
class AsyncEmailService(Service):
    async def on_init(self):
        # Async initialization
        await self.connect()
    
    async def on_destroy(self):
        # Async cleanup
        await self.disconnect()
```

## FAQ

### Q: Do I need to migrate my existing services?

**A:** No. Existing services continue to work. Migrate only when you need new features.

### Q: Can I mix old and new styles?

**A:** Yes. You can have some services using `cullinan.service` and others using `cullinan.service_new`.

### Q: What happens to the old service.py?

**A:** It remains unchanged and fully supported. The new module is `service_new`.

### Q: How do I initialize services?

**A:** Call `registry.initialize_all()` once during application startup.

```python
from cullinan.service_new import get_service_registry

# During app startup
registry = get_service_registry()
registry.initialize_all()

# During app shutdown
registry.destroy_all()
```

### Q: Can services depend on services from the old module?

**A:** It's not recommended. Stick to one module per application for consistency.

### Q: What about performance?

**A:** Overhead is minimal (<1ms per request). Dependency resolution is cached.

### Q: How do I debug dependency issues?

**A:** Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Circular dependencies will be detected and reported with clear error messages.

## Troubleshooting

### Issue: "Circular dependency detected"

**Solution:** Review your dependency graph. Services cannot depend on each other in a cycle.

```python
# Bad - Circular dependency
@service(dependencies=['ServiceB'])
class ServiceA(Service): pass

@service(dependencies=['ServiceA'])
class ServiceB(Service): pass

# Good - Linear dependencies
@service
class ServiceA(Service): pass

@service(dependencies=['ServiceA'])
class ServiceB(Service): pass
```

### Issue: "Dependency not found"

**Solution:** Ensure all dependencies are registered before calling `initialize_all()`.

```python
# Make sure all services are decorated with @service before initializing
@service
class ServiceA(Service): pass

@service(dependencies=['ServiceA'])  # ServiceA must be registered first
class ServiceB(Service): pass
```

### Issue: Tests interfering with each other

**Solution:** Use `IsolatedServiceTestCase` or reset the registry between tests.

```python
from cullinan.testing import IsolatedServiceTestCase

class TestMyService(IsolatedServiceTestCase):
    # Each test gets a fresh, isolated registry
    def test_something(self):
        self.registry.register('MyService', MyService)
        # ...
```

## Next Steps

1. **Read the examples**: Check `examples/service_examples.py`
2. **Review documentation**: See `next_docs/` for detailed design docs
3. **Start small**: Try the enhanced decorator on one service
4. **Add tests**: Use MockService for easy testing
5. **Expand gradually**: Migrate more services as needed

## Support

- **Issues**: https://github.com/plumeink/Cullinan/issues
- **Wiki**: https://github.com/plumeink/Cullinan/wiki
- **Examples**: `examples/service_examples.py`
