title: "Application Runtime Model"
slug: "wiki-application-runtime"
module: ["cullinan.application_model"]
tags: ["wiki", "application", "runtime", "module"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/wiki/application_runtime.md"
related_tests: ["tests/core/test_application_model_refactor.py", "tests/core/test_decorators.py", "tests/integration/test_adapter_integration.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-31T00:00:00Z"
pr_links: []

# Application Runtime Model

This page explains the application runtime introduced around
`cullinan.application_model` and re-exported from `cullinan`.
Cullinan's intended experience is decorator-first business development: the
runtime assembles what your modules declare, instead of asking you to wire a
manual app object step by step.

For the runtime contracts that now fail fast or warn, see [Framework Semantics](../framework_semantics.md). In particular, `Application.run()` assumes component decorators have already executed during module import, and `refresh()` marks the end of structural registration.

## Core concepts

- `Application` owns one root module graph, one `ApplicationContext`, and one `WebRuntime`
- `@module` declares a structured boundary for owned Python packages, reload, draining, and hot-pluggable runtime behavior
- `Runtime` is the mutable record for a validated / warmed application candidate
- `current_app()` resolves the active application and prefers the request-bound snapshot during draining

## Typical runtime assembly

```python
from cullinan import Application, controller, get_api, module, service
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
        return {"message": self.greeting_service.greet()}


@module
class RootModule:
    pass


app = Application.run(RootModule)
```

## Module graph and ownership

Each module contributes:

- `imports` — child or sibling modules included in the root graph
- `packages` — Python package prefixes owned by that module
- `ownership_overrides` — explicit ownership for intentionally shared packages
- `warmup` / `health_checks` — hooks that run during build and validation

Component ownership is resolved from decorator metadata captured on
`@service`, `@controller`, `@component`, and `@provider`. If the same component
matches multiple module package prefixes at the same depth, startup fails until
you provide `ownership_overrides`.

## Build and activation flow

`Application.run()` performs these stages:

1. Discover runtime boundaries and import owned Python modules.
2. Rebuild pending registrations from decorator metadata.
3. Assemble an `ApplicationContext` and `WebRuntime`.
4. Validate, refresh, and warm the runtime.
5. Atomically bind the new application as active.

## Reload and draining

`Application.reload()` creates a fresh application candidate from the same root
module. If activation succeeds:

1. the new runtime becomes active immediately
2. the previous runtime enters `DRAINING`
3. in-flight requests keep their request-bound app snapshot
4. the old runtime closes only after request counts drop to zero

This is why `current_app()` may return an older application inside a draining
request even after a newer runtime is already active globally.

## Adapters and request binding

`ASGIAdapter` and `TornadoAdapter` bind the runtime into the current request
context before dispatch. That request binding enables:

- request-scoped dependency resolution against the correct application
- `current_app()` inside controllers and middleware
- safe draining while older requests are still finishing

## When to use ApplicationContext directly

Keep using `ApplicationContext` directly when you need low-level container
integration, explicit registration, or compatibility-oriented bootstrapping. For
new application code, start from decorators and use `Application` plus
`@module` when you need explicit runtime boundaries.

## Related documents

- [cullinan.application module](../modules/application.md)
- [Application Lifecycle](lifecycle.md)
- [Components](components.md)
