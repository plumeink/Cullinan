# Cullinan 统一 DI 架构设计

## 概览

Cullinan 框架采用类似 Spring 的统一依赖注入（DI）架构，所有组件（Service、Controller）都使用 `cullinan.core` 作为唯一的 IoC/DI 容器。

## 架构设计

### 核心组件

```
┌─────────────────────────────────────────────────┐
│          cullinan.core (IoC/DI 容器)             │
│  - InjectionRegistry (依赖注入注册表)             │
│  - @injectable (可注入标记装饰器)                 │
│  - Inject() / InjectByName() (注入描述符)        │
└─────────────────────────────────────────────────┘
                        ▲
                        │ 注册为 provider
        ┌───────────────┴───────────────┐
        │                               │
┌───────┴────────┐             ┌───────┴────────┐
│ ServiceRegistry│             │ControllerReg   │
│  (Provider)    │             │  (Provider)    │
│  - Service实例 │             │  - Controller  │
│  - 生命周期管理 │             │    实例        │
└────────────────┘             └────────────────┘
        ▲                               ▲
        │ @service                      │ @controller
        │                               │
┌───────┴────────┐             ┌───────┴────────┐
│  Service 类    │             │  Controller类  │
│  - @service    │────注入─────>│  - @controller │
│  - 业务逻辑    │             │  - 路由处理    │
└────────────────┘             └────────────────┘
```

## 关键设计原则

### 1. 单一注册系统

**所有依赖注入都通过 `cullinan.core.InjectionRegistry` 管理**

- ✅ `ServiceRegistry` 和 `ControllerRegistry` 作为 **provider** 注册到 `InjectionRegistry`
- ✅ 不再使用 legacy `DependencyInjector`
- ✅ Service 和 Controller 都使用 `@injectable` 标记

### 2. 装饰器统一

**`@service` 和 `@controller` 都调用 `@injectable`**

```python
@service
class EmailService(Service):
    pass

# 等价于：
@injectable
class EmailService(Service):
    pass
# + 注册到 ServiceRegistry
```

### 3. 依赖注入方式

**推荐使用类型注入（类似 Spring @Autowired）**

```python
from cullinan.core import Inject, InjectByName

@service
class UserService(Service):
    # 方式1: 类型注入（推荐）
    email_service: EmailService = Inject()
    
    # 方式2: 字符串注入（无需 import）
    sms_service = InjectByName('SmsService')
    
    def create_user(self, user_data):
        self.email_service.send_welcome_email(...)
```

### 4. Provider 机制

**ServiceRegistry 和 ControllerRegistry 作为 provider**

```python
# ServiceRegistry.__init__
injection_registry = get_injection_registry()
injection_registry.add_provider_registry(self, priority=10)

# 当注入依赖时
# InjectionRegistry._resolve_dependency() 会调用：
# ServiceRegistry.get_instance(name) -> Service 实例
```

## 工作流程

### Service 注册和注入流程

```python
# 1. 定义 Service
@service
class EmailService(Service):
    def send_email(self, to, subject, body):
        print(f"Sending email to {to}")

# 2. @service 装饰器执行
#    a. 调用 @injectable -> 扫描类的 Inject/InjectByName
#    b. 注册到 ServiceRegistry
#    c. ServiceRegistry 已注册为 InjectionRegistry 的 provider

# 3. 在其他组件中使用
@service
class UserService(Service):
    email_service: EmailService = Inject()  # 类型注入
    
    def register_user(self, user):
        # 当首次访问 self.email_service 时：
        # -> Inject.__get__() 被调用
        # -> InjectionRegistry._resolve_dependency('EmailService')
        # -> ServiceRegistry.get_instance('EmailService')
        # -> 创建 EmailService 实例（如果不存在）
        # -> 返回实例并缓存
        self.email_service.send_email(...)
```

### Controller 注入 Service 流程

```python
# 1. 定义 Controller
@controller(url='/api/users')
class UserController:
    user_service: UserService = Inject()  # 注入 Service
    
    @get_api('')
    def list_users(self):
        users = self.user_service.get_all()
        return {'users': users}

# 2. @controller 装饰器执行
#    a. 调用 @injectable -> 扫描 Inject/InjectByName
#    b. 注册到 ControllerRegistry
#    c. 注册路由和 HTTP 方法

# 3. 处理请求时
#    a. Tornado 路由匹配到 UserController
#    b. 创建 UserController 实例
#    c. @injectable 包装的 __init__ 执行
#    d. 自动注入 user_service
#    e. 调用 list_users() 方法
```

## 与 Spring 的对比

| 功能 | Spring | Cullinan |
|------|--------|----------|
| IoC 容器 | ApplicationContext | InjectionRegistry |
| 服务注册 | @Service | @service + @injectable |
| 控制器注册 | @Controller | @controller + @injectable |
| 依赖注入 | @Autowired | Inject() / InjectByName() |
| 作用域 | @Scope | Singleton (默认) |
| 生命周期 | @PostConstruct | on_init() |
| 启动 | @EventListener | on_startup() |
| Provider | BeanFactory | ServiceRegistry/ControllerRegistry |

## 迁移指南

### 从 legacy DependencyInjector 迁移

**之前（不推荐）：**
```python
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
```

**现在（推荐）：**
```python
@service
class UserService(Service):
    email_service: EmailService = Inject()
    
    # on_init 中依赖已经自动注入完成
    def on_init(self):
        # self.email_service 已经可用
        pass
```

### Controller 注入

**推荐方式：**
```python
from cullinan.core import Inject, InjectByName

@controller(url='/api/users')
class UserController:
    # 方式1: 类型注入
    user_service: UserService = Inject()
    
    # 方式2: 字符串注入（无需 import Service）
    auth_service = InjectByName('AuthService')
    
    @get_api('')
    def list_users(self):
        return self.user_service.get_all()
```

## 优势

### 1. 统一性
- 所有组件使用相同的 DI 系统
- 一致的注入语法和行为
- 易于理解和维护

### 2. 解耦
- Service 不依赖 ServiceRegistry
- Controller 不依赖 ControllerRegistry
- 组件之间通过 core DI 系统通信

### 3. 可测试性
- 支持 Mock 注入
- 可以手动设置依赖
```python
controller = UserController()
controller.user_service = MockUserService()  # Mock 注入
```

### 4. 延迟加载
- 依赖在首次访问时才解析
- 避免循环依赖问题
- 提高启动性能

### 5. 类型安全
- 支持类型注解
- IDE 自动补全
- 静态类型检查

## 最佳实践

### 1. 优先使用类型注入
```python
# 好
user_service: UserService = Inject()

# 也可以（无需 import）
user_service = InjectByName('UserService')
```

### 2. 避免循环依赖
```python
# 不好：A -> B -> A
@service
class ServiceA:
    service_b: ServiceB = Inject()

@service
class ServiceB:
    service_a: ServiceA = Inject()  # 循环依赖！

# 解决方案：重新设计或使用事件
```

### 3. 使用可选依赖
```python
@service
class UserService:
    # 如果 CacheService 不存在，不会抛出异常
    cache: Optional[CacheService] = Inject(required=False)
    
    def get_user(self, id):
        if self.cache:
            return self.cache.get(f"user:{id}")
        return self.db.get_user(id)
```

### 4. 合理使用生命周期钩子
```python
@service
class DatabaseService:
    def on_init(self):
        """快速初始化（同步）"""
        self.config = load_config()
    
    def on_startup(self):
        """启动阶段（连接外部服务）"""
        self.connection = create_connection()
    
    def on_shutdown(self):
        """优雅关闭"""
        self.connection.close()
```

## 调试技巧

### 1. 查看注册的服务
```python
from cullinan.core import get_injection_registry
from cullinan.service import get_service_registry

injection_registry = get_injection_registry()
service_registry = get_service_registry()

# 查看所有注册的服务类
print(service_registry.list_all())

# 查看某个类的注入信息
print(injection_registry.get_injection_info(UserService))
```

### 2. 启用调试日志
```python
import logging

# 启用 core 和 service 的调试日志
logging.getLogger('cullinan.core.injection').setLevel(logging.DEBUG)
logging.getLogger('cullinan.service.registry').setLevel(logging.DEBUG)
```

### 3. 检查循环依赖
```python
# 如果出现 CircularDependencyError，检查日志
# 日志会显示依赖链：ServiceA -> ServiceB -> ServiceA
```

## 总结

Cullinan 的统一 DI 架构提供了：

1. ✅ **单一职责**：`cullinan.core` 是唯一的 IoC 容器
2. ✅ **解耦设计**：组件通过 DI 系统通信，不直接依赖
3. ✅ **类 Spring**：熟悉的编程模型和概念
4. ✅ **可扩展**：易于添加新的 Provider
5. ✅ **高性能**：延迟加载、缓存、O(1) 查找

通过这个架构，Cullinan 实现了现代 Python Web 框架应有的依赖注入能力，同时保持了简洁和高性能。

