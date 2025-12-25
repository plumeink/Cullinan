title: "组件"
slug: "components"
module: ["cullinan"]
tags: ["components", "architecture"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/wiki/components.md"
related_tests: []
related_examples: []
estimate_pd: 2.0
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# 组件

> **说明（v0.90）**：核心（IoC/DI）组件已在 0.90 版本中重新设计。
> 新架构请参阅 [IoC/DI 2.0 架构](ioc_di_v2.md)。
> `cullinan.core.container` 中的新 `ApplicationContext` 是推荐的入口点。

本文介绍 Cullinan 的主要组件及其职责，并给出实现代码的指向（`cullinan/` 包）。目标是为贡献者与使用者提供一个简明索引，方便定位源码子系统。

组件概览

- 路由 / URL 解析器
  - 职责：将 URL 模式解析为控制器处理函数并分发请求。
  - 关键文件：`cullinan/controller/core.py`、`cullinan/controller/registry.py`、`cullinan/controller/__init__.py`。
  - 公有符号：`controller`（装饰器）、`get_controller_registry`、`url_resolver`。

- 控制器层
  - 职责：定义控制器类与处理器方法；提供请求/响应抽象与响应池工具。
  - 关键文件：`cullinan/controller/core.py`、`cullinan/controller/registry.py`、`cullinan/controller/stateless_validator.py`。
  - 公有符号：`Handler`、`ControllerRegistry`、`response_build`、`request_resolver`。

- 请求处理与 HTTP 集成
  - 职责：把 Tornado 的 `HTTPServerRequest` 适配为控制器处理器，管理请求解析与头部解析。
  - 关键文件：`cullinan/handler/*`、`cullinan/controller/core.py`。
  - 公有符号：`get_handler_registry`、`request_handler`。

- 中间件
  - 职责：提供请求/响应处理的拦截点，如认证、日志或变换。
  - 关键文件：`cullinan/middleware/*`。
  - 说明：中间件按流水线应用；详见 `middleware` 目录中的样例与顺序语义。

- 服务（业务层）
  - 职责：为控制器提供长期运行的服务（数据库访问、缓存、后台任务等）。
  - 关键文件：`cullinan/service/*`（base、decorators、registry）。
  - 公有符号：`Service`、`ServiceRegistry`、`service`（装饰器）、`get_service_registry`。

- 核心（IoC / DI / 生命周期 / provider / scope）
  - 职责：依赖注入、提供者注册、作用域（singleton/transient/request）、生命周期管理。
  - 关键文件：`cullinan/core/*`（`injection.py`、`provider.py`、`registry.py`、`scope.py`、`lifecycle*.py`）。
  - 公有符号：`Inject`、`injectable`、`inject_constructor`、`InjectionRegistry`、`ProviderRegistry`、`SingletonScope`、`RequestScope`、`create_context`。

- 应用 / 启动
  - 职责：应用生命周期、服务发现与初始化、有序的启动/关闭与信号处理。
  - 关键文件：`cullinan/app.py`、`cullinan/application.py`。
  - 公有符号：`create_app`、`CullinanApplication`、`run`（应用入口）。

示例 — 快速参考

最小的控制器注册示例（概念性）：

```python
from cullinan.controller import controller, get_controller_registry

@controller(path='/hello')
def hello_handler(request):
    return {'status': 200, 'body': 'Hello Cullinan'}

# 控制器被扫描或注册；应用会将 /hello 路由到 hello_handler
```

最小的服务示例（概念性）：

```python
from cullinan.service import Service, service, get_service_registry

@service
def MySvc():
    # 注册服务
    pass

svc_registry = get_service_registry()
```

接下来应查看的地方

- 阅读 `tests/` 下的测试以获取真实用法与期望行为：推荐起点 `tests/test_core_injection.py`、`tests/test_controller_injection_fix.py`、`tests/test_provider_system.py`。
- 阅读 `docs/wiki/injection.md` 以获取 IoC/DI 的详细示例与可运行片段。

文档下一步

- 扩展每个组件小节，加入时序图与从测试中提取的具体代码样例。
- 增加一个公有符号到文件路径的映射表，便于快速导航源码。
