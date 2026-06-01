title: "工程实践"
slug: "engineering-practices"
module: []
tags: ["docs", "how-to", "knowledge-base"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/how-to/index.md"
related_tests: ["tests/core/test_developer_experience.py", "tests/web/test_openapi_generator.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# 工程实践

这部分按**开发任务**组织，而不是按内部模块名组织。

当你已经理解推荐启动路径和框架语义后，就可以从这里开始回答
“我该如何在 Cullinan 里完成某件事”。

## 常见任务

- [依赖注入指南](../dependency_injection_guide.md) —— 选择并使用注入原语
- [Web Runtime 指南](../web_runtime_guide.md) —— 在公开运行时表面上构建 Web API
- [参数系统指南](../parameter_system_guide.md) —— 使用类型化请求参数
- [测试与验证](../testing.md) —— 遵循仓库测试工作流
- [构建与运行](../build_run.md) —— 本地运行与构建约定

## 知识角色

这里的页面是实践指南，不应再次承担以下职责：

- 底层 runtime 内部机制
- 历史迁移说明
- 全量 API 符号索引

这些内容分别去 [运行时与扩展](../internals/index.md)、
[版本迁移](../migration/index.md) 和 [API 参考](../reference/index.md)。
