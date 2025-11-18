title: "Cullinan 快速开始"
slug: "getting-started"
module: ["cullinan.application"]
tags: ["getting-started", "tutorial"]
author: "Plumeink"
reviewers: []
status: draft
locale: zh
translation_pair: "docs/getting_started.md"
related_tests: ["tests/test_real_app_startup.py"]
related_examples: ["examples/hello_http.py"]
estimate_pd: 2.0
last_updated: "2025-11-18T12:00:00Z"
pr_links: []

# Cullinan 快速开始

本页提供最小化的快速入门，说明如何安装并运行 Cullinan 示例应用。

## 前置条件
- Python 3.8+
- Git

## 安装（PowerShell）

python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -U pip; pip install -e .

## 快速开始
1. 确保你在仓库根目录。
2. 激活虚拟环境（见上文命令）。
3. 运行示例服务器：

python examples\hello_http.py

预期：服务器启动并监听配置的端口。打开 http://localhost:8888 查看响应。

## 已验证的示例（本地运行）

我在 Windows PowerShell 会话中使用上述命令本地运行了该示例。观察到的日志输出（节选）：

```
INFO:__main__:Starting IOLoop... (will stop after one verification request)
INFO:__main__:Async Requesting http://127.0.0.1:8888/hello
INFO:tornado.access:200 GET /hello (127.0.0.1) 0.50ms
INFO:__main__:Response status: 200
INFO:__main__:Response body: Hello Cullinan
INFO:__main__:IOLoop stopped, exiting
```

说明：该示例使用 `cullinan.handler.registry.get_handler_registry()` 注册一个简单的 Tornado 处理器，并发起一次验证请求后退出。它适合作为文档中的烟雾测试示例。

## 最小应用示例

这是一个演示 Cullinan 核心功能的最小应用：

```python
# minimal_app.py
from cullinan.app import create_app
from cullinan.controller import controller

@controller(path='/hello')
def hello_handler(request):
    """简单的 HTTP 处理器。"""
    return {'message': 'Hello from Cullinan!'}

if __name__ == '__main__':
    app = create_app()
    # 控制器通过自动发现或显式注册
    app.run()  # 在默认端口启动 Tornado IOLoop
```

运行此示例：

```powershell
# 将上述代码保存为 minimal_app.py
.\\.venv\\Scripts\\Activate.ps1
python minimal_app.py
```

然后在浏览器中访问 `http://localhost:8888/hello`。

## 理解基础知识

### 应用生命周期
1. **创建**：`create_app()` 使用默认设置初始化应用
2. **注册**：通过模块扫描或显式注册发现控制器和服务
3. **启动**：`app.run()` 启动 Tornado IOLoop 并开始接受请求
4. **关闭**：在 SIGINT/SIGTERM 信号时优雅关闭

### 依赖注入
Cullinan 提供内置的 IoC/DI 支持。服务注入示例：

```python
from cullinan.service import Service, service
from cullinan.core import injectable, Inject

@service
class DatabaseService(Service):
    def query(self, sql):
        return f"Results for: {sql}"

@injectable
class UserController:
    db: DatabaseService = Inject()
    
    def get_users(self):
        return self.db.query("SELECT * FROM users")
```

有关注入模式的详细信息，请参阅 `docs/wiki/injection.md`。

## 常见模式

### 添加中间件
```python
from cullinan.middleware import MiddlewareBase

class LoggingMiddleware(MiddlewareBase):
    def process_request(self, request):
        print(f"Request: {request.method} {request.path}")

# 在应用初始化期间注册
app.add_middleware(LoggingMiddleware())
```

### 配置
```python
from cullinan.config import Config

config = Config()
config.set('database.url', 'postgresql://localhost/mydb')
config.set('server.port', 8080)
```

## 故障排查
- 如果 `Activate.ps1` 失败，请确保 PowerShell 执行策略允许脚本执行：`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

## 下一步
- 阅读 `docs/wiki/injection.md` 了解 IoC/DI 细节。
- 浏览 `examples/` 目录查看可运行示例。

## 其他资源

- **架构**：参阅 `docs/architecture.md` 了解系统设计概览
- **组件**：阅读 `docs/wiki/components.md` 了解组件职责
- **生命周期**：在 `docs/wiki/lifecycle.md` 中学习应用生命周期
- **中间件**：在 `docs/wiki/middleware.md` 中理解中间件
- **API 参考**：浏览 `docs/api_reference.md` 查看完整 API 文档
- **示例**：探索 `examples/` 目录获取更多示例

## 社区与支持

- **问题反馈**：在 [GitHub Issues](https://github.com/your-org/cullinan/issues) 报告 bug
- **贡献**：参阅 `docs/contributing.md` 了解贡献指南
- **测试**：阅读 `docs/testing.md` 了解测试最佳实践
