# Cullinan 框架 - 入门指南

欢迎使用 Cullinan！本指南将帮助您快速上手 Cullinan Web 框架。

## 什么是 Cullinan？

Cullinan 是一个基于 Tornado 构建的 Python Web 框架，灵感来自 Spring Boot。它提供：

- 🎯 **依赖注入** - Spring 风格的自动依赖管理
- 🔄 **生命周期管理** - 完整的服务生命周期钩子
- 🚀 **简单路由** - 基于装饰器的路由注册
- 📦 **服务层** - 内置服务架构
- 🔌 **WebSocket 支持** - 一流的 WebSocket 集成
- ⚡ **高性能** - 基于 Tornado 的异步架构

## 快速开始

### 安装

```bash
# 从源码安装
pip install path/to/Cullinan

# 或以开发模式安装
cd path/to/Cullinan
pip install -e .
```

### 第一个应用

创建文件 `app.py`：

```python
from cullinan import application
from cullinan.controller import controller, get_api

@controller(url='/api')
class HelloController:
    @get_api(url='/hello')
    def hello(self, query_params):
        return {'message': '你好，世界！'}

if __name__ == '__main__':
    application.run()
```

运行应用：

```bash
python app.py
```

访问 `http://localhost:4080/api/hello`，您将看到：

```json
{"message": "你好，世界！"}
```

## 核心概念

### 1. 控制器（Controllers）

控制器处理 HTTP 请求。使用装饰器定义路由：

```python
from cullinan.controller import controller, get_api, post_api

@controller(url='/api/users')
class UserController:
    @get_api(url='')
    def list_users(self, query_params):
        return {'users': ['张三', '李四']}
    
    @post_api(url='')
    def create_user(self, body_params):
        name = body_params.get('name')
        return {'created': True, 'name': name}
```

### 2. 服务（Services）

服务包含业务逻辑。使用 `@service` 装饰器：

```python
from cullinan.service import service, Service

@service
class UserService(Service):
    def get_all_users(self):
        return ['张三', '李四', '王五']
    
    def create_user(self, name):
        # 业务逻辑
        return {'id': 1, 'name': name}
```

### 3. 依赖注入

自动将服务注入到控制器：

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject

@controller(url='/api/users')
class UserController:
    # 使用字符串注解注入服务（无需 import！）
    user_service: 'UserService' = Inject()
    
    @get_api(url='')
    def list_users(self, query_params):
        # 直接使用注入的服务
        users = self.user_service.get_all_users()
        return {'users': users}
```

**无需导入 Service 类！** 只需使用字符串注解。

### 4. 生命周期钩子

服务可以钩入应用生命周期：

```python
from cullinan.service import service, Service

@service
class DatabaseService(Service):
    def get_phase(self) -> int:
        return -100  # 早启动（数字越小越早）
    
    def on_startup(self):
        """在 Web 服务器启动前调用"""
        print("正在连接数据库...")
        self._connect()
    
    def on_shutdown(self):
        """关闭时调用"""
        print("正在关闭数据库连接...")
        self._disconnect()
```

**Phase 顺序**：
- `-200`：配置服务（最早）
- `-100`：数据库、缓存服务
- `-50`：后台工作线程、Bot
- `0`：业务服务（默认）
- `50`：Web 相关服务（最晚）

## 项目结构

推荐的 Cullinan 项目结构：

```
my-project/
├── app.py                 # 应用入口
├── .env                   # 环境变量
├── controllers/           # HTTP 请求处理器
│   ├── __init__.py
│   ├── user_controller.py
│   └── product_controller.py
├── services/              # 业务逻辑
│   ├── __init__.py
│   ├── user_service.py
│   └── email_service.py
├── models/                # 数据模型
│   └── user.py
├── templates/             # HTML 模板（可选）
└── static/                # 静态文件（可选）
```

## 配置

### 环境变量

创建 `.env` 文件：

```env
SERVER_PORT=4080
SERVER_THREAD=1
DISCORD_TOKEN=your_token_here
DATABASE_URL=postgresql://localhost/mydb
```

在代码中访问：

```python
import os
token = os.getenv('DISCORD_TOKEN')
```

### 应用设置

在主文件中配置：

```python
from cullinan import application

if __name__ == '__main__':
    application.run()  # 使用默认设置
```

## 下一步

- 📖 [完整教程](./TUTORIAL.md) - 构建真实应用
- 🎯 [依赖注入指南](./DEPENDENCY_INJECTION.md) - 掌握依赖注入
- 🔄 [生命周期管理](./LIFECYCLE_MANAGEMENT.md) - 服务生命周期
- 🌐 [WebSocket 指南](./WEBSOCKET.md) - 实时通信
- 📚 [API 参考](./API_REFERENCE.md) - 完整 API 文档
- 💡 [示例](../examples/) - 代码示例

## 获取帮助

- 📄 查看 [常见问题](./FAQ.md)
- 💬 在 GitHub Issues 提问
- 📖 阅读完整文档

## 示例

查看 [examples 目录](../examples/) 获取完整的工作示例：

- `basic/` - 简单的 Hello World 应用
- `service_examples.py` - 服务层示例
- `core_injection_example.py` - 依赖注入示例
- `discord_bot_lifecycle_example.py` - Discord Bot 生命周期
- `websocket_injection_example.py` - WebSocket 依赖注入

---

**准备好开始构建了吗？** 从[完整教程](./TUTORIAL.md)开始！

