title: "Cullinan 知识库"
slug: "docs-home"
module: []
tags: ["docs", "home", "knowledge-base"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/README.md"
related_tests: []
related_examples: []
estimate_pd: 0.5
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# Cullinan 知识库

Cullinan 文档现在按**知识库**组织，而不是把 wiki、模块页、指南、迁移说明混在一起。

> **当前版本：0.93a6.post1**。推荐的应用入口是
> `from cullinan import configure, run`：先从业务装饰器和业务方法开始，
> 只有在应用确实需要时，再进入高级运行时细节。

## 默认学习路径

1. [应用构建](start/index.md)
2. [框架语义](concepts/index.md)
3. [工程实践](how-to/index.md)
4. [API 参考](reference/index.md)

这条路径适用于大多数使用 Cullinan 构建业务应用的开发者。它刻意把高级运行时内部机制
与版本迁移说明放在首读路径之外。

## 六大知识域

### 1. [应用构建](start/index.md)

用于通过推荐公开 API 启动新应用。

- [快速开始](getting_started.md)
- [示例](examples.md)
- [构建与运行](build_run.md)

### 2. [框架语义](concepts/index.md)

用于理解 Cullinan 的工作方式，以及它为什么不鼓励显式 app 风格的手工注册。

- [框架语义规则](framework_semantics.md)
- [架构设计](architecture.md)

### 3. [工程实践](how-to/index.md)

用于回答具体开发任务怎么做。

- [依赖注入指南](dependency_injection_guide.md)
- [Web Runtime 指南](web_runtime_guide.md)
- [参数系统指南](parameter_system_guide.md)
- [测试与验证](testing.md)

### 4. [API 参考](reference/index.md)

用于查符号与查看稳定 API 表面。

- [API 参考总览](api_reference.md)
- [模块参考：app](modules/app.md)
- [模块参考：application](modules/application.md)
- [模块参考：core](modules/core.md)
- [模块参考：controller](modules/controller.md)
- [模块参考：service](modules/service.md)

### 5. [运行时与扩展](internals/index.md)

只有在你明确需要高级运行时或扩展知识时才进入这里。

- [应用运行时模型](wiki/application_runtime.md)
- [扩展开发指南](extension_development_guide.md)
- [扩展快速入门](quick_start_extensions.md)

### 6. [版本迁移](migration/index.md)

用于升级版本或把旧代码对齐到新语义。

- [运行时整合](runtime_updates_v093.md)
- [迁移指南](migration_guide.md)
- [迁移指南 v2](migration_guide_v2.md)
- [0.90 导入迁移](import_migration_090.md)

## 文档治理规则

- 新内容先定义知识角色，再落页
- 教学页、参考页、内部页、迁移页不应混合承担同一个页面的主职责
- 高级主题必须明确标注为高级
- 英文页位于 `docs/`，中文镜像位于 `docs/zh/`，并保持相同相对路径

源码与发布历史请访问 [GitHub 仓库](https://github.com/plumeink/Cullinan)。
