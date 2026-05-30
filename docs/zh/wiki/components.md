title: "组件"
slug: "components"
module: ["cullinan"]
tags: ["components", "architecture"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/wiki/components.md"
related_tests: ["tests/web/test_web_runtime.py", "tests/integration/test_service_lifecycle_integration.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# 组件

本文给出 Cullinan 当前主要运行时组件的高层地图。

## 运行时概览

### 1. 核心容器

- 职责：依赖注册、解析、作用域、生命周期、请求上下文
- 主包：`cullinan.core`
- 关键 API：`ApplicationContext`、`Definition`、`ScopeType`、`Inject`、`InjectByName`

### 2. 服务层

- 职责：业务逻辑与受框架管理的长生命周期服务
- 主包：`cullinan.service`
- 关键 API：`service`、`Service`

### 3. 控制器层

- 职责：路由声明与处理器方法
- 主包：`cullinan.controller`
- 关键 API：`controller`、`get_api`、`post_api`、`response_build`

### 4. Web Runtime

- 职责：标准化请求/响应模型、路由、分发、中间件、异常处理
- 主包：`cullinan.gateway`
- 关键 API：`WebRequest`、`WebResponse`、`Router`、`Dispatcher`、`MiddlewarePipeline`、`WebRuntime`

### 5. 适配器层

- 职责：把 Web Runtime 绑定到具体服务器环境
- 主包：`cullinan.adapter`
- 关键 API：`WebAdapter`、`TornadoAdapter`、`ASGIAdapter`

### 6. 参数与模型绑定

- 职责：把 path/query/body/header/file 输入映射为处理器参数
- 主包：`cullinan.params`
- 关键 API：`Path`、`Query`、`Body`、`Header`、`File`

## 建议阅读顺序

1. [架构设计](../architecture.md)
2. [依赖注入指南](../dependency_injection_guide.md)
3. [Web Runtime 指南](../web_runtime_guide.md)
4. [测试与验证](../testing.md)
