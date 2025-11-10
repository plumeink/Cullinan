# Cullinan v0.7.0 架构分析与实现 - 主文档

**[English](../ARCHITECTURE_MASTER.md)** | [中文](ARCHITECTURE_MASTER.md)

**状态**: ✅ 已实现  
**版本**: 0.7.0-alpha1  
**日期**: 2025年11月10日  
**文档目的**: 整合分析、设计决策和实现细节

---

## 目录

1. [执行摘要](#执行摘要)
2. [服务层分析](#服务层分析)
3. [注册表模式评估](#注册表模式评估)
4. [核心模块设计](#核心模块设计)
5. [实现细节](#实现细节)
6. [测试策略](#测试策略)
7. [迁移指南](#迁移指南)
8. [未来路线图](#未来路线图)

---

## 执行摘要

### 构建内容

Cullinan v0.7.0 代表了框架的完整架构重新设计，取得了以下关键成就：

**核心模块** (`cullinan.core`):
- ✅ 具有类型安全的基础 `Registry[T]` 模式
- ✅ 用于可选依赖管理的 `DependencyInjector`
- ✅ 具有初始化/清理钩子的 `LifecycleManager`
- ✅ 用于线程安全请求范围数据的 `RequestContext`

**增强服务层** (`cullinan.service`):
- ✅ 具有生命周期钩子的 `Service` 基类 (`on_init`, `on_destroy`)
- ✅ 具有依赖注入的 `ServiceRegistry`
- ✅ 具有依赖规范的 `@service` 装饰器
- ✅ 100% 向后兼容过渡

**WebSocket 集成** (`cullinan.websocket_registry`):
- ✅ 具有统一模式的 `WebSocketRegistry`
- ✅ `@websocket_handler` 装饰器
- ✅ WebSocket 处理程序的生命周期支持
- ✅ 与旧 `@websocket` 向后兼容

**文档和示例**:
- ✅ 更新了 v0.7.0 的 README.md
- ✅ 具有迁移指南的综合 CHANGELOG.md
- ✅ 新示例：展示所有功能的 `v070_demo.py`
- ✅ 整合分析文档（本文档）

### 设计理念

1. **轻量级 + 渐进式增强**: 默认简单，需要时强大
2. **显式优于隐式**: 清晰的注册和依赖声明
3. **模块化设计**: 每个模块都有清晰的边界和职责
4. **生产就绪**: 不仅仅是概念验证，为实际应用做好准备
5. **测试友好**: 易于模拟和隔离组件

### 关键决策

| 决策 | 理由 |
|----------|-----------|
| **保留服务层** | 提供清晰的关注点分离和可测试性 |
| **统一注册表** | 所有组件的一致模式 |
| **可选 DI** | 适用于复杂场景但不是必需的 |
| **生命周期钩子** | 适当的资源管理（初始化/清理）|
| **无向后兼容** | 干净的中断允许更好的架构 |

---

## 服务层分析

### 为什么保留服务层？

经过彻底分析，我们决定**保留和增强**服务层，原因如下：

#### 1. 清晰的关注点分离

```
控制器（HTTP）→ 服务（业务逻辑）→ DAO/模型（数据访问）
```

**好处**:
- 控制器专注于 HTTP 关注点（路由、验证、响应格式化）
- 服务包含可重用的业务逻辑
- 清晰的边界使代码更容易理解和维护

#### 2. 增强的可测试性

**没有服务层**:
```python
# 难以测试 - 与 HTTP 紧密耦合
@controller(url='/api')
class UserController:
    @post_api(url='/users')
    def create_user(self, body_params):
        # 业务逻辑与 HTTP 处理混合
        user = validate_user_data(body_params)
        db.save(user)
        return user
```

**有服务层**:
```python
# 易于测试 - 业务逻辑隔离
@service
class UserService(Service):
    def create_user(self, name, email):
        # 纯业务逻辑
        user = {'name': name, 'email': email}
        return self.user_dao.save(user)

# 测试不需要 HTTP
def test_create_user():
    service = UserService()
    user = service.create_user('Alice', 'alice@example.com')
    assert user['name'] == 'Alice'
```

#### 3. 代码重用

服务可以在多个控制器、后台作业、CLI 命令等中使用：

```python
@service
class EmailService(Service):
    def send_email(self, to, subject, body):
        # 电子邮件逻辑

# 在控制器中使用
@controller(url='/api')
class UserController:
    def __init__(self):
        self.email_service = get_service('EmailService')

# 在后台作业中使用
def send_daily_report():
    email_service = get_service('EmailService')
    email_service.send_email(...)

# 在 CLI 中使用
def cli_send_email():
    email_service = get_service('EmailService')
    email_service.send_email(...)
```

---

## 注册表模式评估

### 统一注册表设计

我们实现了一个**统一注册表模式**，适用于所有组件：

```python
# 基础注册表（通用）
class Registry[T]:
    def register(self, name: str, instance: T) -> None
    def get(self, name: str) -> T | None
    def get_all(self) -> dict[str, T]

# 服务注册表（专用）
class ServiceRegistry(Registry[Service]):
    # 添加了依赖注入
    # 添加了生命周期管理

# WebSocket 注册表（专用）
class WebSocketRegistry(Registry[WebSocketHandler]):
    # 添加了 URL 路由
    # 添加了连接管理
```

**好处**:
1. **一致性**: 所有组件遵循相同的模式
2. **可预测性**: 开发人员知道会发生什么
3. **可扩展性**: 易于添加新的注册表类型
4. **类型安全**: 使用 Python 的类型提示

---

## 核心模块设计

### 架构概览

```
cullinan/
├── core/                    # 核心基础设施
│   ├── registry.py         # 基础注册表模式
│   ├── injection.py        # 依赖注入引擎
│   ├── lifecycle.py        # 生命周期管理
│   └── context.py          # 请求上下文
├── service/                 # 增强服务层
│   ├── base.py             # Service 基类
│   ├── registry.py         # ServiceRegistry
│   └── decorators.py       # @service 装饰器
└── websocket_registry.py    # WebSocket 集成
```

### 组件说明

#### 1. Registry（注册表）

通用注册表模式，用于管理组件：

```python
from cullinan.core import Registry

class MyRegistry(Registry[MyComponent]):
    pass

registry = MyRegistry()
registry.register('component1', MyComponent())
component = registry.get('component1')
```

#### 2. DependencyInjector（依赖注入器）

可选的依赖管理：

```python
from cullinan.core import DependencyInjector

injector = DependencyInjector()
injector.register('db', DatabaseConnection())
injector.register('cache', RedisCache(depends_on=['db']))

# 自动解析依赖
injector.resolve_dependencies()
```

#### 3. LifecycleManager（生命周期管理器）

管理组件初始化和清理：

```python
from cullinan.core import LifecycleManager

manager = LifecycleManager()
manager.register(service1)
manager.register(service2)

# 初始化所有组件
manager.initialize_all()

# 清理所有组件
manager.destroy_all()
```

#### 4. RequestContext（请求上下文）

线程安全的请求范围数据：

```python
from cullinan.core import create_context, get_current_context

with create_context():
    ctx = get_current_context()
    ctx.set('user_id', 123)
    ctx.set('request_id', 'abc-123')
    # 自动清理
```

---

## 实现细节

### 服务层实现

```python
from cullinan import service, Service

@service(dependencies=['EmailService', 'UserDAO'])
class UserService(Service):
    def on_init(self):
        """在服务初始化时调用"""
        self.email = self.dependencies['EmailService']
        self.user_dao = self.dependencies['UserDAO']
        
    def on_destroy(self):
        """在服务清理时调用"""
        pass
        
    def create_user(self, name, email):
        """业务逻辑方法"""
        user = self.user_dao.create(name, email)
        self.email.send_welcome(email)
        return user
```

### WebSocket 实现

```python
from cullinan import websocket_handler

@websocket_handler(url='/ws/chat')
class ChatHandler:
    def on_init(self):
        """在处理程序初始化时调用"""
        self.connections = set()
    
    def on_open(self):
        """WebSocket 连接打开时"""
        self.connections.add(self)
    
    def on_message(self, message):
        """接收消息时"""
        for conn in self.connections:
            conn.write_message(message)
    
    def on_close(self):
        """连接关闭时"""
        self.connections.discard(self)
```

---

## 测试策略

### 单元测试

```python
from cullinan.testing import TestRegistry, MockService

def test_user_service():
    # 创建测试注册表
    registry = TestRegistry()
    
    # 添加模拟服务
    mock_email = MockService('EmailService')
    registry.register_service('EmailService', mock_email)
    
    # 测试服务
    user_service = UserService()
    user = user_service.create_user('Alice', 'alice@example.com')
    
    assert user['name'] == 'Alice'
    assert mock_email.was_called('send_welcome')
```

### 集成测试

```python
def test_full_stack():
    # 使用真实服务
    app = create_app()
    
    response = app.post('/api/users', {
        'name': 'Alice',
        'email': 'alice@example.com'
    })
    
    assert response.status == 200
    assert response.json['name'] == 'Alice'
```

---

## 迁移指南

### 从 v0.6.x 升级到 v0.7.0

#### 1. 导入更改

```python
# v0.6.x
from cullinan.service import service, Service

# v0.7.0
from cullinan import service, Service
```

#### 2. 服务声明

```python
# v0.6.x
@service
class UserService(Service):
    pass

# v0.7.0（可选增强）
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
```

#### 3. WebSocket

```python
# v0.6.x
@websocket(url='/ws/chat')
class ChatHandler:
    pass

# v0.7.0（推荐）
@websocket_handler(url='/ws/chat')
class ChatHandler:
    def on_init(self):
        # 初始化逻辑
        pass
```

---

## 未来路线图

### v0.7.x（短期）

- [ ] 更多生命周期钩子 (`on_request`, `on_response`)
- [ ] 性能优化
- [ ] 额外的中间件
- [ ] 改进的文档

### v0.8.0（中期）

- [ ] 移除已弃用的 API
- [ ] 高级作用域（singleton、request、transient）
- [ ] 服务网格集成
- [ ] GraphQL 支持

### v1.0.0（长期）

- [ ] 稳定的 API 保证
- [ ] 完全 async/await 支持
- [ ] 云原生功能
- [ ] 微服务工具

---

## 资源

- **主 README**: [../../README.MD](../../README.MD)
- **CHANGELOG**: [../../CHANGELOG.md](../../CHANGELOG.md)
- **示例**: [../../examples/v070_demo.py](../../examples/v070_demo.py)
- **源代码**: [../../cullinan/](../../cullinan/)

---

**最后更新**: 2025年11月10日  
**状态**: 实现完成  
**维护者**: Cullinan 开发团队
