---
title: "架构概述"
slug: "architecture"
module: ["cullinan.core"]
tags: ["architecture", "ioc", "design"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/wiki/architecture.md"
related_tests: []
related_examples: []
estimate_pd: 2.5
last_updated: "2025-12-25T00:00:00Z"
pr_links: []
---

# 架构概述

> **说明（v0.90）**：IoC/DI 架构已在 0.90 版本中重新设计。
> 新架构请参阅 [IoC/DI 2.0 架构](ioc_di_v2.md) 和 [架构更新](../architecture_updated.md)。
> `cullinan.core.container` 中的新 `ApplicationContext` 提供统一的容器入口。

本文档基于源码实现（以代码为事实）记录 Cullinan 的高层架构：组件职责、模块交互、启动/请求/关闭序列，以及简单的架构示意图（便于在无渲染器环境中查看）。

## 关键组件（速查表）

| 组件 | 代码位置（示例） | 主要职责 |
| --- | --- | --- |
| Core (IoC/DI) | `cullinan/core/*` | 提供 DI 原语（Provider、Registry、Scope）、生命周期钩子（`on_init`/`on_shutdown`）和上下文管理（`RequestScope`）。 |
| Service 层 | `cullinan/service/*` | 定义长期运行的服务（通常为单例），实现初始化/销毁钩子，并提供业务能力。 |
| Controller / Handler | `cullinan/controller/*`, `cullinan/handler/*` | 路由注册、请求解析、响应构建与访问日志。处理器通过 DI 获取服务。 |
| Application | `cullinan/app.py`, `cullinan/application.py` | 协调启动/关闭：注册 providers、发现服务/控制器、初始化服务、启动 Tornado IOLoop 并安装信号处理器。 |
| Middleware | `cullinan/middleware/*` | 可插拔的请求/响应处理链（日志、认证、监控等）。 |


## 模块交互（简要）

- Application 协调整个系统：它调用 ModuleScanner 发现控制器、服务和提供者。发现的 Provider 被注册到 `ProviderRegistry`，然后添加到 `InjectionRegistry` 使注入点可解析。
- `ServiceRegistry` 管理服务依赖排序并在启动时调用 `on_init()`；它确保服务在请求处理开始前可用。
- 在请求时，框架创建 `RequestContext`（通过 `create_context()`），使 `RequestScope` 生效；处理器在该上下文中解析依赖（属性注入或构造器注入）并可使用请求作用域或单例实例。


## 启动 / 请求 / 关闭 序列（概要）

1. 应用被构建：`create_app()` 或 `CullinanApplication()`。
2. 模块扫描：发现控制器、服务、providers（或依赖显式注册）。
3. 注入配置：注册 `ProviderRegistry` 实例并添加到 `InjectionRegistry`。
4. 服务初始化：`ServiceRegistry` 解析依赖顺序并实例化服务，调用 `on_init`。失败时记录并可能中止启动。
5. 启动 IOLoop：调用 `IOLoop.start()` 接受请求。
6. 请求处理：每次请求创建 `RequestContext` -> 解析注入 -> 执行处理器 -> 中间件后处理 -> 清理 `RequestContext`。
7. 关闭：收到 SIGINT/SIGTERM 或手动 `shutdown()`，按顺序执行注册的关闭处理器和服务 `on_shutdown` 钩子，停止 IOLoop 并退出。


## 架构交互图（ASCII，制表符对齐）

下面是一个纯文本图，使用制表符列对齐，便于在代码块和无 Mermaid 支持的环境中渲染。

```
Application		ModuleScanner		ProviderRegistry	InjectionRegistry	ServiceRegistry	Tornado IOLoop
-----------		------------		----------------	-----------------	--------------	---------------
create_app() -->	 scan() ----> 	 register() ---->	 add_registry() -->	 register_services() --> start()
                                                    |
                                                    |--dispatch--> Handler (controller/handler)
                                                    |               |
                                                    |               |--uses--> Inject/ProviderRegistry -> provides instances

Request Flow (每次请求):
IOLoop -> create_context() -> resolve request-scoped providers -> Handler executes -> response -> context cleanup

图例:
- register(): 从发现的模块进行 provider 注册
- add_registry(): injection registry 获取 provider registries 以解析注入标记
- register_services(): 服务发现和 on_init 序列
```


## 常见注意事项与故障排查

- 注入返回 `None` 通常表示 provider 未注册到 `ProviderRegistry`，或 `InjectionRegistry` 未包含该 registry。
- 循环依赖会抛出 `CircularDependencyError`；检查服务依赖并考虑重构（接口/事件）以打破循环。

