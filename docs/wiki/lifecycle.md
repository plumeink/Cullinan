title: "Application Lifecycle"
slug: "lifecycle"
module: ["cullinan.application"]
tags: ["lifecycle", "startup"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/wiki/lifecycle.md"
related_tests: ["tests/test_real_app_startup.py","tests/test_comprehensive_lifecycle.py"]
related_examples: ["docs/work/core_examples.py","examples/hello_http.py"]
estimate_pd: 1.5
last_updated: "2026-02-19T00:00:00Z"
pr_links: []

# Application Lifecycle

> **Note (v0.92)**: This document describes the unified lifecycle management system.
> All components (`@service`, `@component`, `@controller`) now use the same lifecycle hooks.
> The `ApplicationContext` provides unified lifecycle management via `refresh()` and `shutdown()`.

This document describes the Cullinan application lifecycle: startup, service initialization, request handling, and graceful shutdown hooks and events. The content is derived from the implementation (source-first) and references `cullinan/app.py`, `cullinan/application.py` and `cullinan/core/lifecycle` related files.

## Unified Lifecycle Hooks (v0.92+)

All components now use unified lifecycle methods (Duck Typing - no base class inheritance required):

| Hook Method | When Called |
|-------------|-------------|
| `on_post_construct()` | After dependency injection |
| `on_startup()` | During application startup |
| `on_shutdown()` | During application shutdown |
| `on_pre_destroy()` | Before destruction |

All hooks support async versions (append `_async` suffix).

### Phase Ordering Control

Control component startup/shutdown order via `get_phase()` method:
- Negative values = starts earlier, stops later
- Positive values = starts later, stops earlier

## Main Phases

1. Startup
   - Entry point: `CullinanApplication.run()` or using `create_app()` then calling `app.run()`.
   - Behavior (see `cullinan/app.py`):
     - Calls `startup()` to perform the startup sequence: configure injection (InjectionRegistry), discover services (ServiceRegistry).
     - `ApplicationContext.refresh()` initializes all components and calls lifecycle hooks (`on_post_construct`, `on_startup`).
     - Registers signal handlers (SIGINT / SIGTERM) to trigger graceful shutdown on signals.
     - Starts Tornado's IOLoop: `IOLoop.start()` (blocking until stop event).

2. Service initialization
   - Services register via `@service` or during module scanning into `ServiceRegistry`.
   - `ApplicationContext.refresh()` instantiates components in dependency order and invokes lifecycle hooks.
   - If no services registered, initialization step is skipped.

3. Request handling & request scope
   - On request arrival, a request context is created (via `create_context()`) to support `RequestScope`.
   - Within the same request context, the RequestScope ensures instances are reused for the lifetime of the request.
   - Handlers (Handler / controller) can obtain request-scoped dependencies via property or constructor injection.

4. Shutdown
   - When the app receives termination signals or a manual shutdown, `shutdown()` is invoked:
     - `ApplicationContext.shutdown()` calls lifecycle hooks (`on_shutdown`, `on_pre_destroy`) on all components.
     - Executes registered shutdown handlers in order (sync or async); errors are controlled by the `force` flag.
     - Sets `_running` to False and stops the IOLoop.

## Common Hooks & Extension Points

- `CullinanApplication.add_shutdown_handler(handler)` — register custom shutdown handlers (async or sync).
- `LifecycleAware` and `SmartLifecycle` (in `cullinan/core`) — components implementing lifecycle interfaces will be called at appropriate times.
- Component lifecycle hooks (`on_post_construct`, `on_startup`, `on_shutdown`, `on_pre_destroy`) — invoked during init and shutdown phases.

Minimal example: registering shutdown handlers

```python
# Quick (recommended): simple entrypoint using the framework module
from cullinan import application

if __name__ == '__main__':
    application.run()

# Advanced (optional): programmatic usage when you need to add shutdown handlers or fine-grained control
from cullinan.app import create_app
import asyncio

application_instance = create_app()

def cleanup_sync():
    print('Running sync cleanup')

async def cleanup_async():
    await asyncio.sleep(0.01)
    print('Running async cleanup')

application_instance.add_shutdown_handler(cleanup_sync)
application_instance.add_shutdown_handler(cleanup_async)

# In process entrypoint call:
# application_instance.run()
```

Request scope example (pseudocode)

```python
from cullinan.core import create_context, RequestScope, ScopedProvider, ProviderRegistry

provider_registry = ProviderRegistry()
provider_registry.register_provider('RequestHandler', ScopedProvider(lambda: RequestHandler(), RequestScope(), 'RequestHandler'))

with create_context():
    handler1 = provider_registry.get_instance('RequestHandler')
    handler2 = provider_registry.get_instance('RequestHandler')
    assert handler1 is handler2

# leaving the context isolates RequestScope instances; next request gets new instances
```

Troubleshooting

- Startup failures: inspect `startup()` error logs (`Application startup failed`) and check service registration/provider initialization stacks.
- Injection/dependency missing: ensure provider is registered in the `ProviderRegistry` and the registry is added to the `InjectionRegistry`.
- Graceful shutdown issues: if a shutdown handler blocks or raises, consider catching errors or using `force=True` during shutdown.

References & next steps

- Source: `cullinan/app.py`, `cullinan/application.py`, `cullinan/core/*` (provider/registry/scope/lifecycle).
- Suggestion: add sequence diagrams illustrating startup and shutdown flows to `docs/wiki/lifecycle.md` for review.

## Lifecycle Sequence (diagram)

```
CullinanApplication    ApplicationContext    ServiceRegistry    Tornado IOLoop    RequestContext    Handler
-------------------    ------------------    ---------------    ---------------    --------------    -------
startup() -> ApplicationContext.refresh() -> discover & init services -> start IOLoop
             (on_post_construct, on_startup)                    |
                                                        |-> IOLoop receives request -> create RequestContext
                                                        |                             -> resolve request-scoped providers
                                                        |                             -> dispatch to Handler (injection resolves)
                                                        |                             -> Handler returns response
                                                        |                             -> RequestContext cleanup
shutdown() -> ApplicationContext.shutdown() -> stop IOLoop
              (on_shutdown, on_pre_destroy)
```

<!--
```mermaid
sequenceDiagram
    autonumber
    participant App as CullinanApplication
    participant Ctx as ApplicationContext
    participant SR as ServiceRegistry
    participant IO as Tornado IOLoop
    participant Req as RequestContext
    participant Hand as Handler

    Note over App: Startup
    App->>Ctx: refresh()
    Ctx->>SR: discover & register services
    Ctx->>Ctx: resolve deps & instantiate
    Ctx->>Ctx: call on_post_construct()
    Ctx->>Ctx: call on_startup()
    App->>IO: start IOLoop

    Note over IO,Req: Request handling
    IO->>Req: create request context
    Req->>Ctx: resolve request-scoped providers
    IO->>Hand: dispatch to handler (injection resolves)
    Hand-->>IO: return response
    Req-->>IO: cleanup request context

    Note over App: Shutdown
    App->>SR: call on_shutdown on services
    App->>IO: stop IOLoop
```

```mermaid
stateDiagram-v2
  [*] --> Initialized
  Initialized --> Running: startup()
  Running --> HandlingRequest: request arrives
  HandlingRequest --> Running: request handled
  Running --> ShuttingDown: shutdown()
  ShuttingDown --> [*]
```
-->
