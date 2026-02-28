# 迁移指南: v0.9x → v0.93

> **Cullinan 框架** — 从 v0.9x 升级到 v0.93 的完整迁移指南。

## 变更总览

Cullinan v0.93 是一次重大架构重写，引入了以下变化：

| 特性 | v0.9x | v0.93 |
|------|-------|------|
| **HTTP 引擎** | 仅 Tornado | Tornado 或 ASGI（可配置） |
| **请求处理** | 每个 URL 一个 Handler（Servlet-per-URL） | 单分发器（Spring 风格） |
| **请求对象** | `tornado.httputil.HTTPServerRequest` | `CullinanRequest`（传输无关） |
| **响应对象** | `HttpResponse` + `self.write()` | `CullinanResponse`（工厂方法） |
| **路由** | 动态 `type('Servlet'...)` 类 | 前缀树 Router |
| **中间件** | 仅初始化，不在请求管线中 | 洋葱模型管线，处理每个请求 |
| **Tornado 依赖** | 必需 | 可选（`pip install cullinan[tornado]`） |
| **ASGI 支持** | 无 | 完整 ASGI 3.0（uvicorn/hypercorn） |
| **WebSocket** | 仅 Tornado | Tornado + ASGI |
| **OpenAPI** | 无 | 自动从路由生成 |

## 安装

```bash
# Tornado 模式（默认，向后兼容）
pip install cullinan[tornado]

# ASGI 模式（uvicorn）
pip install cullinan[asgi]

# 完整安装
pip install cullinan[full]
```

## 逐步迁移

### 1. 导入路径变更

所有现有导入仍然有效，新增了以下导入：

```python
# v0.9x — 在 v0.93 中仍然有效
from cullinan.controller import controller, get_api, post_api
from cullinan.service import service, Service
from cullinan.core import Inject

# v0.93 — 新增可用导入
from cullinan import (
    CullinanRequest, CullinanResponse,     # 统一请求/响应
    Router, Dispatcher,                     # 网关层
    GatewayMiddleware, CORSMiddleware,      # 中间件管线
    OpenAPIGenerator,                       # OpenAPI 规范
    TornadoAdapter, ASGIAdapter,            # 服务器适配器
    get_asgi_app,                           # ASGI 便捷函数
)
```

### 2. Controller 变更

#### v0.9x：Controller 方法使用 Tornado 的 `self.write()`

```python
# v0.9x — handler 直接操作 tornado 内部 API
@controller(url='/api/users')
class UserController:
    @get_api(url='/{id}')
    async def get_user(self, url_params=None):
        user_id = url_params.get('id')
        # ... 业务逻辑 ...
        return HttpResponse(body=user_data, status=200)
```

#### v0.93：Controller 方法返回 `CullinanResponse`

```python
# v0.93 — 传输无关，返回 CullinanResponse
from cullinan import CullinanResponse

@controller(url='/api/users')
class UserController:
    user_service: UserService = Inject()

    @get_api(url='/{id}')
    async def get_user(self, id):
        user = self.user_service.get_by_id(id)
        if not user:
            return CullinanResponse.error(404, "User not found")
        return CullinanResponse.json(user)
```

**向后兼容**：旧的 `HttpResponse` 返回类型仍然有效 — `Dispatcher` 会自动转换。

### 3. 响应对象迁移

| v0.9x | v0.93 等价写法 |
|-------|-------------|
| `HttpResponse(body=data, status=200)` | `CullinanResponse.json(data)` |
| `HttpResponse(body="text", status=200)` | `CullinanResponse.text("text")` |
| `HttpResponse(body=data, status=404)` | `CullinanResponse.error(404, "msg")` |
| `return {"key": "value"}`（dict） | `return {"key": "value"}`（自动 JSON，仍有效） |
| `return None` | `return None`（自动 204 No Content） |

### 4. 运行应用

#### v0.9x：仅 Tornado

```python
from cullinan.application import run
run()  # 在端口 4080 启动 Tornado
```

#### v0.93：选择你的引擎

```python
from cullinan.application import run

# 方式 A：Tornado（默认，向后兼容）
run()

# 方式 B：Tornado（显式指定）
run(engine='tornado')

# 方式 C：ASGI
run(engine='asgi')

# 方式 D：ASGI app 用于外部服务器
from cullinan import get_asgi_app
app = get_asgi_app()
# 然后：uvicorn myapp:app
```

环境变量：`CULLINAN_ENGINE=asgi`，或配置：`server_engine='asgi'`。

### 5. 配置变更

```python
from cullinan import configure

configure(
    user_packages=['myapp'],
    # v0.93 新增选项：
    # server_engine='tornado',        # 'tornado' 或 'asgi'
    # asgi_server='uvicorn',          # 'uvicorn' 或 'hypercorn'
    # route_trailing_slash=False,
    # route_case_sensitive=True,
    # debug=False,
)
```

### 6. 中间件迁移

#### v0.9x：中间件注册但未接入请求管线

```python
from cullinan.middleware import Middleware, middleware

@middleware(order=1)
class AuthMiddleware(Middleware):
    def process_request(self, request):
        # 启动时初始化，但不会在每个请求中调用
        pass
```

#### v0.93：中间件在洋葱管线中

```python
from cullinan import GatewayMiddleware, get_pipeline

class AuthMiddleware(GatewayMiddleware):
    async def __call__(self, request, call_next):
        token = request.get_header('Authorization')
        if not token:
            return CullinanResponse.error(401, "Unauthorized")
        response = await call_next(request)
        return response

# 注册
get_pipeline().add(AuthMiddleware())
```

**向后兼容**：旧的 `@middleware` 类通过 `LegacyMiddlewareBridge` 自动桥接。

### 7. OpenAPI 集成

```python
from cullinan import OpenAPIGenerator, get_router

# 从所有已注册路由自动生成规范
gen = OpenAPIGenerator(
    title='My API',
    version='1.0.0',
    description='我的 API',
)

# 注册 /openapi.json 和 /openapi.yaml 端点
gen.register_spec_routes()

# 或以编程方式获取规范
spec_dict = gen.to_dict()
json_str = gen.to_json()
```

### 8. WebSocket 变更

#### v0.9x：仅 Tornado WebSocket

```python
@websocket_handler(url='/ws/chat')
class ChatHandler:
    def on_open(self):
        pass
    def on_message(self, message):
        self.write_message(f"echo: {message}")
    def on_close(self):
        pass
```

#### v0.93：相同 API，同时支持 Tornado 和 ASGI

`@websocket_handler` API 不变。在 ASGI 模式下运行时，WebSocket 连接通过 ASGI WebSocket 协议原生处理。

### 9. 参数系统

`cullinan.params` 系统（`Path`、`Query`、`Body`、`Header`）不变，在 v0.93 中工作方式完全相同。参数现在由 `Dispatcher` 而非 Tornado handler 解析。

## 架构对比

### v0.9x 架构

```
请求 → Tornado → 动态 Handler(每个URL) → Controller 方法 → self.write()
```

### v0.93 架构

```
请求 → 适配器(Tornado/ASGI) → CullinanRequest → 中间件管线
  → Dispatcher → Router → Controller 方法 → CullinanResponse
  → 适配器 → 原生响应
```

## 破坏性变更

1. **`tornado` 不再是必需依赖** — 如果需要请使用 `pip install cullinan[tornado]` 安装。
2. **`Handler` 基类** 已弃用 — controller 不再继承 `tornado.web.RequestHandler`。
3. **直接使用 Tornado API**（controller 中的 `self.set_status()`、`self.write()`、`self.finish()`）已弃用 — 请使用 `CullinanResponse` 代替。

## 弃用时间表

| 项目 | v0.93 状态 | 计划移除 |
|------|----------|---------|
| `Handler` 类 | 弃用（警告） | v3.0 |
| `HttpResponse` | 弃用（自动桥接） | v3.0 |
| `EncapsulationHandler.add_url()` | 仅内部使用 | v3.0 |
| controller 中的 `self.write()` | 弃用 | v3.0 |
| 旧中间件（`Middleware` 基类） | 自动桥接 | v3.0 |

