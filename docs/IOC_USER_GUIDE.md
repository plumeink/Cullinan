# Cullinan Core IoC/DI User Guide

Version: v0.8.0-beta  
Last Updated: 2025-01-13

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Dependency Injection Methods](#dependency-injection-methods)
4. [Provider System](#provider-system)
5. [Scope Management](#scope-management)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [FAQ](#faq)

---

## Quick Start

### Installation

Cullinan Core is part of the Cullinan framework. No separate installation required.

### First Example

```python
from cullinan.core import injectable, Inject

# 1. Define a service
class UserService:
    def get_user(self, user_id):
        return f"User {user_id}"

# 2. Register the service
from cullinan.service import service

@service
class UserService:
    def get_user(self, user_id):
        return f"User {user_id}"

# 3. Use dependency injection
@injectable
class UserController:
    user_service: UserService = Inject()
    
    def index(self):
        return self.user_service.get_user(1)

# 4. Create instance (auto-injection)
controller = UserController()
print(controller.index())  # Output: User 1
```

---

## Core Concepts

### Dependency Injection

Dependency Injection is a design pattern that implements Inversion of Control (IoC). It separates the creation and management of dependencies from their consumers.

**Benefits**:
- Reduced coupling
- Improved testability
- Easier maintenance and extension
- Interface-oriented programming support

### IoC Container

Cullinan Core provides a complete IoC container responsible for:
- Managing object lifecycles
- Resolving dependencies
- Auto-wiring dependencies
- Handling scopes

---

## Dependency Injection Methods

Cullinan Core supports three injection methods:

### 1. Property Injection (Recommended)

Use `Inject` descriptor for property injection:

```python
from cullinan.core import injectable, Inject

@injectable
class UserController:
    # Auto-infer type
    user_service: UserService = Inject()
    
    # Specify name
    email_service: Any = Inject(name='EmailService')
    
    # Optional dependency
    cache: Cache = Inject(required=False)
```

**Features**:
- Lazy loading (resolved on first access)
- Type inference support
- Optional dependencies
- Easy to test (can be manually set)

### 2. Constructor Injection

Use `@inject_constructor` decorator:

```python
from cullinan.core import inject_constructor

@inject_constructor
class UserController:
    def __init__(self, user_service: UserService, config: Config):
        self.user_service = user_service
        self.config = config
```

**Features**:
- Suitable for immutable objects
- Dependencies injected at construction
- Ensures object completeness
- Supports partial manual parameters

### 3. Mixed Injection

Combine property and constructor injection:

```python
from cullinan.core import inject_constructor, injectable, Inject

@inject_constructor
@injectable
class UserController:
    # Constructor injection (required dependencies)
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    # Property injection (optional dependencies)
    cache: Cache = Inject(required=False)
    logger: Logger = Inject(required=False)
```

**Use Cases**:
- Required dependencies via constructor
- Optional dependencies via property

---

## Provider System

Providers define how dependencies are created and obtained.

### Provider Types

#### 1. InstanceProvider

Provides existing instances directly:

```python
from cullinan.core import InstanceProvider

config = Config()
provider = InstanceProvider(config)

# Always returns the same instance
instance = provider.get()
```

#### 2. ClassProvider

Provides dependencies by instantiating classes:

```python
from cullinan.core import ClassProvider

# Singleton mode
provider = ClassProvider(UserService, singleton=True)
service1 = provider.get()
service2 = provider.get()
assert service1 is service2  # Same instance

# Transient mode
provider = ClassProvider(TempData, singleton=False)
temp1 = provider.get()
temp2 = provider.get()
assert temp1 is not temp2  # Different instances
```

#### 3. FactoryProvider

Provides dependencies via factory functions:

```python
from cullinan.core import FactoryProvider

def create_database():
    return Database(host='localhost', port=5432)

# Singleton factory
provider = FactoryProvider(create_database, singleton=True)

# Transient factory
provider = FactoryProvider(lambda: TempFile(), singleton=False)
```

#### 4. ScopedProvider

Scoped provider (use with Scope):

```python
from cullinan.core import ScopedProvider, SingletonScope

provider = ScopedProvider(
    lambda: UserService(),
    SingletonScope(),
    'UserService'
)
```

### ProviderRegistry

Manages all providers:

```python
from cullinan.core import ProviderRegistry

registry = ProviderRegistry()

# Register instance
registry.register_instance('config', config)

# Register class
registry.register_class('UserService', UserService, singleton=True)

# Register factory
registry.register_factory('database', create_database, singleton=True)

# Get instance
service = registry.get_instance('UserService')
```

---

## Scope Management

Scopes control the lifecycle and sharing of dependency instances.

### SingletonScope

Application-level singleton, created once per application:

```python
from cullinan.core import SingletonScope, ScopedProvider

scope = SingletonScope()
provider = ScopedProvider(
    lambda: Database(),
    scope,
    'Database'
)

db1 = provider.get()
db2 = provider.get()
assert db1 is db2  # Same instance
```

**Use Cases**:
- Database connections
- Configuration objects
- Logging services
- Cache managers

### TransientScope

Creates new instance for each request:

```python
from cullinan.core import TransientScope, ScopedProvider

scope = TransientScope()
provider = ScopedProvider(
    lambda: TempData(),
    scope,
    'TempData'
)

temp1 = provider.get()
temp2 = provider.get()
assert temp1 is not temp2  # Different instances
```

**Use Cases**:
- Temporary data objects
- Stateless services
- Short-lived objects

### RequestScope

One instance per request, shared within same request:

```python
from cullinan.core import RequestScope, ScopedProvider, create_context

scope = RequestScope()
provider = ScopedProvider(
    lambda: RequestHandler(),
    scope,
    'RequestHandler'
)

# Request 1
with create_context():
    handler1 = provider.get()
    handler2 = provider.get()
    assert handler1 is handler2  # Same instance

# Request 2
with create_context():
    handler3 = provider.get()
    assert handler3 is not handler1  # Different instance
```

**Use Cases**:
- Request handlers
- Current user information
- Request-level cache
- Transaction managers

### Global Scope Instances

Use predefined global scopes:

```python
from cullinan.core import (
    get_singleton_scope,
    get_transient_scope,
    get_request_scope
)

singleton_scope = get_singleton_scope()
transient_scope = get_transient_scope()
request_scope = get_request_scope()
```

---

## Advanced Features

### 1. MRO Inheritance Support

Subclasses automatically inherit parent injection declarations:

```python
@injectable
class BaseController:
    logger: Logger = Inject()

class UserController(BaseController):
    # Automatically inherits logger injection
    user_service: UserService = Inject()
```

### 2. Circular Dependency Detection

Automatically detects and reports circular dependencies:

```python
# If ServiceA depends on ServiceB, and ServiceB depends on ServiceA
# Raises CircularDependencyError:
# "Circular dependency detected: ServiceA -> ServiceB -> ServiceA"
```

### 3. Thread Safety

All registry operations are thread-safe:

```python
import threading

registry = ProviderRegistry()

def worker(thread_id):
    registry.register_instance(f'item_{thread_id}', Item())

threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 4. Duplicate Registration Policy

Configure duplicate registration handling:

```python
from cullinan.core import SimpleRegistry

# Strict mode - raise exception
registry = SimpleRegistry(duplicate_policy='error')

# Warning mode - log warning and skip (default)
registry = SimpleRegistry(duplicate_policy='warn')

# Replace mode - silently replace
registry = SimpleRegistry(duplicate_policy='replace')
```

### 5. Optional Dependencies

Support optional dependencies that don't raise errors if not found:

```python
@injectable
class UserController:
    # Required dependency
    user_service: UserService = Inject()
    
    # Optional dependencies
    cache: Cache = Inject(required=False)
    logger: Logger = Inject(required=False)
```

---

## Best Practices

### 1. Choose the Right Injection Method

- **Property Injection**: Default choice, flexible and testable
- **Constructor Injection**: Immutable objects, required dependencies
- **Mixed Injection**: Combine benefits of both

### 2. Use Appropriate Scopes

- **SingletonScope**: Stateless services, shared resources
- **TransientScope**: Stateful objects, temporary data
- **RequestScope**: Request-related data

### 3. Avoid Circular Dependencies

If circular dependencies occur, consider:
- Redesign class structure
- Use interfaces/abstract classes
- Lazy loading
- Use events/callbacks

### 4. Write Testable Code

```python
@injectable
class UserController:
    user_service: UserService = Inject()
    
    def get_user(self, user_id):
        return self.user_service.get_user(user_id)

# Can manually set dependencies in tests
def test_get_user():
    controller = UserController()
    controller.user_service = MockUserService()  # Mock object
    result = controller.get_user(1)
    assert result == "Mock User 1"
```

### 5. Explicit Dependencies

```python
# Good practice - explicit type annotations
@injectable
class UserController:
    user_service: UserService = Inject()
    config: Config = Inject()

# Avoid - using Any
@injectable
class UserController:
    user_service: Any = Inject(name='UserService')
```

---

## FAQ

### Q: Injection fails with "dependency not found"?

**A**: Check the following:
1. Is the dependency registered (using `@service` or manual registration)?
2. Is the type annotation correct?
3. Does the injection name match?
4. Is the Provider Registry added to InjectionRegistry?

### Q: How to mock dependencies in tests?

**A**: Two ways:
```python
# Method 1: Directly set property
controller = UserController()
controller.user_service = MockUserService()

# Method 2: Register mock object
mock_registry = SimpleRegistry()
mock_registry.register('UserService', MockUserService())
get_injection_registry().add_provider_registry(mock_registry, priority=100)
```

### Q: What's the difference between constructor and property injection?

**A**: 
- **Constructor Injection**: Dependencies injected at object creation, suitable for immutable objects
- **Property Injection**: Lazy injection, resolved on first access, more flexible

### Q: How to implement singleton pattern?

**A**: Three ways:
```python
# Method 1: ClassProvider with singleton=True
provider = ClassProvider(UserService, singleton=True)

# Method 2: SingletonScope
provider = ScopedProvider(lambda: UserService(), SingletonScope(), 'UserService')

# Method 3: Register instance directly
registry.register_instance('UserService', UserService())
```

### Q: Must RequestScope be used within request context?

**A**: Yes, RequestScope requires an active request context:
```python
from cullinan.core import create_context

# Automatically created in request handlers
# Manual use requires with create_context()
with create_context():
    service = request_scoped_provider.get()
```

### Q: How to handle circular dependencies?

**A**: Cullinan automatically detects and raises `CircularDependencyError`. Solutions:
1. Refactor code to break the cycle
2. Use interfaces/abstract classes
3. Lazy loading (Inject is already lazy)
4. Reconsider if there's a design issue

---

## Related Documentation

- [API Reference](API_REFERENCE.md)
- [Architecture Design](ARCHITECTURE_MASTER.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [FAQ](FAQ.md)

---

**Version**: v0.8.0-beta  
**Last Updated**: 2025-01-13  
**Maintainer**: Cullinan Team
# Cullinan Core IoC/DI 使用指南

版本：v0.8.0-beta  
更新日期：2025-01-13

---

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [依赖注入方式](#依赖注入方式)
4. [Provider 系统](#provider-系统)
5. [作用域管理](#作用域管理)
6. [高级特性](#高级特性)
7. [最佳实践](#最佳实践)
8. [常见问题](#常见问题)

---

## 快速开始

### 安装

Cullinan Core 是 Cullinan 框架的核心模块，无需单独安装。

### 第一个示例

```python
from cullinan.core import injectable, Inject

# 1. 定义服务
class UserService:
    def get_user(self, user_id):
        return f"User {user_id}"

# 2. 注册服务
from cullinan.service import service

@service
class UserService:
    def get_user(self, user_id):
        return f"User {user_id}"

# 3. 使用依赖注入
@injectable
class UserController:
    user_service: UserService = Inject()
    
    def index(self):
        return self.user_service.get_user(1)

# 4. 创建实例（自动注入）
controller = UserController()
print(controller.index())  # 输出: User 1
```

---

## 核心概念

### 依赖注入（Dependency Injection）

依赖注入是一种设计模式，用于实现控制反转（IoC）。它允许您将依赖关系的创建和管理从使用者中分离出来。

**优点**：
- 降低耦合度
- 提高可测试性
- 便于维护和扩展
- 支持面向接口编程

### IoC 容器

Cullinan Core 提供了一个完整的 IoC 容器，负责：
- 管理对象的生命周期
- 解析依赖关系
- 自动装配依赖
- 处理作用域

---

## 依赖注入方式

Cullinan Core 支持三种依赖注入方式：

### 1. 属性注入（推荐）

使用 `Inject` 描述符进行属性注入：

```python
from cullinan.core import injectable, Inject

@injectable
class UserController:
    # 自动推断类型
    user_service: UserService = Inject()
    
    # 指定名称
    email_service: Any = Inject(name='EmailService')
    
    # 可选依赖
    cache: Cache = Inject(required=False)
```

**特点**：
- 延迟加载（首次访问时才解析）
- 支持类型推断
- 支持可选依赖
- 易于测试（可手动设置）

### 2. 构造器注入

使用 `@inject_constructor` 装饰器进行构造器注入：

```python
from cullinan.core import inject_constructor

@inject_constructor
class UserController:
    def __init__(self, user_service: UserService, config: Config):
        self.user_service = user_service
        self.config = config
```

**特点**：
- 适合不可变对象
- 依赖在构造时注入
- 保证对象完整性
- 支持部分手动传参

### 3. 混合注入

结合属性注入和构造器注入：

```python
from cullinan.core import inject_constructor, injectable, Inject

@inject_constructor
@injectable
class UserController:
    # 构造器注入（必需依赖）
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    # 属性注入（可选依赖）
    cache: Cache = Inject(required=False)
    logger: Logger = Inject(required=False)
```

**适用场景**：
- 必需依赖使用构造器注入
- 可选依赖使用属性注入

---

## Provider 系统

Provider 定义了依赖的创建和获取方式。

### Provider 类型

#### 1. InstanceProvider

直接提供已创建的实例：

```python
from cullinan.core import InstanceProvider

config = Config()
provider = InstanceProvider(config)

# 始终返回同一实例
instance = provider.get()
```

#### 2. ClassProvider

通过实例化类提供依赖：

```python
from cullinan.core import ClassProvider

# 单例模式
provider = ClassProvider(UserService, singleton=True)
service1 = provider.get()
service2 = provider.get()
assert service1 is service2  # 相同实例

# 瞬时模式
provider = ClassProvider(TempData, singleton=False)
temp1 = provider.get()
temp2 = provider.get()
assert temp1 is not temp2  # 不同实例
```

#### 3. FactoryProvider

通过工厂函数提供依赖：

```python
from cullinan.core import FactoryProvider

def create_database():
    return Database(host='localhost', port=5432)

# 单例工厂
provider = FactoryProvider(create_database, singleton=True)

# 瞬时工厂
provider = FactoryProvider(lambda: TempFile(), singleton=False)
```

#### 4. ScopedProvider

带作用域的提供者（结合 Scope 使用）：

```python
from cullinan.core import ScopedProvider, SingletonScope

provider = ScopedProvider(
    lambda: UserService(),
    SingletonScope(),
    'UserService'
)
```

### ProviderRegistry

管理所有 Provider：

```python
from cullinan.core import ProviderRegistry

registry = ProviderRegistry()

# 注册实例
registry.register_instance('config', config)

# 注册类
registry.register_class('UserService', UserService, singleton=True)

# 注册工厂
registry.register_factory('database', create_database, singleton=True)

# 获取实例
service = registry.get_instance('UserService')
```

---

## 作用域管理

作用域控制依赖实例的生命周期和共享范围。

### SingletonScope（单例作用域）

应用级单例，整个应用生命周期内只创建一次：

```python
from cullinan.core import SingletonScope, ScopedProvider

scope = SingletonScope()
provider = ScopedProvider(
    lambda: Database(),
    scope,
    'Database'
)

db1 = provider.get()
db2 = provider.get()
assert db1 is db2  # 相同实例
```

**适用场景**：
- 数据库连接
- 配置对象
- 日志服务
- 缓存管理器

### TransientScope（瞬时作用域）

每次请求都创建新实例：

```python
from cullinan.core import TransientScope, ScopedProvider

scope = TransientScope()
provider = ScopedProvider(
    lambda: TempData(),
    scope,
    'TempData'
)

temp1 = provider.get()
temp2 = provider.get()
assert temp1 is not temp2  # 不同实例
```

**适用场景**：
- 临时数据对象
- 无状态服务
- 短生���周期对象

### RequestScope（请求作用域）

每个请求一个实例，同一请求内共享：

```python
from cullinan.core import RequestScope, ScopedProvider, create_context

scope = RequestScope()
provider = ScopedProvider(
    lambda: RequestHandler(),
    scope,
    'RequestHandler'
)

# 请求 1
with create_context():
    handler1 = provider.get()
    handler2 = provider.get()
    assert handler1 is handler2  # 相同实例

# 请求 2
with create_context():
    handler3 = provider.get()
    assert handler3 is not handler1  # 不同实例
```

**适用场景**：
- 请求处理器
- 当前用户信息
- 请求级缓存
- 事务管理器

### 全局作用域实例

使用预定义的全局作用域：

```python
from cullinan.core import (
    get_singleton_scope,
    get_transient_scope,
    get_request_scope
)

singleton_scope = get_singleton_scope()
transient_scope = get_transient_scope()
request_scope = get_request_scope()
```

---

## 高级特性

### 1. MRO 继承支持

子类自动继承父类的注入声明：

```python
@injectable
class BaseController:
    logger: Logger = Inject()

class UserController(BaseController):
    # 自动继承 logger 注入
    user_service: UserService = Inject()
```

### 2. 循环依赖检测

自动检测并报告循环依赖：

```python
# 如果 ServiceA 依赖 ServiceB，ServiceB 依赖 ServiceA
# 会抛出 CircularDependencyError:
# "Circular dependency detected: ServiceA -> ServiceB -> ServiceA"
```

### 3. 线程安全

所有注册表操作都是线程安全的：

```python
import threading

registry = ProviderRegistry()

def worker(thread_id):
    registry.register_instance(f'item_{thread_id}', Item())

threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 4. 重复注册策略

配置重复注册的处理方式：

```python
from cullinan.core import SimpleRegistry

# 严格模式 - 抛出异常
registry = SimpleRegistry(duplicate_policy='error')

# 警告模式 - 记录警告并跳过（默认）
registry = SimpleRegistry(duplicate_policy='warn')

# 替换模式 - 静默替换
registry = SimpleRegistry(duplicate_policy='replace')
```

### 5. 可选依赖

支持可选依赖，未找到时不抛出异常：

```python
@injectable
class UserController:
    # 必需依赖
    user_service: UserService = Inject()
    
    # 可选依赖
    cache: Cache = Inject(required=False)
    logger: Logger = Inject(required=False)
```

---

## 最佳实践

### 1. 选择合适的注入方式

- **属性注入**：默认选择，灵活且易于测试
- **构造器注入**：不可变对象、必需依赖
- **混合注入**：结合两者优点

### 2. 使用合适的作用域

- **SingletonScope**：无状态服务、共享资源
- **TransientScope**：有状态对象、临时数据
- **RequestScope**：请求相关数据

### 3. 避免循环依赖

如果遇到循环依赖，考虑：
- 重新设计类结构
- 使用接口/抽象类
- 延迟加载
- 使用事件/回调

### 4. 编写可测试代码

```python
@injectable
class UserController:
    user_service: UserService = Inject()
    
    def get_user(self, user_id):
        return self.user_service.get_user(user_id)

# 测试时可以手动设置依赖
def test_get_user():
    controller = UserController()
    controller.user_service = MockUserService()  # Mock 对象
    result = controller.get_user(1)
    assert result == "Mock User 1"
```

### 5. 明确依赖关系

```python
# 好的做法 - 明确的类型注解
@injectable
class UserController:
    user_service: UserService = Inject()
    config: Config = Inject()

# 避免 - 使用 Any
@injectable
class UserController:
    user_service: Any = Inject(name='UserService')
```

---

## 常见问题

### Q: 依赖注入失败，提示找不到依赖？

**A**: 检查以下几点：
1. 依赖是否已注册（使用 `@service` 或手动注册）
2. 类型注解是否正确
3. 注入名称是否匹配
4. Provider Registry 是否已添加到 InjectionRegistry

### Q: 如何在测试中 Mock 依赖？

**A**: 两种方式：
```python
# 方式1：直接设置属性
controller = UserController()
controller.user_service = MockUserService()

# 方式2：注册 Mock 对象
mock_registry = SimpleRegistry()
mock_registry.register('UserService', MockUserService())
get_injection_registry().add_provider_registry(mock_registry, priority=100)
```

### Q: 构造器注入和属性注入有什么区别？

**A**: 
- **构造器注入**：依赖在对象创建时注入，适合不可变对象
- **属性注入**：延迟注入，首次访问时才解析，更灵活

### Q: 如何实现单例模式？

**A**: 三种方式：
```python
# 方式1：ClassProvider with singleton=True
provider = ClassProvider(UserService, singleton=True)

# 方式2：SingletonScope
provider = ScopedProvider(lambda: UserService(), SingletonScope(), 'UserService')

# 方式3：直接注册实例
registry.register_instance('UserService', UserService())
```

### Q: RequestScope 必须在请求上下文中使用吗？

**A**: 是的，RequestScope 需要活动的请求上下文：
```python
from cullinan.core import create_context

# 在请求处理器中自动创建
# 手动使用需要 with create_context()
with create_context():
    service = request_scoped_provider.get()
```

### Q: 如何处理循环依赖？

**A**: Cullinan 会自动检测并抛出 `CircularDependencyError`。解决方法：
1. 重构代码，打破循环
2. 使用接口/抽象类
3. 延迟加载（Inject 本身就是延迟的）
4. 考虑是否设计有问题

---

## 相关文档

- [API 参考](API_REFERENCE.md)
- [架构设计](ARCHITECTURE_MASTER.md)
- [迁移指南](MIGRATION_GUIDE.md)
- [常见问题](FAQ.md)

---

**版本**: v0.8.0-beta  
**最后更新**: 2025-01-13  
**维护者**: Cullinan Team

