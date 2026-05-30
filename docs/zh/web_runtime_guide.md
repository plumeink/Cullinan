title: "Web Runtime 指南"
slug: "web-runtime-guide"
module: ["cullinan.gateway", "cullinan.adapter"]
tags: ["web", "runtime", "gateway"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/web_runtime_guide.md"
related_tests: ["tests/web/test_web_runtime.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# Web Runtime 指南

Cullinan 当前的 HTTP 运行时是传输无关的。共享的请求/响应行为位于 `cullinan.gateway`，而服务器相关的集成位于 `cullinan.adapter`。

## 公开 API 面

### Gateway

- `WebRequest`
- `WebResponse`
- `WebHeaders`
- `WebCookies`
- `Router`
- `Dispatcher`
- `MiddlewarePipeline`
- `ExceptionHandler`
- `WebRuntime`

### 适配器

- `WebAdapter`
- `TornadoAdapter`
- `ASGIAdapter`

## 控制器层用法

大多数应用停留在控制器层即可，由框架把返回值转换成 `WebResponse`。

```python
from cullinan.controller import controller, get_api

@controller(url="/health")
class HealthController:
    @get_api(url="/")
    async def health(self):
        return {"status": "ok"}
```

`Dispatcher` 会把普通返回值转换为 `WebResponse`，并统一应用 header policy 与中间件链。

## 底层 gateway 用法

如需自定义运行时行为，可直接使用 gateway 层。

```python
import asyncio

from cullinan.gateway import Dispatcher, Router, WebRequest

router = Router()
router.add_route("GET", "/health", handler=lambda: {"status": "ok"})
dispatcher = Dispatcher(router=router)

request = WebRequest(method="GET", path="/health")
response = asyncio.run(dispatcher.dispatch(request))
assert response.status_code == 200
```

## 响应模型

`WebResponse` 支持：

- text / json 辅助构造
- 显式状态码
- 重复响应头
- cookie 输出
- 在适配器写回前冻结

示例：

```python
from cullinan.gateway import WebResponse

response = WebResponse.json({"ok": True})
response.set_cookie("sid", "abc", http_only=True)
response.freeze()
```

## 运行时切换

`WebRuntime` 负责追踪当前活动运行时，并支持分阶段替换与 drain。这在服务器或适配器切换运行时状态、但仍有飞行中请求时尤其有用。

## 中间件与异常流

- `MiddlewarePipeline` 负责组合 gateway 中间件
- `LegacyMiddlewareBridge` 可把旧式 middleware 注册桥接到 gateway pipeline
- `ExceptionHandler` 负责把未捕获异常转换成 HTTP 响应

## 迁移说明

新文档与新代码应使用以下名称：

- `WebRequest`，而不是旧的 request 包装类型
- `WebResponse`，而不是旧的 response 包装类型
- `WebAdapter`，而不是旧的 adapter 命名

另见：

- [RESTful API wiki](wiki/restful_api.md)
- [架构设计](architecture.md)
- [运行时整合概览](runtime_updates_v093.md)
