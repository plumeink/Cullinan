# 常见问题解答 (FAQ)

## 通用问题

### Cullinan 是什么？

Cullinan 是一个基于 Tornado 构建的 Python Web 框架，灵感来自 Spring Boot。它提供依赖注入、生命周期管理和清晰的架构，用于构建 Web 应用和 API。

### 为什么选择 Cullinan 而不是 Flask/Django/FastAPI？

**Cullinan 提供**：
- Spring Boot 风格的依赖注入
- 内置生命周期管理
- 高性能（基于 Tornado）
- 清晰的关注点分离（Controller/Service/Repository）
- 开箱即用的 WebSocket 支持

**选择 Cullinan 如果**：
- 您喜欢 Spring Boot 并希望在 Python 中使用类似模式
- 您需要在一个框架中同时支持 HTTP 和 WebSocket
- 您想要强大的架构模式

## 安装和设置

### 如何安装 Cullinan？

```bash
pip install path/to/Cullinan
```

或以开发模式：
```bash
cd path/to/Cullinan
pip install -e .
```

### 最低要求是什么？

- Python 3.8 或更高版本
- Tornado（自动安装）

### 如何配置服务器端口？

创建 `.env` 文件：
```env
SERVER_PORT=4080
```

或设置环境变量：
```bash
export SERVER_PORT=8080
python app.py
```

## 依赖注入

### 我需要导入 Service 类吗？

**不需要！** 使用字符串类型注解：

```python
from cullinan.core import Inject

@controller(url='/api')
class MyController:
    # 无需 import！
    my_service: 'MyService' = Inject()
```

### 为什么注入的服务仍然是 `Inject` 对象？

**问题**：您忘记了类型注解。

```python
# ✗ 错误 - 没有类型注解
my_service = Inject(name='MyService')

# ✓ 正确 - 有类型注解
my_service: 'MyService' = Inject()
```

### 可以将服务注入到服务中吗？

**可以！** 服务可以依赖其他服务：

```python
@service
class UserService(Service):
    database: 'DatabaseService' = Inject()
    email: 'EmailService' = Inject()
```

### 循环依赖如何工作？

Cullinan 使用**延迟加载**处理循环依赖：

```python
@service
class ServiceA(Service):
    service_b: 'ServiceB' = Inject()  # 延迟加载

@service
class ServiceB(Service):
    service_a: 'ServiceA' = Inject()  # 延迟加载
```

## 生命周期管理

### `on_startup()` 何时被调用？

**在 Web 服务器启动之前**。这确保您的服务在接受请求之前完全初始化。

### 为什么我的 `on_startup()` 没有被调用？

确保您使用标准的 `application.run()` 函数：

```python
from cullinan import application

if __name__ == '__main__':
    application.run()  # 这会触发生命周期
```

### `on_post_construct()` 和 `on_startup()` 有什么区别？

- **`on_post_construct()`**：快速初始化（依赖注入后）
- **`on_startup()`**：可以耗时（连接数据库、登录 bot 等）

```python
@service
class BotService(Service):
    def on_post_construct(self):
        # 快速：创建客户端对象
        self._client = discord.Client()
    
    def on_startup(self):
        # 慢速：登录并等待就绪
        self.initialize_bot(token)
```

### 如何控制启动顺序？

使用 `get_phase()`：

```python
@service
class DatabaseService(Service):
    def get_phase(self) -> int:
        return -100  # 早启动

@service
class BotService(Service):
    def get_phase(self) -> int:
        return -50  # 在数据库之后启动

@service
class UserService(Service):
    # 默认 phase = 0，最后启动
    pass
```

**较小的 phase 数字 = 更早启动**

## 控制器

### 如何捕获路径参数？

使用正则表达式组：

```python
@get_api(url='/users/([0-9]+)')
def get_user(self, user_id):
    # user_id 将是捕获的数字
    pass

@get_api(url='/posts/([a-z]+)/comments/([0-9]+)')
def get_comment(self, post_slug, comment_id):
    # 多个参数
    pass
```

### 如何获取查询参数？

```python
@get_api(url='/users')
def list_users(self, query_params):
    page = query_params.get('page', 1)
    limit = query_params.get('limit', 10)
    return {'users': [...]}
```

调用：`GET /users?page=2&limit=20`

### 如何获取请求体？

```python
@post_api(url='/users')
def create_user(self, body_params):
    name = body_params.get('name')
    email = body_params.get('email')
    return {'created': True}
```

### 如何获取请求头？

```python
@get_api(url='/protected', headers=['Authorization'])
def protected_route(self, query_params, headers):
    token = headers.get('Authorization')
    # 验证 token...
```

### 可以返回不同的状态码吗？

```python
from cullinan.controller import get_api

@get_api(url='/users/([0-9]+)')
def get_user(self, user_id):
    user = self.user_service.get(user_id)
    
    if not user:
        self.set_status(404)
        return {'error': '未找到用户'}
    
    return {'user': user}
```

## 服务

### Service 和 Controller 有什么区别？

- **Controller**：处理 HTTP 请求、验证输入、返回响应
- **Service**：包含业务逻辑，独立于 HTTP

```python
# Controller - HTTP 关注点
@controller(url='/api/users')
class UserController:
    user_service: 'UserService' = Inject()
    
    @post_api(url='')
    def create(self, body_params):
        # 验证 HTTP 输入
        if not body_params.get('email'):
            return {'error': '邮箱为必填项'}
        
        # 调用服务
        user = self.user_service.create(body_params)
        return {'user': user}

# Service - 业务逻辑
@service
class UserService(Service):
    def create(self, data):
        # 业务规则
        # 数据库操作
        return user
```

## WebSocket

### 如何创建 WebSocket 处理器？

```python
from cullinan.websocket_registry import websocket_handler

@websocket_handler(url='/ws/chat')
class ChatWebSocket:
    def on_open(self):
        print("客户端已连接")
    
    def on_message(self, message):
        self.write_message(f"回声：{message}")
    
    def on_close(self):
        print("客户端已断开")
```

### WebSocket 中可以使用依赖注入吗？

**可以！**

```python
@websocket_handler(url='/ws/notifications')
class NotificationWebSocket:
    user_service: 'UserService' = Inject()
    
    def on_open(self):
        users = self.user_service.get_all()
        self.write_message({'users': users})
```

## 错误和调试

### 我遇到 "Service not found" 错误

**解决方案**：确保 Service 已注册：

```python
# 导入 service 以使 @service 装饰器运行
from services.my_service import MyService

# 或在 __init__.py 中导入
```

### 我的更改没有生效

**解决方案**：重启服务器。Cullinan 在生产模式下没有自动重载。

对于开发，您可以使用：
```bash
# 使用 watchdog 或类似工具进行自动重载
watchmedo auto-restart -p "*.py" -- python app.py
```

### 如何启用调试日志？

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 性能

### Cullinan 快吗？

是的！基于 Tornado 的异步 I/O：
- 处理数千个并发连接
- 非阻塞 I/O
- 高效的 WebSocket 支持

### 我应该使用 async/await 吗？

当您有 I/O 操作时使用 async：

```python
@service
class DatabaseService(Service):
    async def on_startup_async(self):
        # 异步 I/O
        await self.connect()
    
    async def query(self, sql):
        # 异步查询
        return await self.execute(sql)
```

对于 CPU 密集或简单操作使用同步：

```python
@service
class UserService(Service):
    def validate_email(self, email):
        # 简单验证 - 同步即可
        return '@' in email
```

## 部署

### 如何在生产环境运行？

```bash
# 设置生产环境
export SERVER_PORT=80
export SERVER_THREAD=4  # 使用多个工作进程

# 运行
python app.py
```

### 可以使用 Gunicorn/uWSGI 吗？

Cullinan 使用 Tornado 的内置服务器，它已经可以用于生产环境。只需设置 `SERVER_THREAD` 以使用多个工作进程。

### 如何处理 HTTPS？

在 Cullinan 前使用反向代理（nginx/Caddy）：

```nginx
server {
    listen 443 ssl;
    
    location / {
        proxy_pass http://localhost:4080;
    }
}
```

## 还有问题？

- 📖 查看[完整文档](./INDEX.md)
- 💡 浏览[示例](../../examples/)
- 💬 在 GitHub 上提 Issue
- 📧 联系维护者

---

**更新时间**：2025-11-11

