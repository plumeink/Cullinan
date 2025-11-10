# Migration Guide

## Executive Summary

This guide helps developers migrate from Cullinan's current service layer to the enhanced version with dependency injection and lifecycle management. **Good news: Migration is optional!** Your existing code will continue to work without changes.

## 1. Migration Philosophy

### 1.1 Backward Compatibility Guarantee

**Your existing code will NOT break.** The enhancements are additive and opt-in.

```python
# This code STILL WORKS in v0.8+
@service
class UserService(Service):
    def create_user(self, name):
        return {'name': name}

# Controllers still work
@controller(url='/api')
class UserController:
    @post_api(url='/users')
    def create_user(self, body_params):
        user = self.service['UserService'].create_user(body_params['name'])
        return self.response_build(status=201, data=user)
```

### 1.2 Progressive Enhancement

You can migrate **service by service** at your own pace.

**Strategy**:
1. Keep existing services as-is
2. Add new services with DI
3. Gradually migrate old services
4. No "all or nothing" migration required

## 2. What's New?

### 2.1 Dependency Injection

**Before** (manual dependency lookup):
```python
@service
class OrderService(Service):
    def process_order(self, order_data):
        # Manual lookup - error prone
        email_service = service_list.get('EmailService')
        payment_service = service_list.get('PaymentService')
        
        if email_service:
            email_service.send(...)
```

**After** (automatic dependency injection):
```python
@service(dependencies=['EmailService', 'PaymentService'])
class OrderService(Service):
    def on_init(self):
        # Dependencies automatically injected
        self.email = self.dependencies['EmailService']
        self.payment = self.dependencies['PaymentService']
    
    def process_order(self, order_data):
        # Direct use - cleaner and safer
        self.email.send(...)
        self.payment.charge(...)
```

### 2.2 Lifecycle Hooks

**Before** (no initialization control):
```python
@service
class DatabaseService(Service):
    def __init__(self):
        # When is this called? Uncertain!
        # self.pool = create_pool()  # Risky!
        pass
```

**After** (controlled initialization):
```python
@service
class DatabaseService(Service):
    def on_init(self):
        # Called once at startup - guaranteed!
        self.pool = create_connection_pool()
        logger.info("Database pool created")
    
    def on_destroy(self):
        # Called at shutdown - cleanup!
        self.pool.close()
        logger.info("Database pool closed")
```

### 2.3 Better Testing

**Before** (global state pollution):
```python
def test_user_service():
    # Pollutes global service_list
    original = service_list.get('EmailService')
    service_list['EmailService'] = MockEmailService()
    
    try:
        # Test code
        pass
    finally:
        # Must remember to cleanup
        service_list['EmailService'] = original
```

**After** (isolated test registry):
```python
from cullinan.testing import TestRegistry, MockService

def test_user_service():
    # Clean isolated registry
    registry = TestRegistry()
    registry.register_mock('EmailService', MockEmailService())
    registry.register('UserService', UserService, dependencies=['EmailService'])
    
    # Test with injected mock
    service = registry.get('UserService')
    service.create_user('John', 'john@example.com')
    
    # Easy assertions
    mock = registry.get_mock('EmailService')
    assert mock.was_called('send')
```

## 3. Migration Scenarios

### 3.1 Scenario 1: Simple Service (No Dependencies)

**Current Code**:
```python
@service
class LogService(Service):
    def log(self, message):
        print(f"LOG: {message}")
```

**Migration Decision**: **No migration needed!** This code works perfectly.

**Optional Enhancement** (add lifecycle hooks):
```python
@service
class LogService(Service):
    def on_init(self):
        # Initialize log file
        self.log_file = open('app.log', 'a')
    
    def on_destroy(self):
        # Close log file on shutdown
        self.log_file.close()
    
    def log(self, message):
        self.log_file.write(f"{message}\n")
        self.log_file.flush()
```

### 3.2 Scenario 2: Service with Manual Dependencies

**Current Code**:
```python
@service
class EmailService(Service):
    def send(self, to, subject, body):
        # Email sending logic
        pass

@service
class UserService(Service):
    def create_user(self, name, email):
        # Manual dependency lookup
        email_svc = service_list['EmailService']
        
        user = {'name': name, 'email': email}
        email_svc.send(email, 'Welcome', f'Hello {name}!')
        return user
```

**Migration Steps**:

**Step 1**: Add dependency declaration
```python
@service
class EmailService(Service):
    def send(self, to, subject, body):
        pass  # No changes needed

@service(dependencies=['EmailService'])  # <- Add this
class UserService(Service):
    def create_user(self, name, email):
        # Still using manual lookup (works)
        email_svc = service_list['EmailService']
        user = {'name': name, 'email': email}
        email_svc.send(email, 'Welcome', f'Hello {name}!')
        return user
```

**Step 2**: Use dependency injection
```python
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):  # <- Add lifecycle hook
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name, email):
        # Use injected dependency
        user = {'name': name, 'email': email}
        self.email.send(email, 'Welcome', f'Hello {name}!')
        return user
```

### 3.3 Scenario 3: Service with Multiple Dependencies

**Current Code**:
```python
@service
class OrderService(Service):
    def process_order(self, order_data):
        email = service_list['EmailService']
        payment = service_list['PaymentService']
        inventory = service_list['InventoryService']
        
        # Order processing logic
```

**Migration**:
```python
@service(dependencies=['EmailService', 'PaymentService', 'InventoryService'])
class OrderService(Service):
    def on_init(self):
        # Clean initialization
        self.email = self.dependencies['EmailService']
        self.payment = self.dependencies['PaymentService']
        self.inventory = self.dependencies['InventoryService']
    
    def process_order(self, order_data):
        # Use injected dependencies
        # Same logic, cleaner code
```

### 3.4 Scenario 4: Service with Resource Management

**Current Code**:
```python
@service
class DatabaseService(Service):
    def __init__(self):
        # Unclear when this runs
        # Connection might not be ready
        pass
    
    def query(self, sql):
        # How to manage connection pool?
        pass
```

**Migration**:
```python
@service
class DatabaseService(Service):
    def on_init(self):
        # Guaranteed to run at startup
        self.pool = create_connection_pool(
            host='localhost',
            port=5432,
            max_connections=10
        )
        logger.info("Database connection pool initialized")
    
    def on_destroy(self):
        # Guaranteed to run at shutdown
        self.pool.close()
        logger.info("Database connection pool closed")
    
    def query(self, sql):
        with self.pool.get_connection() as conn:
            return conn.execute(sql)
```

## 4. Testing Migration

### 4.1 Current Testing Approach

```python
import unittest
from cullinan.service import service_list

class TestUserService(unittest.TestCase):
    def setUp(self):
        # Manual mock setup
        self.original_email = service_list.get('EmailService')
        self.mock_email = MockEmailService()
        service_list['EmailService'] = self.mock_email
    
    def tearDown(self):
        # Manual cleanup
        if self.original_email:
            service_list['EmailService'] = self.original_email
        else:
            del service_list['EmailService']
    
    def test_create_user(self):
        user_service = service_list['UserService']
        user = user_service.create_user('John', 'john@example.com')
        self.assertEqual(user['name'], 'John')
        self.assertTrue(self.mock_email.sent)
```

### 4.2 New Testing Approach

```python
import unittest
from cullinan.testing import TestRegistry, MockService

class MockEmailService(MockService):
    def send(self, to, subject, body):
        self.record_call('send', to=to, subject=subject, body=body)

class TestUserService(unittest.TestCase):
    def setUp(self):
        # Clean isolated registry
        self.registry = TestRegistry()
        
        # Register mock
        self.mock_email = MockEmailService()
        self.registry.register_mock('EmailService', self.mock_email)
        
        # Register service under test
        self.registry.register('UserService', UserService, 
                              dependencies=['EmailService'])
    
    def test_create_user(self):
        # Get service with injected mocks
        service = self.registry.get('UserService')
        
        # Test
        user = service.create_user('John', 'john@example.com')
        
        # Assertions
        self.assertEqual(user['name'], 'John')
        self.assertTrue(self.mock_email.was_called('send'))
        self.assertEqual(self.mock_email.call_count('send'), 1)
        
        # Check call arguments
        args = self.mock_email.get_call_args('send')
        self.assertEqual(args['to'], 'john@example.com')
```

**Benefits of New Approach**:
- ✅ No global state pollution
- ✅ Automatic cleanup
- ✅ Better assertions
- ✅ Isolated tests

## 5. Step-by-Step Migration Process

### 5.1 Phase 1: Assessment

**Analyze your services**:
```bash
# Count services
grep -r "@service" your_app/ | wc -l

# Identify dependencies
grep -r "service_list\[" your_app/
```

**Categorize services**:
- **Simple** (no dependencies) → No migration needed
- **With dependencies** → Good candidates for DI
- **With resources** → Good candidates for lifecycle hooks

### 5.2 Phase 2: Test Infrastructure

**Update test utilities first**:
```python
# tests/conftest.py (pytest) or test_base.py (unittest)
from cullinan.testing import TestRegistry

class BaseServiceTest(unittest.TestCase):
    def setUp(self):
        self.registry = TestRegistry()
    
    def tearDown(self):
        self.registry.clear()
```

### 5.3 Phase 3: Migrate Services

**Order of migration**:
1. **Leaf services first** (no dependencies)
2. **Move up the tree** (services that depend on migrated ones)
3. **Root services last** (depend on many others)

**Example Order**:
```
1. ConfigService (no deps)
2. LogService (no deps)
3. DatabaseService (depends on ConfigService)
4. EmailService (depends on ConfigService)
5. UserService (depends on DatabaseService, EmailService)
6. OrderService (depends on UserService, others)
```

### 5.4 Phase 4: Verification

**After each service migration**:
```bash
# Run tests
python -m pytest tests/test_user_service.py -v

# Run all tests
python run_tests.py

# Check for issues
python -m pytest -v --tb=short
```

## 6. Common Pitfalls

### 6.1 Circular Dependencies

**Problem**:
```python
@service(dependencies=['ServiceB'])
class ServiceA(Service):
    pass

@service(dependencies=['ServiceA'])  # Circular!
class ServiceB(Service):
    pass
```

**Error**:
```
CircularDependencyError: Circular dependency detected: ServiceA -> ServiceB -> ServiceA
```

**Solution**: Refactor to break the cycle
```python
# Extract common logic to a third service
@service
class CommonService(Service):
    pass

@service(dependencies=['CommonService'])
class ServiceA(Service):
    pass

@service(dependencies=['CommonService'])
class ServiceB(Service):
    pass
```

### 6.2 Missing on_init() Call

**Problem**:
```python
@service(dependencies=['EmailService'])
class UserService(Service):
    # Forgot on_init()!
    
    def create_user(self, name):
        # self.email doesn't exist!
        self.email.send(...)  # AttributeError!
```

**Solution**:
```python
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):  # Add this!
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name):
        self.email.send(...)
```

### 6.3 Accessing Services Too Early

**Problem**:
```python
@service(dependencies=['ConfigService'])
class DatabaseService(Service):
    def __init__(self):
        # Too early! Dependencies not injected yet!
        config = self.dependencies['ConfigService']  # KeyError!
```

**Solution**:
```python
@service(dependencies=['ConfigService'])
class DatabaseService(Service):
    def on_init(self):  # Use on_init() instead!
        config = self.dependencies['ConfigService']
        self.pool = create_pool(config.db_url)
```

## 7. Migration Checklist

### 7.1 Pre-Migration

- [ ] Read all documentation
- [ ] Understand new concepts
- [ ] Review your service dependencies
- [ ] Backup your code (git commit)
- [ ] Ensure all tests pass

### 7.2 During Migration

- [ ] Migrate tests first
- [ ] Migrate one service at a time
- [ ] Run tests after each change
- [ ] Update documentation
- [ ] Check for circular dependencies

### 7.3 Post-Migration

- [ ] All tests pass
- [ ] Code review
- [ ] Update team documentation
- [ ] Monitor for issues
- [ ] Celebrate! 🎉

## 8. Rollback Plan

### 8.1 If Issues Arise

**Per-service rollback**:
```python
# Revert to simple decorator
@service  # Remove dependencies parameter
class UserService(Service):
    # Remove on_init()
    # Go back to manual lookup
    def create_user(self, name):
        email = service_list['EmailService']
        email.send(...)
```

**Full rollback**:
```bash
git revert <commit-hash>
# Or restore from backup
```

## 9. Getting Help

### 9.1 Resources

**Documentation**:
- API Reference: `docs/api/`
- Examples: `examples/`
- This migration guide

**Community**:
- GitHub Issues: Report problems
- Discussions: Ask questions
- Discord/Slack: Real-time help

### 9.2 Common Questions

**Q: Do I have to migrate?**
A: No! Your code works as-is. Migrate when you're ready.

**Q: Can I mix old and new styles?**
A: Yes! They work together seamlessly.

**Q: What if I find a bug?**
A: Report it on GitHub Issues. We'll fix it promptly.

**Q: Can I migrate gradually?**
A: Yes! That's the recommended approach.

---

**Document Version**: 1.0  
**Author**: Cullinan Framework Team  
**Date**: 2025-11-10  
**Status**: Final Draft
