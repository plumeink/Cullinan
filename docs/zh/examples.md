title: "示例与指引"
slug: "examples"
module: []
tags: ["examples"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/examples.md"
related_tests: ["tests/integration/test_examples_public_guides.py"]
related_examples: ["examples/minimal_app", "examples/controller_service_inject", "examples/middleware_and_module", "examples/parameter_handling", "examples/testing_flow"]
estimate_pd: 1.5
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# 示例与指引

本页是仓库内可运行示例的正式导航入口。现在唯一的示例代码主入口是项目根目录
`examples/`，而不是 `docs/examples/`，也不再是早期的单文件 demo。

> **推荐心智：** 先写装饰器式业务代码，声明 `RootModule`，调用 `configure(root_module=...)`，
> 再让 `run()` 或 `get_asgi_app()` 完成运行时装配。<br>
> **延伸阅读：** [快速开始](getting_started.md)、[构建与运行](build_run.md)、
> [参数系统指南](parameter_system_guide.md)、[测试与验证](testing.md)

## 推荐阅读顺序

1. `examples/minimal_app/` —— 最短公开入口
2. `examples/controller_service_inject/` —— `@service`、`@controller` 与 `Inject()` 的业务分层
3. `examples/middleware_and_module/` —— `@module` 与 `@middleware` 的协同语义
4. `examples/parameter_handling/` —— `Path`、`Query`、`Body` 的控制器方法参数绑定
5. `examples/testing_flow/` —— 不启动真实服务进程时的 `configure(...) + get_asgi_app()` 测试流

## 示例地图

| 示例 | 主要讲什么 | 运行命令 | 源码 |
| --- | --- | --- | --- |
| `examples/minimal_app/` | 使用 `configure(root_module=...) + run()` 组织最小应用 | `python -m examples.minimal_app` | [在 GitHub 查看](https://github.com/plumeink/Cullinan/tree/main/examples/minimal_app) |
| `examples/controller_service_inject/` | `service/controller` 分层与类型驱动的 `Inject()` 注入 | `python -m examples.controller_service_inject` | [在 GitHub 查看](https://github.com/plumeink/Cullinan/tree/main/examples/controller_service_inject) |
| `examples/middleware_and_module/` | 模块边界归属与中间件管线扩展 | `python -m examples.middleware_and_module` | [在 GitHub 查看](https://github.com/plumeink/Cullinan/tree/main/examples/middleware_and_module) |
| `examples/parameter_handling/` | 控制器方法上的 `Path`、`Query`、`Body` | `python -m examples.parameter_handling` | [在 GitHub 查看](https://github.com/plumeink/Cullinan/tree/main/examples/parameter_handling) |
| `examples/testing_flow/` | 基于公开 API 的 ASGI 测试流 | `python -m pytest examples/testing_flow/test_app.py -q` | [在 GitHub 查看](https://github.com/plumeink/Cullinan/tree/main/examples/testing_flow) |

## 为什么要重构示例

旧示例容易把开发者带回“手工注册 app”的思路。新的示例集刻意把
Cullinan 当前想表达的概念放在最前面：

- 业务装饰器优先，而不是显式 app 装配优先
- 当结构和归属重要时，用 `RootModule` 表达运行时边界
- 类型契约清晰时，默认优先使用 `Inject()`
- 把参数绑定写在控制器方法上，而不是先教底层 request plumbing
- 通过公开 API 做测试，而不是依赖内部启动捷径

## 补充说明

- 根目录 `examples/README.md` 会同步这条学习链路，方便直接看仓库的开发者。
- 也可以直接从 [`examples/`](https://github.com/plumeink/Cullinan/tree/main/examples) 浏览已入库的示例源码。
- `tests/integration/test_examples_public_guides.py` 会对当前维护的示例做 smoke test。
- 如果你第一次接触 Cullinan，建议先完成 `examples/minimal_app/`，再进入
  `examples/controller_service_inject/`。
