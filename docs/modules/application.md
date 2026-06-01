title: "cullinan.application module"
slug: "modules-application"
module: ["cullinan.application"]
tags: ["api", "module", "application"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/modules/application.md"
related_tests: ["tests/core/test_application_model_refactor.py", "tests/core/test_decorators.py", "tests/di/test_global_container_manager.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-31T00:00:00Z"
pr_links: []

# cullinan.application

`cullinan.application` exposes the recommended runtime-assembly surface for
new Cullinan applications:

- `Application.run(RootModule)` builds, warms, and activates one assembled runtime
- `@module` declares a boundary when you need module ownership, reload, and hot-pluggable runtime behavior
- `current_app()` returns the active application, and prefers the request
  snapshot while an older runtime is draining
- legacy `run(handlers=None, engine=None)` remains available for compatibility

The bootstrap contract also depends on the framework semantics documented in [Framework Semantics](../framework_semantics.md): component discovery is import-executed, automatic scanning only guarantees module-top-level decorated components, and structural registration freezes after `refresh()`.

In practice, most application code starts from business decorators and methods.
`@module` is not a manual app-registration center; it is the structured boundary
that keeps ownership, reload, draining, and runtime switching explicit and stable.

## Recommended bootstrap

```python
from cullinan import Application, controller, current_app, get_api, module, service
from cullinan.core import Inject


@service
class GreetingService:
    def greet(self) -> str:
        return "hello"


@controller(url="/api")
class GreetingController:
    greeting_service: GreetingService = Inject()

    @get_api(url="/whoami")
    def whoami(self):
        return {
            "root": current_app().root_module.__name__,
            "message": self.greeting_service.greet(),
        }


@module
class RootModule:
    pass


app = Application.run(RootModule)
```

## Module ownership and boundaries

`@module` uses Python package ownership to discover components. When a component
matches more than one module package, startup fails fast. Resolve intentional
overlap with `ownership_overrides`.

```python
@module(
    imports=[SharedModule, OrdersModule],
    ownership_overrides={"myapp.shared": SharedModule},
)
class RootModule:
    pass
```

## Runtime switching

`Application.reload()` builds a fresh candidate runtime, validates and warms it,
then atomically switches the active application. The previous runtime enters
draining state, and `current_app()` keeps returning the request-bound snapshot
until the in-flight request ends.

## Compatibility note

`ApplicationContext` remains the low-level container/runtime primitive. Existing
code using `register()`, `refresh()`, `get()`, or the legacy
`cullinan.application.run()` entrypoint continues to work, but new application
setup should start from business decorators and use `Application` plus `@module`
when it needs explicit runtime boundaries.

## Related documents

- [Application Runtime Model](../wiki/application_runtime.md)
- [Application Lifecycle](../wiki/lifecycle.md)
