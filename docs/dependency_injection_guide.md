# Cullinan Dependency Injection Guide

> **Version**: v0.90  
> **Author**: Plumeink  
> **Last Updated**: 2025-12-25

---

## Overview

Cullinan provides a powerful Dependency Injection (DI) system that supports multiple injection methods. Version 0.90 introduces a unified injection model. This guide helps you understand and use these features.

## Table of Contents

1. [Basic Concepts](#basic-concepts)
2. [Three Injection Methods](#three-injection-methods)
3. [Unified Injection Model](#unified-injection-model)
4. [Advanced Features](#advanced-features)
5. [Best Practices](#best-practices)
6. [Migration Guide](#migration-guide)

---

## Basic Concepts

### What is Dependency Injection?

Dependency Injection is a design pattern that implements Inversion of Control (IoC). Simply put, it allows the framework to automatically inject required dependencies into your classes, rather than manually creating them inside the class.

### Why Use Dependency Injection?

✅ **Loose Coupling**: Clearer dependency relationships between classes  
✅ **Testable**: Easy to replace dependencies for unit testing  
✅ **Maintainable**: Centralized dependency management  
✅ **Extensible**: Easy to add new services and components

---

## Three Injection Methods

Cullinan supports three dependency injection methods, all unified under the new injection model.

### 1. Inject() - Type Annotation Injection

**Recommendation**: ⭐⭐⭐⭐⭐

Uses type annotations, providing the best IDE support and type safety.

```python
from cullinan.core import Inject
from cullinan.service import service

@service
class DatabaseService:
    def query(self, sql: str):
        return f"Result: {sql}"

@service
class UserService:
    # Use type annotation + Inject()
    database: DatabaseService = Inject()
    
    def get_user(self, user_id: int):
        return self.database.query(f"SELECT * FROM users WHERE id={user_id}")
```

**Features**:
- ✅ IDE auto-completion
- ✅ Type checking
- ✅ Automatic dependency name inference
- ✅ Support for optional dependencies

**Optional Dependencies**:
```python
class UserService:
    database: DatabaseService = Inject()
    cache: CacheService = Inject(required=False)  # Optional
    
    def get_user(self, user_id: int):
        # cache may be None
        if self.cache:
            return self.cache.get(f"user_{user_id}")
        return self.database.query(...)
```

### 2. InjectByName() - String Name Injection

**Recommendation**: ⭐⭐⭐⭐

Uses string names, no need to import dependency classes.

```python
from cullinan.controller import controller
from cullinan.core import InjectByName

@controller(url='/api')
class UserController:
    # Explicitly specify name
    user_service = InjectByName('UserService')
    
    # Auto-infer name (email_service → EmailService)
    email_service = InjectByName()
    
    def get_user(self, user_id: int):
        return self.user_service.get_user(user_id)
```

**Features**:
- ✅ No need to import dependency classes
- ✅ Avoid circular imports
- ✅ Automatic name inference (snake_case → PascalCase)
- ✅ Support for optional dependencies

**Auto Name Inference Rules**:
```python
user_service = InjectByName()  # → UserService
email_service = InjectByName()  # → EmailService
cache_manager = InjectByName()  # → CacheManager
```

### 3. @injectable - Decorator Batch Injection

**Recommendation**: ⭐⭐⭐⭐⭐

Uses decorator approach, automatically injects all dependencies when the class is instantiated.

```python
from cullinan.controller import controller
from cullinan.core import injectable, Inject, InjectByName

@injectable
@controller(url='/api')
class UserController:
    database: DatabaseService = Inject()
    cache = InjectByName('CacheService')
    logger = InjectByName('LogService', required=False)
    
    def __init__(self):
        # After __init__, all dependencies are automatically injected
        pass
    
    def get_user(self, user_id: int):
        # database and cache are now available
        result = self.database.query(...)
        if self.cache:
            self.cache.set(f"user_{user_id}", result)
        return result
```

**Features**:
- ✅ Automatic batch injection
- ✅ Mix Inject and InjectByName
- ✅ Injection happens immediately after __init__
- ✅ Compatible with @service and @controller decorators

---

## Unified Injection Model

### New Architecture Overview

Starting from v0.90, Cullinan introduces a unified injection model where all injection methods are based on the same underlying architecture:

```
┌─────────────────────────────────────────┐
│  Application Layer (Inject / InjectByName / @injectable) │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  InjectionPoint (Unified Metadata Model) │
│  - attr_name: Attribute name             │
│  - dependency_name: Dependency name      │
│  - required: Is required                 │
│  - attr_type: Type annotation            │
│  - resolve_strategy: Resolution strategy │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  InjectionExecutor (Unified Executor)    │
│  - resolve_injection_point()             │
│  - inject_instance()                     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  ServiceRegistry / ProviderRegistry      │
│  (Service Providers)                     │
└─────────────────────────────────────────┘
```

### Resolution Strategies

The new model supports three resolution strategies:

#### AUTO (Automatic Inference)
```python
# Default strategy when using Inject()
user_service: UserService = Inject()
# Strategy: Priority by type (UserService), fallback to name ('UserService')
```

#### BY_TYPE (By Type)
```python
# Force resolution by type
user_service: UserService = Inject()
# Only look for services of type UserService
```

#### BY_NAME (By Name)
```python
# Strategy when using InjectByName
user_service = InjectByName('UserService')
# Only look for services named 'UserService'
```

### Performance Features

The new unified model provides excellent performance:

- **Caching**: Injected dependencies are cached in instances, avoiding repeated resolution
- **Lazy Injection**: Dependencies are only resolved on first access
- **Batch Injection**: @injectable injects all dependencies at once, reducing overhead

---

## Advanced Features

### 1. Nested Dependencies

Services can depend on other services, forming dependency chains:

```python
@service
class DatabaseService:
    pass

@service
class CacheService:
    pass

@service
@injectable
class DataAccessLayer:
    database: DatabaseService = Inject()
    cache: CacheService = Inject()
    
    def fetch(self, key):
        # Check cache first
        if self.cache:
            return self.cache.get(key)
        # Then query database
        return self.database.query(...)

@injectable
class BusinessLogic:
    dal: DataAccessLayer = Inject()
    
    def process(self, key):
        return self.dal.fetch(key)
```

### 2. Circular Dependency Detection

The framework automatically detects and prevents circular dependencies:

```python
@service
@injectable
class ServiceA:
    b: ServiceB = Inject()

@service
@injectable
class ServiceB:
    a: ServiceA = Inject()  # ❌ Raises CircularDependencyError
```

**Solutions**:
1. Redesign dependency relationships
2. Use lazy injection
3. Introduce an intermediate layer to break the cycle

### 3. String Annotation Support

Supports string type annotations (to avoid circular imports):

```python
from __future__ import annotations

@injectable
class UserController:
    # Use string annotation (Python 3.7+)
    user_service: 'UserService' = Inject()
```

### 4. Test Mocking

All injection methods support manual setting (convenient for testing):

```python
def test_user_controller():
    controller = UserController()
    
    # Manually inject mock object
    controller.user_service = MockUserService()
    
    # Test business logic
    result = controller.get_user(123)
    assert result == expected_value
```

---

## Best Practices

### ✅ Recommended Approaches

#### 1. Prefer Inject() + Type Annotations
```python
@injectable
class UserService:
    database: DatabaseService = Inject()  # ✅ Recommended
    cache: CacheService = Inject()
```

#### 2. Clearly Mark Optional Dependencies
```python
class UserService:
    database: DatabaseService = Inject()  # Required
    cache: CacheService = Inject(required=False)  # Optional
```

#### 3. Use @injectable to Simplify Injection
```python
@injectable
class UserController:
    user_service: UserService = Inject()
    # Automatically injected, no manual call needed
```

#### 4. Service Classes Use @service Decorator
```python
@service  # Auto-register to ServiceRegistry
@injectable  # Support dependency injection
class UserService:
    database: DatabaseService = Inject()
```

### ❌ Things to Avoid

#### 1. Avoid Accessing Dependencies in Constructor
```python
@injectable
class UserService:
    database: DatabaseService = Inject()
    
    def __init__(self):
        # ❌ database not yet injected
        # self.database.query(...)  
        pass
    
    def get_user(self, user_id):
        # ✅ Safe to access now
        return self.database.query(...)
```

#### 2. Avoid Circular Dependencies
```python
# ❌ Wrong: Circular dependency
@service
class ServiceA:
    b: ServiceB = Inject()

@service
class ServiceB:
    a: ServiceA = Inject()
```

#### 3. Avoid Overusing InjectByName
```python
# ❌ Not recommended: Lose type safety
user_service = InjectByName('UserService')

# ✅ Recommended: Type-safe
user_service: UserService = Inject()
```

---

## Migration Guide

### Migrating from Old Code

If your code uses the old injection approach, **no changes needed**! The new unified model is fully backward compatible.

#### Old Code Still Works
```python
# Old code - still works
@injectable
class UserService:
    database: DatabaseService = Inject()

# New code - exactly the same syntax
@injectable
class UserService:
    database: DatabaseService = Inject()
```

#### Backward Compatibility Mechanism

The framework internally uses a backward compatibility mechanism:
1. **Try new model first** (InjectionExecutor)
2. **Auto-fallback on failure** to old logic (registry.inject())
3. **Completely transparent**, users unaware

These backward compatibility codes are marked in the source:
```python
# BACKWARD_COMPAT: v0.8 - Keep old injection logic
# Planned removal version: v1.0
```

### Upgrade Recommendations

Although old code continues to work, it's recommended to:

1. **New projects**: Use the new recommended patterns directly
2. **Existing projects**: Migrate gradually, no need to change everything at once
3. **Monitor performance**: New model performs better in most scenarios

---

## FAQ

### Q: Which of the three injection methods should I use?

**A**: Recommended priority:
1. **Inject() + type annotations**: Most recommended, type-safe
2. **@injectable + mixed use**: Simplifies code
3. **InjectByName**: Use when avoiding circular imports

### Q: When are dependencies injected?

**A**: 
- **Inject/InjectByName**: On first property access (lazy injection)
- **@injectable**: After __init__ method executes (batch injection)

### Q: How to handle optional dependencies?

**A**: 
```python
cache: CacheService = Inject(required=False)

if self.cache:  # Check if None
    self.cache.set(key, value)
```

### Q: How to avoid circular dependencies?

**A**:
1. Redesign dependency relationships
2. Use event system for decoupling
3. Introduce intermediate layer/Facade

### Q: What about performance?

**A**: The new model performs excellently:
- Cache hit: < 1 μs
- First resolution: 10-50 μs
- On par with or better than old model

---

## Complete Examples

### Example 1: Simple Three-Tier Architecture

```python
from cullinan.core import Inject, injectable
from cullinan.service import service

# Data Access Layer
@service
class DatabaseService:
    def query(self, sql: str):
        return f"Query result: {sql}"

# Business Logic Layer
@service
@injectable
class UserService:
    database: DatabaseService = Inject()
    
    def get_user(self, user_id: int):
        return self.database.query(
            f"SELECT * FROM users WHERE id={user_id}"
        )
    
    def create_user(self, username: str):
        return self.database.query(
            f"INSERT INTO users (username) VALUES ('{username}')"
        )

# Controller Layer
@injectable
class UserController:
    user_service: UserService = Inject()
    
    def get(self, user_id: int):
        return self.user_service.get_user(user_id)
    
    def post(self, username: str):
        return self.user_service.create_user(username)
```

### Example 2: Complex Scenario with Caching

```python
from cullinan.core import Inject, InjectByName, injectable
from cullinan.service import service

@service
class CacheService:
    def get(self, key): pass
    def set(self, key, value): pass

@service
class LogService:
    def log(self, message): pass

@service
@injectable
class UserService:
    database: DatabaseService = Inject()
    cache: CacheService = Inject(required=False)
    logger = InjectByName('LogService', required=False)
    
    def get_user(self, user_id: int):
        # Try to get from cache
        if self.cache:
            cached = self.cache.get(f"user_{user_id}")
            if cached:
                if self.logger:
                    self.logger.log(f"Cache hit: user_{user_id}")
                return cached
        
        # Query from database
        result = self.database.query(
            f"SELECT * FROM users WHERE id={user_id}"
        )
        
        # Write to cache
        if self.cache:
            self.cache.set(f"user_{user_id}", result)
        
        return result
```

---

## References

- [Architecture Documentation](./architecture.md)
- [Extension Development Guide](./extension_development_guide.md)
- [API Reference](./api_reference.md)

---

**Changelog**:
- 2025-12-24: Document created, covering v0.9 unified injection model
- Future: Continuous updates to best practices and examples

