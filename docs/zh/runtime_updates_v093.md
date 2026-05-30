title: "运行时整合概览"
slug: "runtime-updates-v093"
module: []
tags: ["release", "architecture", "testing"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/runtime_updates_v093.md"
related_tests: ["tests/web/test_web_runtime.py", "tests/di/test_core_constructor_injection.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# 运行时整合概览

本文汇总当前代码库与文档已落地的三次大更新。

## 1. IoC/DI 整合

当前容器模型以 `ApplicationContext` 为中心，并通过 `cullinan.core` 作为公开入口。

### 变更内容

- `cullinan.core` 成为容器、生命周期与上下文 API 的公开门面
- `ApplicationContext.refresh()` / `shutdown()` 成为主要生命周期转换点
- `cullinan.core.container.*` 下的兼容模块现在转发到同一套核心实现
- 旧构造器注入辅助 API 仅保留兼容意义，不再是推荐模型

### 当前应使用

- `@service`、`@controller`
- `Inject()` 与 `InjectByName()`
- 需要显式注册或做集成时直接使用 `ApplicationContext`

## 2. Web Runtime 整合

Web 栈已围绕 `cullinan.gateway` 中的传输无关运行时完成重组。

### 变更内容

- `WebRequest`、`WebResponse`、`WebAdapter` 定义了当前公开 HTTP 抽象
- `Router`、`Dispatcher`、`MiddlewarePipeline`、`ExceptionHandler` 统一经由 gateway 门面暴露
- `cullinan.gateway.web_core` 承载共享请求/响应模型
- 适配器独立在 `cullinan.adapter` 中（`TornadoAdapter`、`ASGIAdapter`）

### 迁移含义

新代码应直接使用统一后的 Web Runtime 名称；旧的 request / response / adapter 名称不再是主要公开接口。

## 3. 测试体系优化

仓库测试工作流已围绕 pytest 完成清理与标准化。

### 变更内容

- 唯一正式入口：`.venv\Scripts\python -m pytest`
- 测试发现规则由 `pytest.ini` 统一定义
- `tests/` 下按主题组织测试
- 旧脚本式验证文件已删除或改造成真正的 pytest 测试

### 当前目录

- `tests/core`
- `tests/di`
- `tests/web`
- `tests/integration`
- `tests/regression`
- `tests/compat`

## 后续阅读

- [架构设计](architecture.md)
- [依赖注入指南](dependency_injection_guide.md)
- [Web Runtime 指南](web_runtime_guide.md)
- [测试与验证](testing.md)
