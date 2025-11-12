# Cullinan 自动依赖注入系统使用指南

## 📋 概述

Cullinan 框架提供了类似 Spring Boot 的自动依赖注入系统，所有 IoC 操作都基于 `core` 模块实现，`service` 和 `controller` 模块在上层使用这些能力，完全解耦。

## 🎯 核心特性

1. **完全自动化** - 无需手动初始化和注册
2. **无需 import** - Controller 中完全不需要 import Service 类
3. **基于 core** - 所有 IoC 能力在 core 模块实现，上层模块无耦合
4. **延迟加载** - 只在首次访问时才解析依赖
5. **单例模式** - 自动管理 Service 生命周期
6. **类型安全** - 运行时检查依赖是否存在

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌───────────────┐              ┌───────────────┐           │
│  │  Controller   │──────────────▶│   Service    │           │
│  │  @controller  │  InjectByName│   @service   │           │
│  └───────────────┘              └───────────────┘           │
│         │                               │                    │
│         │ 使用                          │ 使用               │
│         ▼                               ▼                    │
├─────────────────────────────────────────────────────────────┤
│                        Core Layer                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           InjectionRegistry (核心注入系统)            │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │InjectByName│  │ injectable │  │   Inject   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Provider Registries                      │  │
│  │  - ServiceRegistry (提供 Service 实例)                │  │
│  │  - 其他 Registry (可扩展)                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 关键组件

#### Core 层（基础设施）
- **`InjectByName`** - 基于字符串名称的依赖注入描述符
- **`Inject`** - 基于类型注解的依赖注入标记
- **`injectable`** - 类装饰器，自动扫描和注入
- **`InjectionRegistry`** - 全局注入注册表，管理依赖解析

#### Service 层（业务逻辑）
- **`@service`** - Service 注册装饰器（使用 core 的 `injectable`）
- **`ServiceRegistry`** - Service 管理（注册为 core 的依赖提供者）

#### Controller 层（HTTP 路由）
- **`@controller`** - Controller 注册装饰器（使用 core 的 `injectable`）

## 📝 使用方式

### 1. 定义 Service（使用 @service）

```python
from cullinan.service import service, Service
from cullinan.core import InjectByName

@service
class EmailService(Service):
    """邮件服务"""
    
    def send_email(self, to: str, subject: str, body: str):
        print(f"📧 Sending email to {to}: {subject}")
        return {"status": "sent"}

@service
class UserService(Service):
    """用户服务 - 依赖 EmailService"""
    
    # 使用 InjectByName 注入，完全不需要 import EmailService！
    email_service = InjectByName('EmailService')
    
    def create_user(self, name: str, email: str):
        # 使用注入的 email_service
        self.email_service.send_email(email, "Welcome", f"Welcome {name}!")
        return {"id": 1, "name": name}
```

### 2. 定义 Controller（使用 InjectByName）

```python
from cullinan.controller import controller, get_api, post_api
from cullinan.core import InjectByName

@controller(url='/api/users')
class UserController:
    """用户控制器 - 完全不需要 import Service！"""
    
    # 使用 InjectByName 自动注入，无需 import UserService
    user_service = InjectByName('UserService')
    
    @get_api(url='')
    def list_users(self):
        """获取用户列表"""
        users = self.user_service.get_all()
        return {"users": users}
    
    @post_api(url='')
    def create_user(self, body_params):
        """创建用户"""
        user = self.user_service.create_user(
            name=body_params.get('name'),
            email=body_params.get('email')
        )
        return {"created": True, "user": user}
```

### 3. 应用启动（自动初始化）

```python
from cullinan import Cullinan

# 创建应用实例
app = Cullinan()

# 应用启动时会自动：
# 1. 扫描所有 @service 注册的 Service
# 2. 按依赖顺序初始化所有 Service
# 3. 调用 Service 的 on_init() 生命周期方法
# 4. 将 ServiceRegistry 注册为 core 的依赖提供者

# 启动应用
app.run(port=8080)
```

## 🔍 两种注入方式详解

Cullinan 提供两种依赖注入方式：

### 方式 1: Inject（基于类型注解）

```python
from cullinan.core import Inject
from typing import TYPE_CHECKING

# 使用 TYPE_CHECKING 避免运行时导入（推荐）
if TYPE_CHECKING:
    from services.user_service import UserService

class MyController:
    # 方式1: 字符串类型注解（推荐，无需运行时 import）
    user_service: 'UserService' = Inject()
    
    # 方式2: 显式指定名称
    auth: Any = Inject(name='AuthService')
    
    # 方式3: 可选依赖
    cache: Any = Inject(name='CacheService', required=False)
```

**优点:**
- ✅ IDE 完整的代码补全
- ✅ 类型安全（编辑器检查）
- ✅ 支持字符串注解（无需运行时 import）

**工作原理:** 配合 `@injectable` 装饰器，在实例化时由 `InjectionRegistry.inject()` 处理

### 方式 2: InjectByName（基于字符串名称）

```python
from cullinan.core import InjectByName

class MyController:
    # 方式1: 显式指定名称
    user_service = InjectByName('UserService')
    
    # 方式2: 自动推断（user_service -> UserService）
    email_service = InjectByName()
    
    # 方式3: 可选依赖
    cache_service = InjectByName('CacheService', required=False)
```

**优点:**
- ✅ 更简洁，不需要类型注解
- ✅ 完全不需要 import
- ✅ 延迟加载（首次访问时才解析）

**工作原理:** 使用 Python 描述符，在首次访问时触发 `__get__` 方法解析依赖

### 对比表

| 特性 | Inject | InjectByName |
|------|--------|--------------|
| 需要类型注解 | ✅ 是 | ❌ 否 |
| IDE 补全 | ✅ 完整 | ❌ 无 |
| 代码简洁度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 注入时机 | 实例化时 | 首次访问时 |
| 推荐场景 | 大型项目 | 快速开发 |

### 使用建议

**推荐使用 Inject（大型项目）:**
```python
from cullinan.core import Inject
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.user_service import UserService

class UserController:
    user_service: 'UserService' = Inject()  # IDE 有补全
```

**使用 InjectByName（快速开发）:**
```python
from cullinan.core import InjectByName

class UserController:
    user_service = InjectByName('UserService')  # 简洁
```

### 命名规则（自动推断）

当不指定名称时，`InjectByName()` 会根据属性名自动推断 Service 名称：

| 属性名 | 推断的 Service 名称 |
|--------|-------------------|
| `user_service` | `UserService` |
| `email_service` | `EmailService` |
| `cache_service` | `CacheService` |
| `auth` | `Auth` |

### 延迟加载机制

```python
class UserController:
    user_service = InjectByName('UserService')
    
    def some_method(self):
        # 只在这里首次访问时才从 ServiceRegistry 获取实例
        users = self.user_service.get_all()  # ← 延迟加载发生在这里
        
        # 第二次访问直接返回缓存的实例（O(1)）
        more_users = self.user_service.get_all()
```

### 错误处理

```python
class MyController:
    # 必需依赖（默认）
    user_service = InjectByName('UserService')  # 找不到会抛出 RegistryError
    
    # 可选依赖
    cache = InjectByName('CacheService', required=False)  # 找不到返回 None
    
    def handle_request(self):
        # 检查可选依赖
        if self.cache is not None:
            data = self.cache.get('key')
        else:
            data = self.load_from_database()
```

## 🔄 依赖注入流程

### 1. Service 注册阶段（import 时）

```python
@service  # ← 此时注册到 ServiceRegistry
class UserService(Service):
    email_service = InjectByName('EmailService')
```

**发生的事情：**
1. `@service` 调用 `@injectable` 装饰器
2. `@injectable` 扫描类的属性，发现 `InjectByName`
3. 记录注入需求到 `InjectionRegistry`
4. 注册类到 `ServiceRegistry`
5. **不立即实例化**

### 2. Service 初始化阶段（应用启动时）

```python
app = Cullinan()  # ← 此时初始化所有 Service
```

**发生的事情：**
1. `ServiceRegistry.initialize_all()` 被调用
2. 按依赖顺序创建 Service 实例
3. 实例化时，`@injectable` 包装的 `__init__` 调用 `inject()`
4. `inject()` 方法将 `InjectByName` 描述符替换为实际的 Service 实例
5. 调用 `on_init()` 生命周期方法

### 3. Controller 使用阶段（请求处理时）

```python
@controller(url='/api/users')
class UserController:
    user_service = InjectByName('UserService')
```

**发生的事情：**
1. 请求到达时，创建 Controller 实例
2. `@injectable` 包装的 `__init__` 自动注入依赖
3. `InjectByName` 描述符从 `ServiceRegistry` 获取已初始化的实例
4. 缓存实例到 Controller 实例字典

## ⚙️ 高级用法

### 1. Service 之间的依赖

```python
@service
class DatabaseService(Service):
    def query(self, sql):
        return [{"id": 1, "name": "Alice"}]

@service
class CacheService(Service):
    database = InjectByName('DatabaseService')
    
    def get_cached(self, key):
        # 先查缓存，缓存未命中则查数据库
        cached = self._cache.get(key)
        if cached is None:
            cached = self.database.query(f"SELECT * FROM {key}")
            self._cache[key] = cached
        return cached

@service
class UserService(Service):
    cache = InjectByName('CacheService')
    
    def get_all(self):
        # 使用 CacheService，CacheService 内部使用 DatabaseService
        return self.cache.get_cached('users')
```

**依赖链：** `UserService` → `CacheService` → `DatabaseService`

框架自动按正确顺序初始化：`DatabaseService` → `CacheService` → `UserService`

### 2. 可选依赖

```python
@service
class UserService(Service):
    cache = InjectByName('CacheService', required=False)
    database = InjectByName('DatabaseService')  # 必需
    
    def get_user(self, user_id):
        # 如果有缓存服务，使用它
        if self.cache is not None:
            cached = self.cache.get(f'user:{user_id}')
            if cached:
                return cached
        
        # 否则直接查数据库
        user = self.database.get_user(user_id)
        
        # 如果有缓存，更新缓存
        if self.cache is not None:
            self.cache.set(f'user:{user_id}', user)
        
        return user
```

### 3. 测试中的 Mock

```python
# 生产代码
@controller(url='/api/users')
class UserController:
    user_service = InjectByName('UserService')

# 测试代码
def test_user_controller():
    # 创建 Mock Service
    class MockUserService:
        def get_all(self):
            return [{"id": 1, "name": "Test User"}]
    
    # 创建 Controller 并注入 Mock
    controller = UserController()
    controller.user_service = MockUserService()  # 手动设置，覆盖自动注入
    
    # 测试
    result = controller.list_users()
    assert result == {"users": [{"id": 1, "name": "Test User"}]}
```

## 🎨 设计原则

### 1. 关注点分离

- **Core 层** - 提供通用的 IoC 能力（注入、注册、生命周期）
- **Service 层** - 专注于业务逻辑，使用 core 提供的能力
- **Controller 层** - 专注于 HTTP 路由，使用 core 提供的能力

### 2. 零耦合

Service 和 Controller 模块不与 core 耦合，它们只是：
- **使用** core 提供的装饰器和工具
- **注册** 自己为 core 的依赖提供者

```python
# service/registry.py
class ServiceRegistry:
    def __init__(self):
        # 注册自己为 core 的依赖提供者
        from cullinan.core import get_injection_registry
        injection_registry = get_injection_registry()
        injection_registry.add_provider_registry(self, priority=10)
```

### 3. 可扩展性

任何模块都可以注册为依赖提供者：

```python
# 自定义模块
class MyCustomRegistry:
    def get_instance(self, name):
        # 返回自定义对象
        return self._objects.get(name)

# 注册为依赖提供者
from cullinan.core import get_injection_registry
injection_registry = get_injection_registry()
injection_registry.add_provider_registry(my_registry, priority=20)

# 现在 InjectByName 可以从 MyCustomRegistry 获取依赖
```

## 🚀 最佳实践

### 1. Service 命名规范

使用 PascalCase 命名 Service 类：

```python
@service
class UserService(Service):  # ✓ 好
    pass

@service
class user_service(Service):  # ✗ 不推荐
    pass
```

### 2. 属性命名与自动推断

如果使用自动推断，属性名应该是 Service 类名的 snake_case：

```python
class UserController:
    user_service = InjectByName()  # ✓ 自动推断为 UserService
    email_service = InjectByName()  # ✓ 自动推断为 EmailService
    
    # 不匹配的命名需要显式指定
    my_user_svc = InjectByName('UserService')  # ✓ 显式指定
```

### 3. 避免循环依赖

```python
# ✗ 不要这样做
@service
class ServiceA(Service):
    service_b = InjectByName('ServiceB')

@service
class ServiceB(Service):
    service_a = InjectByName('ServiceA')  # 循环依赖！
```

解决方案：重构代码，提取共同依赖：

```python
# ✓ 好的做法
@service
class CommonService(Service):
    pass

@service
class ServiceA(Service):
    common = InjectByName('CommonService')

@service
class ServiceB(Service):
    common = InjectByName('CommonService')
```

### 4. Service 生命周期

```python
@service
class MyService(Service):
    def on_init(self):
        """初始化时调用（应用启动时）"""
        print("Service starting...")
        self.connection = self.connect_to_database()
    
    def on_destroy(self):
        """销毁时调用（应用关闭时）"""
        print("Service shutting down...")
        self.connection.close()
```

## 📊 与 Spring Boot 的对比

| 特性 | Spring Boot | Cullinan |
|------|------------|----------|
| 自动注册 | `@Service` | `@service` |
| 依赖注入 | `@Autowired` | `InjectByName()` |
| 无需 import | ✓ | ✓ |
| 自动初始化 | ✓ | ✓ |
| 生命周期管理 | `@PostConstruct`, `@PreDestroy` | `on_init()`, `on_destroy()` |
| 单例模式 | ✓ (默认) | ✓ |
| 延迟加载 | 可选 | ✓ (默认) |
| 类型安全 | ✓ | 运行时检查 |

## 🎉 总结

Cullinan 的自动依赖注入系统提供了：

1. ✅ **简单** - 只需要 `@service` 和 `InjectByName`
2. ✅ **强大** - 支持复杂的依赖链和生命周期管理
3. ✅ **优雅** - Controller 中完全不需要 import Service
4. ✅ **解耦** - 所有 IoC 能力在 core 层，上层模块无耦合
5. ✅ **可靠** - 自动管理初始化顺序，避免依赖问题
6. ✅ **高效** - 延迟加载 + 实例缓存，性能优秀

现在你可以像使用 Spring Boot 一样，享受自动依赖注入的便利！🚀

