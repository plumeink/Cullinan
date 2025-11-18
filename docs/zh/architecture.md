---
title: "架构概述"
slug: "architecture"
module: ["cullinan.core"]
tags: ["architecture", "ioc", "design"]
author: "Plumeink"
reviewers: []
status: draft
locale: zh
translation_pair: "docs/architecture.md"
related_tests: []
related_examples: []
estimate_pd: 2.5
last_updated: "2025-11-18T00:00:00Z"
pr_links: []
---

# 架构概述

本文档基于源码实现（以代码为事实）记录 Cullinan 的高层架构：组件职责、模块交互、启动/请求/关闭序列，以及简单的架构示意图（便于在无渲染器环境中查看）。

## 关键组件（职责速查表）

| 组件 | 代码位置（示例） | 主要职责 |
| --- | --- | --- |
| Core (IoC/DI) | `cullinan/core/*` | 实现注入原语（Provider、Registry、Scope）、生命周期 hook（on_init/on_shutdown）和上下文管理（RequestScope）。 |
| Service 层 | `cullinan/service/*` | 定义长期运行的服务（通常为单例），提供初始化/销毁钩子，并作为应用业务能力的载体。 |
| Controller / Handler | `cullinan/controller/*`, `cullinan/handler/*` | 路由绑定、请求解析、响应构建与访问日志。支持通过注入获取 service 实例。 |
| Application | `cullinan/app.py`, `cullinan/application.py` | 协调启动/关闭流程：注册 providers、发现服务/控制器、初始化服务、启动 Tornado IOLoop 并注册信号处理。 |
| Middleware | `cullinan/middleware/*` | 插件式请求/响应处理链，用于统一处理（日志、鉴权、监控等）。 |


## 模块交互（简要说明）

- 应用（Application）负责协调：它触发模块扫描（ModuleScanner），把发现的 Provider 注册到 `ProviderRegistry`，并把 ProviderRegistry 关联到 `InjectionRegistry`，使所有注入点可解析。
- `ServiceRegistry` 负责管理服务的依赖顺序并依次调用 `on_init()`，启动时将准备就绪的服务置于可用状态。
- 在请求级别，框架在进入请求时创建 RequestContext（`create_context()`），使 `RequestScope` 生效；处理器在该上下文中通过 `Inject` 或构造器注入获得 request-scoped 或单例实例。


## 启动 / 请求 / 关闭 序列（概要）

1. 应用被创建：`create_app()` 或 `CullinanApplication()`。
2. 模块扫描：发现 controllers、services、providers（或由显式注册提供）。
3. 注入配置：注册 `ProviderRegistry` 并把其添加到 `InjectionRegistry`。
4. 服务初始化：`ServiceRegistry` 按依赖顺序实例化服务并执行 `on_init`。失败时记录并可选择停止启动。
5. 启动 IOLoop：调用 `IOLoop.start()` 开始接受请求。
6. 请求处理：每次请求创建 RequestContext -> 解析注入 -> 执行 Handler -> 中间件后处理 -> 清理 RequestContext。
7. 触发关闭：接收到 SIGINT/SIGTERM 或手动调用 `shutdown()`，按照注册顺序调用 shutdown handlers 与 service `on_shutdown`，停止 IOLoop 并退出。


## 架构交互图（制表符对齐的代码块）

下面的图使用制表符在代码块中对齐，便于纯文本环境查看。制表符在不同编辑器中显示略有差异，但在等宽字体/代码块中可保持对齐。你可以把它复制到 Markdown 文档或 README 中查看。

```
Application		ModuleScanner		ProviderRegistry	InjectionRegistry	ServiceRegistry	Tornado IOLoop
-----------		------------		----------------	-----------------	--------------	---------------
create_app() -->	 scan() ----> 	 register() ---->	 add_registry() -->	 register_services() --> start()
													|
													|--dispatch--> Handler (controller/handler)
													|               |
													|               |--uses--> Inject/ProviderRegistry -> provides instances

Request Flow (per request):
IOLoop -> create_context() -> resolve request-scoped providers -> Handler executes -> response -> context cleanup

Legend:
- register(): provider registration from discovered modules
- add_registry(): injection registry gets provider registries to resolve inject markers
- register_services(): service discovery and on_init sequence
```


## 常见注意点与排错建议

- 注入失败（None）通常是因为 provider 尚未注册到 ProviderRegistry，或 `InjectionRegistry` 未包含该 registry。
- 循环依赖会抛出 `CircularDependencyError`，请检查服务依赖顺序并考虑重构为接口/事件回调模式以打破循环。
- 在测试中请使用 `reset_injection_registry()` 和明确的 ProviderRegistry 配置以保证隔离性。


## 工件与后续工作

- 图示占位：`docs/work/architecture_assets/`（可放 Mermaid PNG/SVG 或其它格式）。
- 建议：基于上面的交互图补充一张 Mermaid/PlantUML 图，并将其置于 `docs/work/architecture_assets/` 以便在 MkDocs site 中渲染。

---

如需我把此 ASCII/制表图也生成 PNG（使用 mermaid-cli 或其它工具），或把它转为更高保真度的 Mermaid 图并插入 EN 文件 `docs/wiki/architecture.md`，我可以继续执行（需要确认是否生成图片文件）。
