title: "Cullinan 文档"
slug: "docs-home"
module: []
tags: ["docs", "home"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/README.md"
related_tests: []
related_examples: []
estimate_pd: 0.5
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# Cullinan 文档

欢迎使用 Cullinan 文档站点。

> **当前版本：0.93a1**。当前文档已对齐统一的 `cullinan.core` 容器门面、传输无关的 Web Runtime（`WebRequest` / `WebResponse` / `WebAdapter`）以及基于 pytest 的测试体系。

## 重点更新

- [运行时整合概览](runtime_updates_v093.md) —— 汇总 IoC/DI、Web Runtime、测试优化三次更新
- [架构设计](architecture.md) —— 当前框架架构与执行流程
- [依赖注入指南](dependency_injection_guide.md) —— 推荐 DI 用法与兼容层说明
- [Web Runtime 指南](web_runtime_guide.md) —— 传输无关的请求/响应运行时与适配器
- [测试与验证](testing.md) —— 仓库测试入口、目录结构与约定

## Wiki

- [IoC 与 DI（注入）](wiki/injection.md) —— 注入模式速查
- [应用生命周期](wiki/lifecycle.md) —— 启动、refresh、请求作用域与关闭流程
- [RESTful API](wiki/restful_api.md) —— 控制器路由与当前 Web Runtime 响应模型

## 其他参考

- [参数系统指南](parameter_system_guide.md)
- [构建与运行](build_run.md)
- [模块文档](modules/)
- [示例](examples/)
- [API 参考](api_reference.md)

## 语言导航

- 英文文档位于 `docs/`
- 中文文档位于 `docs/zh/`
- 更新页面按相同相对路径维护中英配对

源码与发布历史请访问 [GitHub 仓库](https://github.com/plumeink/Cullinan)。
