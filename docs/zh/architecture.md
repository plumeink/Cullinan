# Cullinan 框架架构

> **版本**：0.93a1  
> **最后更新**：2026-05-30  
> **状态**：已更新

## 概览

Cullinan 是一个面向 Tornado 的应用框架，当前运行时围绕三条已经整合完成的主线组织：

1. **统一容器门面** —— `cullinan.core` 是公开的 IoC/DI 入口。
2. **传输无关的 Web Runtime** —— `cullinan.gateway` 承载 `WebRequest`、`WebResponse`、路由、分发、中间件与异常处理。
3. **pytest 优先的验证体系** —— 仓库测试统一收敛到 `tests/` 目录和单一 pytest 入口。

## 架构分层

```text
应用代码
├── @service / @controller / @component
├── 使用 get_api/post_api/... 的控制器方法
└── 业务服务与中间件

框架门面
├── cullinan.core      -> ApplicationContext、作用域、生命周期、请求上下文
├── cullinan.gateway   -> WebRequest、WebResponse、Router、Dispatcher、WebRuntime
├── cullinan.adapter   -> WebAdapter、TornadoAdapter、ASGIAdapter
└── cullinan.params    -> Path、Query、Body、Header、File、模型解析

运行时执行
├── 模块扫描与显式注册
├── ApplicationContext.refresh()
├── Gateway pipeline + dispatcher
├── 适配器层请求/响应转换
└── ApplicationContext.shutdown()
```

## 核心容器模型

`cullinan.core` 暴露公开容器 API。`ApplicationContext` 是注册、解析、refresh 与 shutdown 的唯一运行时入口。

### 主要职责

- 注册依赖定义
- 解析 singleton / prototype / request 作用域实例
- 在 `refresh()` 与 `shutdown()` 期间驱动生命周期钩子
- 保存框架集成使用的当前活动应用上下文

### 公开流程

```python
from cullinan.core import ApplicationContext, set_application_context

ctx = ApplicationContext()
set_application_context(ctx)

# 注册可来自装饰器、扫描器或显式 Definition
ctx.refresh()
...
ctx.shutdown()
```

旧的 `cullinan.core.container.*` 模块现在仅保留为薄转发层，不再维护独立状态。

## 依赖注入与生命周期

装饰器层（`@service`、`@controller`、`Inject`、`InjectByName`）最终都归并到统一容器模型。

### 推荐用法

- 普通业务代码优先使用 `@service` 和 `@controller`
- 字段注入优先使用 `Inject()` 以获得类型安全
- 需要按名称解析或规避循环导入时使用 `InjectByName()`
- 自定义工厂或第三方集成场景直接使用 `ApplicationContext`

### 生命周期钩子

所有受管组件共享同一套生命周期约定：

- `on_post_construct()`
- `on_startup()`
- `on_shutdown()`
- `on_pre_destroy()`

支持追加 `_async` 的异步版本；可通过 `get_phase()` 影响执行顺序。

## Web Runtime

当前 Web 栈以 `cullinan.gateway.web_core` 及其对外导出的 `cullinan.gateway` 门面为核心。

### 公开运行时对象

- `WebRequest` —— 标准化请求对象
- `WebResponse` —— 可在写回前冻结的响应构建器
- `Router` —— 路由注册与匹配
- `Dispatcher` —— 请求分发与返回值处理
- `MiddlewarePipeline` —— 洋葱模型中间件链
- `ExceptionHandler` —— 异常到响应的转换器
- `WebRuntime` —— 活动运行时状态与切换控制

### 适配器边界

服务器集成位于 `cullinan.adapter`：

- `WebAdapter` —— 公共适配器协议
- `TornadoAdapter` —— Tornado 集成
- `ASGIAdapter` —— ASGI 集成

这种分层让请求处理逻辑不再绑定单一服务器实现。

## 请求流程

1. 应用启动时创建并保存 `ApplicationContext`。
2. 模块扫描注册服务与控制器。
3. `ctx.refresh()` 解析 eager 组件并执行启动钩子。
4. Gateway pipeline 接收已归一化的 `WebRequest`。
5. `Dispatcher` 匹配路由、解析参数、调用处理器，并生成 `WebResponse`。
6. 具体适配器把响应写回 Tornado 或 ASGI。
7. 关闭阶段调用 `ctx.shutdown()` 并完成所有受管生命周期清理。

## 测试策略

仓库当前以 pytest 作为唯一正式测试运行器。

- 仓库正式命令：`.venv\Scripts\python -m pytest`
- 共享测试引导位于 `tests/conftest.py`
- 测试目录按主题划分：`tests/core`、`tests/di`、`tests/web`、`tests/integration`、`tests/regression`、`tests/compat`

详见 [测试与验证](testing.md)。

## 相关文档

- [运行时整合概览](runtime_updates_v093.md)
- [依赖注入指南](dependency_injection_guide.md)
- [Web Runtime 指南](web_runtime_guide.md)
- [测试与验证](testing.md)
