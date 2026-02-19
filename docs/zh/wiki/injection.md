title: "IoC 与 DI（注入）"
slug: "injection"
module: ["cullinan.core"]
tags: ["ioc", "di", "injection"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/wiki/injection.md"
related_tests: ["tests/test_core_injection.py"]
related_examples: ["examples/ioc_facade_demo.py"]
estimate_pd: 2.0
last_updated: "2025-12-26T00:00:00Z"
pr_links: []

# IoC 与 DI（注入）

> **版本**: v0.90  
> **作者**: Plumeink

本文档介绍 Cullinan 的 IoC（控制反转）与 DI（依赖注入）系统。完整架构概览请参阅 [架构设计](../architecture.md)。从旧版本迁移请参阅 [迁移指南](../migration_guide.md)。

## 核心概念

### 控制反转 (IoC)

IoC 是一种设计原则，将对象创建和生命周期的控制权从应用程序代码转移给框架或容器。

### 依赖注入 (DI)

DI 是实现 IoC 的一种技术。依赖项被"注入"到类中，而不是由类自己创建。

## 推荐用法（基于装饰器）

### 1. 定义服务

```python
from cullinan.service import service, Service

@service
class DatabaseService(Service):
    def __init__(self):
        super().__init__()
        self.connection = None
    
    def on_startup(self):
        """服务启动时调用"""
        self.connection = create_connection()
    
    def on_shutdown(self):
        """服务关闭时调用"""
        if self.connection:
            self.connection.close()
    
    def query(self, sql: str):
        return self.connection.execute(sql)
```

### 2. 注入依赖

```python
from cullinan.service import service, Service
from cullinan.core import Inject

@service
class UserService(Service):
    # 通过类型注解自动注入
    database: DatabaseService = Inject()
    
    def get_user(self, user_id: int):
        return self.database.query(f"SELECT * FROM users WHERE id={user_id}")
```

### 3. 在控制器中使用

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject
from cullinan.params import Path

@controller(url='/api/users')
class UserController:
    user_service: UserService = Inject()
    
    @get_api(url='/{user_id}')
    async def get_user(self, user_id: int = Path()):
        return self.user_service.get_user(user_id)
```

## 注入方式

### Inject() - 类型注解注入（推荐）

最佳的 IDE 支持和类型安全。

```python
from cullinan.core import Inject

@service
class MyService(Service):
    # 从类型注解推断依赖名称
    database: DatabaseService = Inject()
    
    # 可选依赖
    cache: CacheService = Inject(required=False)
```

### InjectByName() - 字符串名称注入

无需导入依赖类，可避免循环导入。

```python
from cullinan.controller import controller
from cullinan.core import InjectByName

@controller(url='/api')
class MyController:
    # 显式指定名称
    user_service = InjectByName('UserService')
    
    # 自动推断名称 (snake_case -> PascalCase)
    email_service = InjectByName()  # -> EmailService
```

## 生命周期钩子

服务支持用于初始化和清理的生命周期钩子（Duck Typing - 无需继承基类）：

```python
@service
class MyService(Service):
    def get_phase(self) -> int:
        """初始化顺序（数值越小越早）"""
        return 0
    
    def on_post_construct(self):
        """依赖注入完成后调用"""
        pass
    
    def on_startup(self):
        """应用启动时调用"""
        pass
    
    def on_shutdown(self):
        """应用关闭时调用"""
        pass
    
    def on_pre_destroy(self):
        """销毁前调用"""
        pass
```

## 高级用法：ApplicationContext（复杂场景）

用于第三方集成或自定义工厂等高级用例：

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

ctx = ApplicationContext()

ctx.register(Definition(
    name='CustomService',
    factory=lambda c: CustomService(c.get('Dependency')),
    scope=ScopeType.SINGLETON,
    source='custom:CustomService'
))

ctx.refresh()  # 冻结注册表
service = ctx.get('CustomService')
```

## 最佳实践

1. **为服务和控制器使用装饰器** - 让框架处理注册
2. **使用 `Inject()` 进行类型安全注入** - 更好的 IDE 支持和重构能力
3. **使用 `InjectByName()` 避免循环导入** - 当无法导入类型时使用
4. **正确实现生命周期钩子** - 干净的初始化和关闭
5. **保持服务职责单一** - 单一职责原则

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 依赖为 None | 确保服务使用 `@service` 装饰器 |
| 找不到服务 | 检查服务名称是否匹配（区分大小写） |
| 循环依赖 | 使用 `InjectByName()` 进行延迟解析 |
| 注入不生效 | 确保类继承自 `Service` 或 `Controller` |

## 另请参阅

- [架构设计](../architecture.md) - 系统架构概览
- [装饰器](decorators.md) - 所有可用的装饰器
- [生命周期](lifecycle.md) - 服务生命周期管理
- [迁移指南](../migration_guide.md) - 从旧版本迁移
