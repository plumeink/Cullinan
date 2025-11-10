```python
# 之前（v0.6x）
from cullinan.service import service, Service

# 之后（v0.7x）
from cullinan import service, Service
```

#### 步骤 2：添加依赖（可选）

```python
# 之前 - 手动依赖管理
@service
class UserService(Service):
    def create_user(self, name):
        email_service = service_list.get('EmailService')
        email_service.send_email(name, "欢迎", "欢迎！")

# 之后 - 自动依赖注入
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name):
        self.email.send_email(name, "欢迎", "欢迎！")
```

#### 步骤 3：添加生命周期钩子（可选）

```python
@service
class DatabaseService(Service):
    def on_init(self):
        """服务创建后调用"""
        self.connection = self.connect_to_database()
    
    def on_destroy(self):
        """服务关闭时调用"""
        self.connection.close()
    
    def connect_to_database(self):
        return "DB_CONNECTION"
```

### 路径 3：完全迁移（使用所有功能）

对于新项目或大型重构，使用所有增强功能。

```python
from cullinan import service, Service

@service(dependencies=['EmailService', 'DatabaseService'])
class UserService(Service):
    def on_init(self):
        """初始化依赖"""
        self.email = self.dependencies['EmailService']
        self.db = self.dependencies['DatabaseService']
        print("UserService 已初始化")
    
    def on_destroy(self):
        """清理资源"""
        print("UserService 正在关闭")
    
    def create_user(self, name, email_addr):
        # 使用注入的依赖
        user = {'name': name, 'email': email_addr}
        self.db.save(user)
        self.email.send_email(email_addr, "欢迎", "欢迎加入！")
        return user
```

## 详细的迁移步骤

### 1. 更新导入

所有服务导入都应该从 `cullinan` 主包导入，而不是从 `cullinan.service`：

**旧的导入（仍然有效但已弃用）**：
```python
from cullinan.service import service, Service, service_list
```

**新的导入（推荐）**：
```python
from cullinan import service, Service
from cullinan import get_service_registry  # 替代 service_list
```

### 2. 添加依赖声明

如果您的服务依赖其他服务，使用 `dependencies` 参数声明它们：

**之前**：
```python
@service
class OrderService(Service):
    def process_order(self, order_data):
        # 手动查找 - 容易出错
        email_service = service_list.get('EmailService')
        payment_service = service_list.get('PaymentService')
        
        if email_service and payment_service:
            # 处理订单...
            pass
```

**之后**：
```python
@service(dependencies=['EmailService', 'PaymentService'])
class OrderService(Service):
    def on_init(self):
        # 依赖自动注入
        self.email = self.dependencies['EmailService']
        self.payment = self.dependencies['PaymentService']
    
    def process_order(self, order_data):
        # 安全使用依赖
        self.payment.charge(order_data['amount'])
        self.email.send_confirmation(order_data['email'])
```

### 3. 实现生命周期钩子

利用生命周期钩子进行适当的资源管理：

```python
@service
class CacheService(Service):
    def on_init(self):
        """服务创建时初始化"""
        self.cache = {}
        self.connection_pool = self._create_pool()
        print("缓存服务已启动")
    
    def on_destroy(self):
        """应用关闭时清理"""
        self.cache.clear()
        self.connection_pool.close()
        print("缓存服务已关闭")
    
    def _create_pool(self):
        # 创建连接池
        return ConnectionPool(size=10)
```

### 4. 更新控制器服务访问

控制器访问服务的方式没有变化：

```python
from cullinan import controller, post_api

@controller(url='/api')
class UserController:
    @post_api(url='/users')
    def create_user(self, body_params):
        # 服务访问保持不变
        user = self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
        return self.response_build(status=201, data=user)
```

### 5. 更新 WebSocket 处理程序（推荐）

虽然旧的 `@websocket` 装饰器仍然有效，但新的 `@websocket_handler` 提供生命周期支持：

**之前**：
```python
from cullinan.websocket import websocket

@websocket(url='/ws/chat')
class ChatHandler:
    def on_open(self):
        print("连接打开")
```

**之后（推荐）**：
```python
from cullinan import websocket_handler

@websocket_handler(url='/ws/chat')
class ChatHandler:
    def on_init(self):
        """处理程序注册时调用"""
        self.connections = set()
        print("聊天处理程序已初始化")
    
    def on_open(self):
        """连接打开时调用"""
        self.connections.add(self)
    
    def on_close(self):
        """连接关闭时调用"""
        self.connections.discard(self)
```

## 测试迁移

### 旧的测试方式

```python
def test_user_service():
    # 手动设置
    service = UserService()
    # 测试...
```

### 新的测试方式

```python
from cullinan.testing import TestRegistry, MockService

def test_user_service():
    # 创建隔离的测试注册表
    registry = TestRegistry()
    
    # 注册模拟依赖
    email_mock = MockService()
    registry.register_mock('EmailService', email_mock)
    
    # 使用模拟依赖测试服务
    user_service = UserService()
    registry.inject_dependencies(user_service, ['EmailService'])
    
    # 运行测试
    user = user_service.create_user('张三', 'zhang@example.com')
    
    # 验证
    assert user['name'] == '张三'
    assert email_mock.send_email.called
```

## 常见问题解答

### Q: 我需要立即迁移所有服务吗？

**A:** 不需要。迁移是可选的和渐进的。您可以：
- 保持现有服务不变
- 仅在新服务中使用新功能
- 随着时间逐步迁移旧服务

### Q: 旧的导入 `from cullinan.service import ...` 还能用吗？

**A:** 不能。在 v0.7x 中，旧的 `cullinan.service` 模块已被移除。所有服务都应该使用从 `cullinan` 根包导入的新 API。

### Q: `service_list` 发生了什么变化？

**A:** 它已在 v0.7x 中移除。增强的服务层现在位于 `cullinan/service/` 中，并通过主 `cullinan` 包导出。使用 `get_service_registry()` 代替。

### Q: 如何测试有依赖的服务？

**A:** 使用 `cullinan.testing` 中的 `TestRegistry` 和 `MockService`：

```python
from cullinan.testing import TestRegistry, MockService

registry = TestRegistry()
registry.register_mock('EmailService', MockService())
user_service = registry.get('UserService')
```

### Q: 生命周期钩子在什么时候调用？

**A:**
- `on_init()`: 服务首次创建后（单例模式）
- `on_destroy()`: 应用关闭时（清理资源）

### Q: 我可以在现有项目中混用旧式和新式服务吗？

**A:** 不能。v0.7x 移除了旧的 `cullinan.service` 模块。所有服务都必须使用新的导入方式：`from cullinan import service, Service`。

### Q: 依赖注入是必需的吗？

**A:** 不是。依赖注入是可选的。您可以：
- 使用 `@service` 而不带 `dependencies` 参数（简单服务）
- 使用 `@service(dependencies=[...])` （需要依赖注入时）

### Q: 如何访问请求上下文？

**A:** 使用请求上下文工具：

```python
from cullinan import get_current_context, create_context

# 在请求处理程序中
with create_context():
    ctx = get_current_context()
    ctx.set('user_id', 123)
    ctx.set('request_id', 'abc-123')
    # 退出时上下文自动清理
```

## 迁移检查清单

使用此检查清单跟踪您的迁移进度：

- [ ] 将所有 `from cullinan.service import ...` 更新为 `from cullinan import ...`
- [ ] 识别具有依赖的服务并添加 `dependencies` 参数
- [ ] 为需要的服务实现 `on_init()` 钩子
- [ ] 为需要清理的服务实现 `on_destroy()` 钩子
- [ ] 将 WebSocket 处理程序更新为 `@websocket_handler`（可选）
- [ ] 使用 `TestRegistry` 和 `MockService` 更新测试
- [ ] 将 `service_list` 的使用替换为 `get_service_registry()`
- [ ] 测试所有迁移的组件
- [ ] 更新文档和注释

## 获取帮助

如果您在迁移过程中遇到问题：

1. 查看 **[架构指南](ARCHITECTURE_MASTER.md)** 以获取详细信息
2. 研究 **[示例应用](../examples/v070_demo.py)** 以获取实际用法
3. 查看 **[CHANGELOG](../CHANGELOG.md)** 以了解所有更改
4. 在 GitHub 上提出问题

## 总结

迁移到增强的服务层：

✅ **可选** - 现有代码无需更改即可工作  
✅ **渐进式** - 逐步迁移服务  
✅ **强大** - 获得依赖注入 + 生命周期管理  
✅ **可测试** - 使用模拟和测试注册表更容易测试  
✅ **面向未来** - 为未来的增强做好准备  

从小处开始，逐步采用新功能，并充分利用增强的架构！

---

**文档版本**: 1.0  
**最后更新**: 2025年11月11日  
**维护者**: Cullinan 开发团队
# 迁移指南：增强的服务层

## 概述

本指南帮助您从基本服务层迁移到具有依赖注入和生命周期管理的增强服务层。

## 关键要点

✅ **100% 向后兼容** - 所有现有代码继续工作  
✅ **可选增强** - 仅在需要时使用新功能  
✅ **无破坏性更改** - 现有的 `@service` 装饰器仍然有效  

## 有什么新功能？

### 核心模块 (`cullinan.core`)
- 所有注册表的基础注册表模式
- 依赖注入引擎
- 生命周期管理（on_init、on_destroy）
- 类型安全的异常层次结构

### 增强的服务层 (`cullinan.service`)
- 具有生命周期钩子的服务基类
- 具有依赖注入的 ServiceRegistry
- 增强的 @service 装饰器，带有依赖参数
- 单例实例管理

### 测试工具 (`cullinan.testing`)
- MockService 用于简单的测试模拟
- TestRegistry 用于隔离测试
- ServiceTestCase 和 IsolatedServiceTestCase 固件

## 迁移路径

### 路径 1：无需迁移（继续使用基本服务）

如果您的服务很简单且不需要依赖注入，**无需更改**。

```python
# 旧代码（仍然完美工作）
from cullinan.service import service, Service

@service
class EmailService(Service):
    def send_email(self, to, subject, body):
        print(f"发送到 {to}: {subject}")
```

### 路径 2：渐进式迁移（添加增强功能）

逐个服务迁移，仅在有益的地方添加新功能。

#### 步骤 1：从新模块导入


