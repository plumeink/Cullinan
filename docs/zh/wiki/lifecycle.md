title: "应用生命周期"
slug: "wiki-lifecycle"
module: ["lifecycle"]
tags: ["wiki", "lifecycle"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/wiki/lifecycle.md"
related_tests: ["tests/integration/test_service_lifecycle_integration.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# 应用生命周期

Cullinan 的生命周期由当前活动的 `ApplicationContext` 驱动。

## 主要阶段

1. **创建上下文** —— 实例化 `ApplicationContext`
2. **注册组件** —— 通过装饰器、扫描器或显式 Definition 完成注册
3. **Refresh** —— 调用 `ctx.refresh()` 构建 eager 状态并执行启动钩子
4. **处理请求** —— request scope 与中间件围绕活动上下文运行
5. **Shutdown** —— 调用 `ctx.shutdown()` 执行销毁钩子并释放受管状态

## 生命周期钩子

受管组件可实现：

- `on_post_construct()`
- `on_startup()`
- `on_shutdown()`
- `on_pre_destroy()`

同样支持 `_async` 后缀的异步版本。

## 顺序控制

若组件必须先于其他组件启动或延后关闭，可实现 `get_phase()`。较低 phase 会更早启动、但在关闭时更晚执行。

## 请求作用域

request scope 依赖绑定到当前请求上下文。框架会在请求处理前后自动创建和释放该上下文。

## 中间件桥接

应用启动阶段可把旧式 middleware 注册桥接进 gateway pipeline，使历史模块仍能参与请求处理，而新代码统一走 Web Runtime。

## 另见

- [IoC 与 DI](injection.md)
- [Web Runtime 指南](../web_runtime_guide.md)
