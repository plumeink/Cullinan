title: "Cullinan 快速开始"
slug: "getting-started"
module: ["cullinan.application"]
tags: ["getting-started", "tutorial"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/getting_started.md"
related_tests: ["tests/test_real_app_startup.py"]
related_examples: ["examples/hello_http.py"]
estimate_pd: 2.0
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# Cullinan 快速开始

本页提供最小化的快速入门，说明如何安装并运行 Cullinan 示例应用。

## 前置条件
- Python 3.8+
- Git

## 安装

在继续之前，请确保已经安装 Python 3.8+ 并可以在命令行中使用 `python` 和 `pip`。

在大多数环境中，可以使用以下命令升级 pip 并安装 Cullinan（适用于 Windows、Linux、macOS）：

```bash
python -m pip install -U pip
python -m pip install cullinan
```

## 快速开始
1. 在你希望放置项目的目录创建一个新项目目录并进入：

在所有平台上：

```bash
mkdir my_cullinan_project
cd my_cullinan_project
```

2. 确保你已有一个 Python 环境（virtualenv、conda、系统 Python 等均可）。然后安装发布版本的包：

```bash
python -m pip install -U pip
python -m pip install cullinan
```

3. 在项目根目录创建一个最小应用文件 `minimal_app.py`，内容如下：

```python
# minimal_app.py
from cullinan.application import run
from cullinan.controller import controller, get_api

@controller(url='/hello')
class HelloController:
    """简单的 HTTP 控制器。"""
    
    @get_api(url='')
    def hello(self):
        return {'message': 'Hello from Cullinan!'}

if __name__ == '__main__':
    run()
```

4. 运行你的应用：

在 Windows（PowerShell）中：

```powershell
python minimal_app.py
```

在 Linux / macOS 中：

```bash
python minimal_app.py
```

在浏览器中打开 `http://localhost:4080/hello` 验证服务器是否启动。

## 示例运行输出

下方日志展示了在本地环境（Windows PowerShell 会话）中成功运行上述示例时的典型输出，实际时间戳和执行耗时可能因环境不同而有所变化：

```
|||||||||||||||||||||||||||||||||||||||||||||||||
|||                                           |||
|||    _____      _ _ _                       |||
|||   / ____|    | | (_)                      |||
|||  | |    _   _| | |_ _ __   __ _ _ __      |||
|||  | |   | | | | | | | '_ \ / _` | '_ \     |||
|||  | |___| |_| | | | | | | | (_| | | | |    |||
|||   \_____\__,_|_|_|_|_| |_|\__,_|_| |_|    |||
|||                                           |||
|||||||||||||||||||||||||||||||||||||||||||||||||
	|||

2025-11-19 04:18:50,209 INFO cullinan.application: loading env...
2025-11-19 04:18:50,210 INFO cullinan.application: └---configuring dependency injection...
2025-11-19 04:18:50,210 INFO cullinan.application: └---dependency injection configured
2025-11-19 04:18:50,210 INFO cullinan.application: └---scanning services...
2025-11-19 04:18:50,210 INFO cullinan.application: ...
2025-11-19 04:18:50,223 INFO cullinan.application: └---found 31 modules to scan
2025-11-19 04:18:50,228 INFO cullinan.application: └---scanning controllers...
2025-11-19 04:18:50,260 INFO cullinan.application: └---found 31 modules to scan
2025-11-19 04:18:50,261 INFO cullinan.application: └---initializing services...
2025-11-19 04:18:50,261 INFO cullinan.application: └---no services registered
2025-11-19 04:18:50,261 INFO cullinan.application: └---loading controller finish

2025-11-19 04:18:50,261 INFO cullinan.application: loading env finish

2025-11-19 04:18:50,262 INFO cullinan.application: server is starting
2025-11-19 04:18:50,262 INFO cullinan.application: port is 4080
```

此时服务器已启动并保持运行状态，监听在 `http://localhost:4080`。使用 Ctrl+C 可以优雅地停止服务器。

## 最小应用示例

这是一个演示 Cullinan 核心功能的最小应用：

```python
# minimal_app.py
from cullinan.application import run
from cullinan.controller import controller, get_api

@controller(url='/hello')
class HelloController:
    """简单的 HTTP 控制器。"""
    
    @get_api(url='')
    def hello(self):
        return {'message': 'Hello from Cullinan!'}

if __name__ == '__main__':
    run()
```

运行此示例：

```powershell
# 将上述代码保存为 minimal_app.py
python minimal_app.py
```

然后在浏览器中访问 `http://localhost:4080/hello`。

## 理解基础知识

### 应用生命周期
1. **创建**：`create_app()` 使用默认设置初始化应用
2. **注册**：通过模块扫描或显式注册发现控制器和服务
3. **启动**：`app.run()` 启动 Tornado IOLoop 并开始接受请求
4. **关闭**：在 SIGINT/SIGTERM 信号时优雅关闭

### 依赖注入
Cullinan 提供内置的 IoC/DI 支持。

#### 注解说明：`@injectable` vs `@controller()`

**`@injectable`** - 通用依赖注入注解
- 适用于任何需要依赖注入的类（Service、Repository、普通类等）
- 需要手动使用，不会自动注册到任何注册表
- 在类实例化后自动注入标记的依赖
- 使用场景：Service 层、Repository 层、工具类等

**`@controller()`** - Controller 专用自注册注解
- 专门用于 HTTP Controller 类
- **自动调用 `@injectable`**，无需手动添加
- 自动注册 Controller 及其路由到 ControllerRegistry
- 自动扫描类中的 `@get_api`、`@post_api` 等方法装饰器
- 使用场景：仅用于 HTTP Controller

```python
from cullinan.controller import controller, get_api
from cullinan.service import Service, service
from cullinan.core import injectable, InjectByName
from cullinan.params import Path

# Service 使用 @service (继承自 Service 基类)
@service
class UserService(Service):
    def get_user(self, user_id):
        return {'id': user_id, 'name': 'John'}

# Repository 使用 @injectable
@injectable
class UserRepository:
    def find_by_id(self, user_id):
        return {'id': user_id}

# Controller 使用 @controller() - 自动包含 @injectable
@controller(url='/api/users')
class UserController:
    # Controller 中的依赖注入
    user_service = InjectByName('UserService')
    
    @get_api(url='/{user_id}')
    async def get_user(self, user_id: Path(int)):
        return self.user_service.get_user(user_id)
```

**重要：** 在 Controller 中**不要**重复使用 `@injectable`，因为 `@controller()` 已经自动包含了它。

---

#### RESTful API 装饰器（快速说明）

Cullinan 提供一组 REST 风格的装饰器，用于将 Controller 方法绑定到 HTTP 路由：

- `get_api`
- `post_api`
- `patch_api`
- `delete_api`
- `put_api`

关键点：

- 这些装饰器在源码中定义为 `def get_api(**kwargs)` 等，**只接受关键字参数**。
  - 写法 `@get_api('/user')` 是**不合法**的，会在导入模块时抛出 `TypeError`。
  - 正确写法应为：`@get_api(url='/user')`。
- `url` 参数使用轻量级模板语法，支持 `{param}` 占位符。

**v0.90+ 推荐：类型安全参数系统**

```python
from cullinan.params import Path, Query, Body, DynamicBody

@controller(url='/api/users')
class UserController:
    # 类型安全的路径和查询参数
    @get_api(url='/{id}')
    async def get_user(self, id: Path(int), include_posts: Query(bool, default=False)):
        return {"id": id, "include_posts": include_posts}
    
    # 带校验的查询参数
    @get_api(url='/')
    async def list_users(
        self,
        page: Query(int, default=1, ge=1),
        size: Query(int, default=10, ge=1, le=100),
    ):
        return {"page": page, "size": size}
    
    # 带校验的类型安全请求体参数
    @post_api(url='/')
    async def create_user(
        self,
        name: Body(str, required=True),
        age: Body(int, default=0, ge=0, le=150),
    ):
        return {"name": name, "age": age}
    
    # DynamicBody 提供灵活的属性访问
    @post_api(url='/dynamic')
    async def create_dynamic(self, body: DynamicBody):
        return {"name": body.name, "age": body.get('age', 0)}
```

详见 [参数系统指南](parameter_system_guide.md)。

<details>
<summary><strong>传统方式（仍然支持）</strong></summary>

传统参数风格仍然支持，用于向后兼容：

常用参数：
- `url`：路由路径（字符串），支持 `{param}` 占位符，例如 `'/users/{user_id}'`。
- `query_params`：查询参数名称列表/元组，例如 `('page', 'size')`。
- `body_params`（仅 POST/PATCH）：需要从 JSON/form body 中解析的字段名称集合。
- `file_params`：上传文件字段名称列表。
- `headers`：必须存在的 HTTP 请求头名称列表。
- `get_request_body`（仅 POST/PATCH）：为 `True` 时，会将原始请求体作为参数传入方法。

```python
@controller(url='/api/users')
class UserController:
    @get_api(url='/{user_id}')
    def get_user(self, url_params):
        user_id = url_params.get('user_id') if url_params else None
        return {"id": user_id}

    @get_api(url='/', query_params=('page', 'size'))
    def list_users(self, query_params):
        page = query_params.get('page') if query_params else None
        size = query_params.get('size') if query_params else None
        return {"page": page, "size": size}

    @post_api(url='/', body_params=('name', 'email'))
    def create_user(self, body_params):
        name = body_params.get('name') if body_params else None
        email = body_params.get('email') if body_params else None
        return {"name": name, "email": email}
```

</details>

如需了解 URL 模板与各装饰器参数的完整说明，请参考 `docs/zh/wiki/restful_api.md`。

---

#### 推荐的依赖注入方式

**方式一：InjectByName（推荐，最简单）**

按名称注入，无需导入依赖类，避免循环导入问题：

```python
from cullinan.service import Service, service
from cullinan.core import injectable, InjectByName

@service
class DatabaseService(Service):
    def query(self, sql):
        return f"Results for: {sql}"

@injectable
class UserRepository:
    # 推荐：InjectByName 不需要类型注解，直接使用字符串名称
    db = InjectByName('DatabaseService')
    
    def get_users(self):
        return self.db.query("SELECT * FROM users")
```

**方式二：Inject + TYPE_CHECKING（支持 IDE 联想）**

如果需要 IDE 自动补全和类型检查，可以使用 `Inject` 配合 TYPE_CHECKING：

```python
from typing import TYPE_CHECKING
from cullinan.core import injectable, Inject
from cullinan.service import Service, service

# TYPE_CHECKING 块中的导入不会在运行时执行，避免循环导入
if TYPE_CHECKING:
    from cullinan.service import DatabaseService

@service
class DatabaseService(Service):
    def query(self, sql):
        return f"Results for: {sql}"

@injectable
class UserRepository:
    # 使用 TYPE_CHECKING 导入类型后，可以获得 IDE 联想支持
    db: 'DatabaseService' = Inject()
    
    def get_users(self):
        # IDE 可以提示 db.query 方法
        return self.db.query("SELECT * FROM users")
```

**方式三：Inject + 纯字符串注解（无 IDE 联想）**

如果不需要 IDE 联想，也可以直接使用字符串注解：

```python
from cullinan.core import injectable, Inject

@injectable
class UserRepository:
    # 纯字符串注解，无需导入，但也没有 IDE 联想
    db: 'DatabaseService' = Inject()
    
    def get_users(self):
        return self.db.query("SELECT * FROM users")
```

**总结：**
- **InjectByName**：推荐用于大多数场景，简单直接，无需类型注解
- **Inject + TYPE_CHECKING**：适合需要 IDE 联想的场景，开发体验更好
- **Inject + 字符串注解**：最简单但无 IDE 支持

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
- 如果安装包时出现错误，请确保 Python 和 pip 已更新，并且能访问 PyPI（网络或代理设置）。
- 如果在运行 PowerShell 命令时遇到权限问题，请检查 PowerShell 的执行策略或以管理员权限运行命令。

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
