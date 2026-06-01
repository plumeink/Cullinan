title: "API 参考"
slug: "reference-index"
module: []
tags: ["docs", "reference", "knowledge-base"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/reference/index.md"
related_tests: []
related_examples: []
estimate_pd: 1.0
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# API 参考

这个知识域面向**查阅**，而不是面向 onboarding。

当你已经知道自己要找哪个符号、哪一类 API 或哪个模块族时，
请从这里进入。这里的页面应保持稳定、可检索、职责清晰。

## 主要入口

- [API 参考总览](../api_reference.md) —— 推荐、高级与兼容 API 分层
- `cullinan.app`、`cullinan.application`、`cullinan.core`、`cullinan.controller`、`cullinan.service` 等模块参考

## 查阅规则

- 常规业务应用应优先从顶层 `cullinan` API 开始
- 高级运行时 API 应显式从对应子模块导入
- 兼容模块仍然保留文档，但不再属于默认路径

## 相关知识域

- 需要解释而不是查阅？去 [框架语义](../concepts/index.md)
- 需要步骤式指导？去 [工程实践](../how-to/index.md)
- 需要内部机制？去 [运行时与扩展](../internals/index.md)
