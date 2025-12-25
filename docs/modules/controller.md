title: "cullinan.controller"
slug: "modules-controller"
module: ["cullinan.controller"]
tags: ["api", "module", "controller"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/modules/controller.md"
related_tests: ["tests/test_controller_injection_fix.py","tests/test_controller_with_methods.py"]
related_examples: ["examples/controller_di_middleware.py"]
estimate_pd: 1.5
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# cullinan.controller

> **Note (v0.90)**: Controller DI is now managed by `ApplicationContext`.
> For the new IoC/DI 2.0 architecture, see [Dependency Injection Guide](../dependency_injection_guide.md).

Summary: Controller registration, lifecycle, and injection into controller instances. Document usage patterns and common pitfalls.

## Public API (auto-generated)

<!-- generated: docs/work/generated_modules/cullinan_controller.md -->

### cullinan.controller

| Name | Kind | Signature / Value |
| --- | --- | --- |
| `controller` | function | `controller(**kwargs) -> Callable` |
| `get_controller_registry` | function | `get_controller_registry() -> cullinan.controller.registry.ControllerRegistry` |
| `get_header_registry` | function | `get_header_registry() -> cullinan.controller.core.HeaderRegistry` |
| `request_resolver` | function | `request_resolver(self, url_param_key_list: Optional[Sequence] = None, url_param_value_list: Optional[Sequence] = None, query_param_names: Optional[Sequence] = None, body_param_names: Optional[Sequence] = None, file_param_key_list: Optional[Sequence] = None) -> Tuple[Optional[dict], Optional[dict], Optional[dict], Optional[dict]]` |
| `reset_controller_registry` | function | `reset_controller_registry() -> None` |
| `response_build` | function | `response_build(**kwargs) -> cullinan.controller.core.StatusResponse` |

## Example: register a simple controller

```python
from cullinan.controller import controller, get_controller_registry

@controller(path='/hello')
def hello(request):
    return {'status': 200, 'body': 'Hello World'}

# Optionally register directly into registry (usually auto-discovered)
registry = get_controller_registry()
registry.register(r'/hello', hello)
```

Notes:
- Use the `controller` decorator for route handlers; the framework supports automatic discovery via module scanning or explicit registry registration.
- If handlers need DI, use `@injectable` classes or property injection and ensure providers are registered before app startup.
