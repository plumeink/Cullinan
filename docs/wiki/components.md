title: "Components"
slug: "components"
module: ["cullinan"]
tags: ["components", "architecture"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/wiki/components.md"
related_tests: ["tests/web/test_web_runtime.py", "tests/integration/test_service_lifecycle_integration.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# Components

This page gives a current high-level map of Cullinan's main runtime components.

## Runtime overview

### 1. Core container

- Responsibility: dependency registration, resolution, scopes, lifecycle, request context
- Main package: `cullinan.core`
- Key APIs: `ApplicationContext`, `Definition`, `ScopeType`, `Inject`, `InjectByName`

### 2. Service layer

- Responsibility: business logic and long-lived framework-managed services
- Main package: `cullinan.service`
- Key APIs: `service`, `Service`

### 3. Controller layer

- Responsibility: route declaration and handler methods
- Main package: `cullinan.controller`
- Key APIs: `controller`, `get_api`, `post_api`, `response_build`

### 4. Web Runtime

- Responsibility: normalized request/response model, routing, dispatch, middleware, exceptions
- Main package: `cullinan.gateway`
- Key APIs: `WebRequest`, `WebResponse`, `Router`, `Dispatcher`, `MiddlewarePipeline`, `WebRuntime`

### 5. Adapters

- Responsibility: bind the Web Runtime to a specific server environment
- Main package: `cullinan.adapter`
- Key APIs: `WebAdapter`, `TornadoAdapter`, `ASGIAdapter`

### 6. Parameters and model binding

- Responsibility: map path/query/body/header/file inputs into handler arguments
- Main package: `cullinan.params`
- Key APIs: `Path`, `Query`, `Body`, `Header`, `File`

## Suggested reading order

1. [Architecture](../architecture.md)
2. [Dependency Injection Guide](../dependency_injection_guide.md)
3. [Web Runtime Guide](../web_runtime_guide.md)
4. [Testing & Verification](../testing.md)
