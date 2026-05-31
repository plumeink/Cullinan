title: "Runtime consolidation overview"
slug: "runtime-updates-v093"
module: []
tags: ["release", "architecture", "testing"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/runtime_updates_v093.md"
related_tests: ["tests/core/test_application_model_refactor.py", "tests/integration/test_adapter_integration.py", "tests/web/test_web_runtime.py", "tests/di/test_core_constructor_injection.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-31T00:00:00Z"
pr_links: []

# Runtime consolidation overview

This page summarizes the four major updates currently reflected in the codebase and documentation.

## 1. IoC/DI consolidation

The container model is now centered on `ApplicationContext` and publicly surfaced through `cullinan.core`.

### What changed

- `cullinan.core` became the public facade for container, lifecycle, and context APIs
- `ApplicationContext.refresh()` / `shutdown()` are the primary lifecycle transitions
- compatibility modules under `cullinan.core.container.*` now forward to the same core implementation
- legacy constructor-injection helpers are compatibility shims, not the recommended model

### What to use now

- `@service`, `@controller`
- `Inject()` and `InjectByName()`
- `ApplicationContext` for explicit registration or integration work

## 2. Application-first runtime

Cullinan now exposes an application-first bootstrap model in `cullinan.application_model`
and re-exports it from `cullinan`.

### What changed

- `Application.run(RootModule)` builds, validates, warms, and activates a root module
- `@module` defines module imports, owned packages, warmup hooks, and health checks
- component discovery rebuilds pending registrations from decorator metadata instead of
  relying on one-shot import timing
- `current_app()` prefers the request-bound application snapshot while an older runtime drains

### Migration implication

New bootstrap code should prefer `Application` + `@module`. Keep using
`ApplicationContext` for low-level container work and use the legacy
`cullinan.application.run()` entrypoint only when compatibility matters.

## 3. Web Runtime consolidation

The web stack was reorganized around a transport-agnostic runtime in `cullinan.gateway`.

### What changed

- `WebRequest`, `WebResponse`, and `WebAdapter` define the current public HTTP abstraction
- `Router`, `Dispatcher`, `MiddlewarePipeline`, and `ExceptionHandler` now live behind the gateway facade
- `cullinan.gateway.web_core` owns the shared request/response model
- adapters are separated into `cullinan.adapter` (`TornadoAdapter`, `ASGIAdapter`)

### Migration implication

Use the unified Web Runtime names in new code. The old request / response / adapter names are no longer the primary public surface.

## 4. Test-suite alignment

The repository test workflow continues to converge on pytest, and the new
application-model and adapter coverage now lives in regular collected tests.

### What changed

- a single formal entrypoint: `.venv\Scripts\python -m pytest`
- test discovery is defined by `pytest.ini`
- topic-based suite layout under `tests/`
- new and refreshed coverage uses real pytest tests under `tests/core` and `tests/integration`
- some historical script-style files still remain and are being migrated incrementally

### Current directories

- `tests/core`
- `tests/di`
- `tests/web`
- `tests/integration`
- `tests/regression`
- `tests/compat`

## Where to read next

- [Architecture](architecture.md)
- [Application Runtime Model](wiki/application_runtime.md)
- [Dependency Injection Guide](dependency_injection_guide.md)
- [Web Runtime Guide](web_runtime_guide.md)
- [Testing & Verification](testing.md)
