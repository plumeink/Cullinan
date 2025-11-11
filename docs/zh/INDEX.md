# Cullinan 框架 - 文档索引

欢迎使用 Cullinan 框架文档！

## 📚 文档结构

### 入门指南
- [**入门指南**](./GETTING_STARTED.md) - Cullinan 快速入门
- [**完整教程**](./TUTORIAL.md) - 逐步构建 Todo API
- [**常见问题**](./FAQ.md) - 常见问题解答

### 核心概念
- [**依赖注入**](./DEPENDENCY_INJECTION.md) - Spring 风格的依赖注入系统
- [**生命周期管理**](./LIFECYCLE_MANAGEMENT.md) - 服务生命周期钩子
- [**控制器**](./CONTROLLERS.md) - HTTP 请求处理
- [**服务**](./SERVICES.md) - 业务逻辑层
- [**WebSocket**](./WEBSOCKET.md) - 实时通信

### 高级主题
- [**配置**](./CONFIGURATION.md) - 应用配置
- [**中间件**](./MIDDLEWARE.md) - 请求/响应处理
- [**错误处理**](./ERROR_HANDLING.md) - 异常管理
- [**测试**](./TESTING.md) - 测试您的应用
- [**部署**](./DEPLOYMENT.md) - 生产环境部署

### 参考资料
- [**API 参考**](./API_REFERENCE.md) - 完整 API 文档
- [**示例**](../../examples/) - 代码示例
- [**迁移指南**](./MIGRATION_GUIDE.md) - 从旧版本升级

## 🌏 语言

- **English** - 英文版 (`docs/`)
- **中文** - 此目录 (`docs/zh/`)

## 🚀 快速链接

### 初学者
1. 从[入门指南](./GETTING_STARTED.md)开始
2. 学习[完整教程](./TUTORIAL.md)
3. 探索[示例](../../examples/)

### 有经验的用户
1. 查看[API 参考](./API_REFERENCE.md)
2. 阅读[架构指南](./ARCHITECTURE_MASTER.md)
3. 查看[迁移指南](./MIGRATION_GUIDE.md)进行升级

## 📖 按功能分类的文档

### 依赖注入
- ✅ 字符串类型注解（无需 import）
- ✅ 自动服务发现
- ✅ 构造函数注入
- ✅ 字段注入
- 📄 [了解更多](./DEPENDENCY_INJECTION.md)

### 生命周期管理
- ✅ 多个生命周期阶段
- ✅ 基于 phase 的启动顺序
- ✅ 异步/同步钩子
- ✅ 优雅关闭
- 📄 [了解更多](./LIFECYCLE_MANAGEMENT.md)

### 控制器和路由
- ✅ 基于装饰器的路由
- ✅ RESTful API 支持
- ✅ 路径参数
- ✅ 查询/请求体参数
- 📄 [了解更多](./CONTROLLERS.md)

### WebSocket
- ✅ 简单的 WebSocket 处理器
- ✅ 依赖注入支持
- ✅ 基于事件的 API
- 📄 [了解更多](./WEBSOCKET.md)

## 🎯 常见任务

### 创建简单 API
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

### 使用依赖注入
```python
from cullinan.service import service, Service
from cullinan.controller import controller, get_api
from cullinan.core import Inject

@service
class UserService(Service):
    def get_users(self):
        return ['张三', '李四']

@controller(url='/api/users')
class UserController:
    user_service: 'UserService' = Inject()  # 无需 import！
    
    @get_api(url='')
    def list_users(self, query_params):
        return {'users': self.user_service.get_users()}
```

### 添加生命周期钩子
```python
from cullinan.service import service, Service

@service
class DatabaseService(Service):
    def get_phase(self) -> int:
        return -100  # 早启动
    
    def on_startup(self):
        print("正在连接数据库...")
        # 初始化连接
    
    def on_shutdown(self):
        print("正在关闭数据库...")
        # 清理
```

## 🔧 配置

### 环境变量
```env
SERVER_PORT=4080
SERVER_THREAD=1
LOG_LEVEL=INFO
```

### 应用设置
```python
from cullinan import application

if __name__ == '__main__':
    application.run()  # 使用 .env 配置
```

## 📝 示例

浏览 [`examples/`](../../examples/) 目录中的完整示例：

- `basic/` - Hello World
- `service_examples.py` - 服务层
- `core_injection_example.py` - 依赖注入
- `discord_bot_lifecycle_example.py` - Discord Bot 生命周期
- `websocket_injection_example.py` - WebSocket 依赖注入

## 🤝 贡献

欢迎改进文档！请查看根目录 `README.md` 了解贡献指南。

## 📬 支持

- 📄 查看[常见问题](./FAQ.md)
- 💬 在 GitHub 上提 Issue
- 📧 联系维护者

---

**使用 Cullinan 愉快地编码！** 🚀

