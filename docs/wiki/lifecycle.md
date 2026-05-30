title: "Application Lifecycle"
slug: "wiki-lifecycle"
module: ["lifecycle"]
tags: ["wiki", "lifecycle"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/wiki/lifecycle.md"
related_tests: ["tests/integration/test_service_lifecycle_integration.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# Application Lifecycle

Cullinan's lifecycle is driven by the active `ApplicationContext`.

## Main phases

1. **Create context** — instantiate `ApplicationContext`
2. **Register components** — decorators, scanners, or explicit definitions
3. **Refresh** — call `ctx.refresh()` to build eager state and run startup hooks
4. **Serve requests** — request scope and middleware operate against the active context
5. **Shutdown** — call `ctx.shutdown()` to run teardown hooks and release managed state

## Lifecycle hooks

Managed components may implement:

- `on_post_construct()`
- `on_startup()`
- `on_shutdown()`
- `on_pre_destroy()`

Async variants are supported through `_async` suffixes.

## Ordering

If a component must start or stop before others, implement `get_phase()`. Lower phases execute earlier on startup and later on shutdown.

## Request scope

Request-scoped dependencies are resolved against the current request context. The framework creates and tears down that context around request handling.

## Middleware bridge

Application bootstrap can bridge older middleware registrations into the gateway pipeline so legacy modules continue to participate in request processing while new code uses the unified Web Runtime.

## See also

- [IoC & DI](injection.md)
- [Web Runtime Guide](../web_runtime_guide.md)
