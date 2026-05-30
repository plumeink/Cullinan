title: "cullinan.core"
slug: "modules-core"
module: ["cullinan.core"]
tags: ["api", "module", "core"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/modules/core.md"
related_tests: ["tests/di/test_core_constructor_injection.py", "tests/integration/test_service_lifecycle_integration.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# cullinan.core

`cullinan.core` 是 Cullinan 统一容器、生命周期与请求上下文 API 的公开门面。

## 推荐入口

### 容器与定义

- `ApplicationContext`
- `Definition`
- `ScopeType`
- `get_application_context()`
- `set_application_context()`

### 装饰器层

- `service`
- `controller`
- `component`
- `Inject`
- `InjectByName`
- `Lazy`

### 生命周期与请求上下文

- `get_lifecycle_manager()`
- `reset_lifecycle_manager()`
- `create_context()`
- `destroy_context()`
- `get_current_context()`
- `set_current_context()`

## 示例

```python
from cullinan.core import ApplicationContext, Definition, ScopeType

ctx = ApplicationContext()
ctx.register(Definition(
    name="Clock",
    factory=lambda c: object(),
    scope=ScopeType.SINGLETON,
    source="docs:Clock",
))
ctx.refresh()
clock = ctx.get("Clock")
ctx.shutdown()
```

## 兼容导出

以下名称仍然存在，但只保留向后兼容意义，不再是主要编程模型：

- `injectable`
- `inject_constructor`
- `InjectionRegistry`
- `get_injection_registry()`
- `reset_injection_registry()`

在当前运行时中，新代码应优先使用 `ApplicationContext` 与基于装饰器的注册方式。

## 另见

- [依赖注入指南](../dependency_injection_guide.md)
- [架构设计](../architecture.md)
