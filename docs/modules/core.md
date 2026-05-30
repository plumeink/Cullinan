title: "cullinan.core"
slug: "modules-core"
module: ["cullinan.core"]
tags: ["api", "module", "core"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/modules/core.md"
related_tests: ["tests/di/test_core_constructor_injection.py", "tests/integration/test_service_lifecycle_integration.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# cullinan.core

`cullinan.core` is the public facade for Cullinan's unified container, lifecycle, and request-context APIs.

## Recommended entrypoints

### Container and definitions

- `ApplicationContext`
- `Definition`
- `ScopeType`
- `get_application_context()`
- `set_application_context()`

### Decorator surface

- `service`
- `controller`
- `component`
- `Inject`
- `InjectByName`
- `Lazy`

### Lifecycle and request context

- `get_lifecycle_manager()`
- `reset_lifecycle_manager()`
- `create_context()`
- `destroy_context()`
- `get_current_context()`
- `set_current_context()`

## Example

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

## Compatibility exports

The following names still exist for backward compatibility, but they are not the primary programming model:

- `injectable`
- `inject_constructor`
- `InjectionRegistry`
- `get_injection_registry()`
- `reset_injection_registry()`

In the current runtime, new code should favor `ApplicationContext` plus decorator-based registration.

## See also

- [Dependency Injection Guide](../dependency_injection_guide.md)
- [Architecture](../architecture.md)
