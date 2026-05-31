title: "Cullinan Documentation"
slug: "docs-home"
module: []
tags: ["docs", "home"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/README.md"
related_tests: []
related_examples: []
estimate_pd: 0.5
last_updated: "2026-05-31T00:00:00Z"
pr_links: []

# Cullinan Documentation

Welcome to the Cullinan documentation site.

> **Current version: 0.93a3**. The current documentation reflects the application-first bootstrap (`Application` + `@module`), the unified `cullinan.core` container facade, the transport-agnostic Web Runtime (`WebRequest` / `WebResponse` / `WebAdapter`), and the current pytest-led test workflow.

## Key updates

- [Runtime consolidation overview](runtime_updates_v093.md) — summary of the IoC/DI, application runtime, Web Runtime, and testing updates
- [Architecture](architecture.md) — current framework architecture and execution flow
- [Application runtime model](wiki/application_runtime.md) — module graph, ownership, activation, reload, and draining semantics
- [Dependency Injection Guide](dependency_injection_guide.md) — recommended DI usage and compatibility notes
- [Web Runtime Guide](web_runtime_guide.md) — transport-agnostic request/response runtime and adapters
- [Testing & Verification](testing.md) — repository test entrypoint, layout, and conventions

## Wiki

- [IoC & DI (Injection)](wiki/injection.md) — quick reference for injection patterns
- [Application Runtime Model](wiki/application_runtime.md) — `Application.run()`, `@module`, ownership, and runtime switching
- [Application Lifecycle](wiki/lifecycle.md) — startup, refresh, request scope, and shutdown
- [RESTful API](wiki/restful_api.md) — controller routing plus the current Web Runtime response model

## Additional references

- [Parameter System Guide](parameter_system_guide.md)
- [Build & Run](build_run.md)
- [Modules](modules/)
- [Examples](examples/)
- [API Reference](api_reference.md)

## Language navigation

- English documents live under `docs/`
- Chinese documents live under `docs/zh/`
- Updated pages are maintained as translation pairs with matching relative paths

For source code and release history, visit the [GitHub repository](https://github.com/plumeink/Cullinan).
