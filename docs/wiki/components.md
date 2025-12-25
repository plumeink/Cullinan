title: "Components"
slug: "components"
module: ["cullinan"]
tags: ["components", "architecture"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/wiki/components.md"
related_tests: []
related_examples: []
estimate_pd: 2.0
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# Components

> **Note (v0.90)**: The Core (IoC/DI) component has been redesigned in version 0.90.
> For the new architecture, see [Dependency Injection Guide](../dependency_injection_guide.md).
> The new `ApplicationContext` from `cullinan.core.container` is now the recommended entry point.

This page describes the primary components of Cullinan and their responsibilities, with pointers to the implementation in the `cullinan/` package. The goal is a concise reference that helps contributors and users understand where to look in the source for each subsystem.

Components overview

- Router / URL resolver
  - Responsibility: resolve URL patterns to controller handlers and dispatch requests.
  - Key files: `cullinan/controller/core.py`, `cullinan/controller/registry.py`, `cullinan/controller/__init__.py`.
  - Public symbols: `controller` (decorator), `get_controller_registry`, `url_resolver`.

- Controller layer
  - Responsibility: define controller classes and handler methods; provide request/response abstractions and response pooling utilities.
  - Key files: `cullinan/controller/core.py`, `cullinan/controller/registry.py`, `cullinan/controller/stateless_validator.py`.
  - Public symbols: `Handler`, `ControllerRegistry`, `response_build`, `request_resolver`.

- Request handler & HTTP integration
  - Responsibility: adapt Tornado HTTPServerRequest to controller handlers, manage request parsing and header resolution.
  - Key files: `cullinan/handler/*`, `cullinan/controller/core.py`.
  - Public symbols: `get_handler_registry`, `request_handler`.

- Middleware
  - Responsibility: provide interception points for request/response processing, such as auth, logging, or transformation.
  - Key files: `cullinan/middleware/*`.
  - Notes: middleware is applied in a pipeline; see `middleware` folder for examples and ordering semantics.

- Service (business/service layer)
  - Responsibility: long-lived services that provide functionality to controllers (database access, caching, background jobs).
  - Key files: `cullinan/service/*` (base, decorators, registry).
  - Public symbols: `Service`, `ServiceRegistry`, `service` (decorator), `get_service_registry`.

- Core (IoC / DI / lifecycle / providers / scopes)
  - Responsibility: dependency injection, provider registry, scopes (singleton/transient/request), lifecycle management.
  - Key files: `cullinan/core/*` (`injection.py`, `provider.py`, `registry.py`, `scope.py`, `lifecycle*.py`).
  - Public symbols: `Inject`, `injectable`, `inject_constructor`, `InjectionRegistry`, `ProviderRegistry`, `SingletonScope`, `RequestScope`, `create_context`.

- Application / Startup
  - Responsibility: application lifecycle, service discovery and initialization, orderly startup/shutdown and signal handling.
  - Key files: `cullinan/app.py`, `cullinan/application.py`.
  - Public symbols: `create_app`, `CullinanApplication`, `run` (application entry points).

Examples — quick reference

Minimal controller registration example (conceptual):

```python
from cullinan.controller import controller, get_api

@controller(url='/hello')
class HelloController:
    @get_api(url='')
    def hello(self):
        return {'status': 200, 'body': 'Hello Cullinan'}

# controllers are discovered automatically; the app will route /hello to HelloController
```

Minimal service example (conceptual):

```python
from cullinan.service import Service, service

@service
class MySvc(Service):
    # service logic here
    pass
```

Where to look next

- Walk the tests in `tests/` (for real usage examples and expected behavior). Recommended starting points: `tests/test_core_injection.py`, `tests/test_controller_injection_fix.py`, `tests/test_provider_system.py`.
- Read `docs/wiki/injection.md` for detailed IoC/DI examples and runnable snippets.

Next steps for documentation

- Expand each component subsection with sequence diagrams and concrete code samples extracted from tests.
- Add a small reference table mapping public symbols to file paths (for faster navigation).
