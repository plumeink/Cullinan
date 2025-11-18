---
title: "Architecture Overview"
slug: "architecture"
module: ["cullinan.core"]
tags: ["architecture", "ioc", "design"]
author: "Plumeink"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/wiki/architecture.md"
related_tests: []
related_examples: []
estimate_pd: 2.5
last_updated: "2025-11-18T00:00:00Z"
pr_links: []
---

# Architecture Overview

This document records Cullinan's high-level architecture based on the source implementation (facts from code). It covers component responsibilities, module interactions, the startup/request/shutdown sequence, and provides a plain-text ASCII architecture diagram for environments without diagram rendering.

## Key components (quick reference)

| Component | Location (example) | Responsibility |
| --- | --- | --- |
| Core (IoC/DI) | `cullinan/core/*` | Provides DI primitives (Provider, Registry, Scope), lifecycle hooks (`on_init`/`on_shutdown`) and context management (`RequestScope`). |
| Service layer | `cullinan/service/*` | Defines long-lived services (typically singletons), implements init/shutdown hooks and provides business capabilities. |
| Controller / Handler | `cullinan/controller/*`, `cullinan/handler/*` | Route registration, request parsing, response construction and access logging. Handlers obtain services via DI. |
| Application | `cullinan/app.py`, `cullinan/application.py` | Coordinates startup/shutdown: registers providers, discovers services/controllers, initializes services, starts Tornado IOLoop and installs signal handlers. |
| Middleware | `cullinan/middleware/*` | Pluggable request/response processing chain (logging, auth, monitoring, etc.). |


## Module interactions (brief)

- The Application coordinates the system: it invokes the ModuleScanner to discover controllers, services and providers. Providers discovered are registered into a `ProviderRegistry`, which is then added to the `InjectionRegistry` to make injection points resolvable.
- `ServiceRegistry` manages service dependency ordering and invokes `on_init()` during startup; it ensures services become available before request handling commences.
- At request time the framework creates a `RequestContext` (via `create_context()`), which enables `RequestScope`; handlers resolve dependencies (property or constructor injection) within that context and may use request-scoped or singleton instances as appropriate.


## Startup / request / shutdown sequence (summary)

1. Application constructed: `create_app()` or `CullinanApplication()`.
2. Module scanning: discover controllers, services, providers (or rely on explicit registration).
3. Injection setup: register `ProviderRegistry` instances and add them to the `InjectionRegistry`.
4. Service initialization: `ServiceRegistry` resolves dependency order and instantiates services, calling `on_init`. Failures are logged and may abort startup.
5. Start IOLoop: call `IOLoop.start()` to accept requests.
6. Request handling: for each request create a `RequestContext` -> resolve injections -> execute handler -> middleware post-processing -> cleanup `RequestContext`.
7. Shutdown: on SIGINT/SIGTERM or manual `shutdown()`, execute registered shutdown handlers and service `on_shutdown` hooks in order, stop the IOLoop and exit.


## Architecture interaction diagram (ASCII, tab-aligned)

Below is a plain-text diagram using tabs for column alignment so it renders sensibly in code blocks and in places without Mermaid support.

```
Application		ModuleScanner		ProviderRegistry	InjectionRegistry	ServiceRegistry	Tornado IOLoop
-----------		------------		----------------	-----------------	--------------	---------------
create_app() -->	 scan() ----> 	 register() ---->	 add_registry() -->	 register_services() --> start()
                                                    |
                                                    |--dispatch--> Handler (controller/handler)
                                                    |               |
                                                    |               |--uses--> Inject/ProviderRegistry -> provides instances

Request Flow (per request):
IOLoop -> create_context() -> resolve request-scoped providers -> Handler executes -> response -> context cleanup

Legend:
- register(): provider registration from discovered modules
- add_registry(): injection registry gets provider registries to resolve inject markers
- register_services(): service discovery and on_init sequence
```


## Common notes and troubleshooting

- Injection returning `None` usually indicates the provider is not registered in a `ProviderRegistry` or the `InjectionRegistry` does not include that registry.
- Circular dependencies raise `CircularDependencyError`; inspect service dependencies and consider refactoring (interfaces/events) to break cycles.
- In tests, use `reset_injection_registry()` and explicit `ProviderRegistry` setup to ensure isolation between tests.


## Artifacts & next steps

- Diagram assets placeholder: `docs/work/architecture_assets/` (store Mermaid/PlantUML/PNG/SVG here).
- Recommendation: produce a Mermaid or PlantUML diagram from the ASCII diagram and place it under `docs/work/architecture_assets/` so MkDocs can render it on the site.

---

If you want I can (A) generate a Mermaid version and insert it into this file, or (B) generate PNG/SVG via mermaid-cli/PlantUML and add the static image under `docs/work/architecture_assets/`. Tell me which option to proceed with.
