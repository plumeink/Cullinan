# Cullinan 统一 DI 快速参考

## 基本用法

### Service 定义和注入

```python
from cullinan.service import service, Service
from cullinan.core import Inject, InjectByName

# 定义 Service
@service
class EmailService(Service):
    def send_email(self, to, subject, body):
        print(f"Email sent to {to}")

# 注入其他 Service
@service
class UserService(Service):
    # 方式1: 类型注入（推荐）
    email_service: EmailService = Inject()
    
    # 方式2: 字符串注入（无需 import）
    sms_service = InjectByName('SmsService')
    
    def create_user(self, user_data):
        self.email_service.send_email(user_data['email'], "Welcome", "...")
```

### Controller 定义和注入

```python
from cullinan.controller import controller, get_api, post_api
from cullinan.core import Inject

@controller(url='/api/users')
class UserController:
    # 注入 Service
    user_service: UserService = Inject()
    
    @get_api('')
    def list_users(self):
        users = self.user_service.get_all()
        return {'users': users}
    
    @post_api('')
    def create_user(self, body_params):
        user = self.user_service.create(body_params)
        return {'user': user}
```

## 高级用法

### 可选依赖

```python
from typing import Optional

@service
class LogService(Service):
    # 如果不存在，不会报错
    cache: Optional[Service] = Inject(name='CacheService', required=False)
    
    def log(self, message):
        if self.cache:
            self.cache.set(f"log:{time.time()}", message)
        print(message)
```

### 生命周期钩子

```python
@service
class DatabaseService(Service):
    def on_init(self):
        """实例创建后立即调用"""
        self.config = load_config()
    
    def on_startup(self):
        """应用启动时调用"""
        self.connection = create_connection()
    
    def on_shutdown(self):
        """应用关闭时调用"""
        self.connection.close()
```

### 初始化所有服务

```python
from cullinan.service import get_service_registry

# 在应用启动时
registry = get_service_registry()
registry.initialize_all()  # 同步版本

# 或异步版本
await registry.initialize_all_async()
```

## 注入方式对比

| 方式 | 语法 | 优点 | 缺点 |
|------|------|------|------|
| **类型注入** | `service: ServiceA = Inject()` | 类型安全，IDE 支持 | 需要 import |
| **字符串注入** | `service = InjectByName('ServiceA')` | 无需 import | 无类型检查 |
| **自动推断** | `service_a = InjectByName()` | 简洁 | 需遵循命名约定 |

## 常见问题

### Q: 如何解决循环依赖？
```python
# 不好：A -> B -> A
@service
class ServiceA:
    service_b: ServiceB = Inject()

@service
class ServiceB:
    service_a: ServiceA = Inject()  # 循环！

# 解决方案：重新设计架构或使用事件
```

### Q: 如何在测试中 Mock 依赖？
```python
# 测试代码
controller = UserController()
controller.user_service = MockUserService()  # 手动设置
```

### Q: 如何查看所有注册的服务？
```python
from cullinan.service import get_service_registry

registry = get_service_registry()
print(registry.list_all())  # ['EmailService', 'UserService', ...]
```

### Q: 如何启用调试日志？
```python
import logging

logging.getLogger('cullinan.core.injection').setLevel(logging.DEBUG)
logging.getLogger('cullinan.service.registry').setLevel(logging.DEBUG)
```

## 迁移指南

### 从旧方式迁移

**旧方式（不推荐）：**
```python
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
```

**新方式（推荐）：**
```python
@service
class UserService(Service):
    email_service: EmailService = Inject()
    # on_init 时依赖已注入完成
```

## 最佳实践

1. ✅ **优先使用类型注入** - 获得 IDE 支持和类型检查
2. ✅ **避免循环依赖** - 重新设计架构
3. ✅ **使用可选依赖** - 提高灵活性
4. ✅ **合理使用生命周期钩子** - on_init 用于快速初始化，on_startup 用于连接外部服务
5. ✅ **保持服务单一职责** - 每个服务专注一个功能

## 更多文档

- [完整架构文档](./UNIFIED_DI_ARCHITECTURE.md)
- [重构报告](../build/unified_di_refactor_report.md)
- [IoC/DI 用户指南](./IOC_USER_GUIDE.md)

