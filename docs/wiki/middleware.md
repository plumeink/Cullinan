title: "Middleware"
slug: "middleware"
module: ["cullinan.middleware"]
tags: ["middleware"]
author: "TBD"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/wiki/middleware.md"
related_tests: []
related_examples: ["examples/controller_di_middleware.py"]
estimate_pd: 1.5
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# Middleware

This document explains Cullinan middleware: responsibilities, execution pipeline, registration, DI integration, examples, troubleshooting and best practices. Middleware is a pluggable stage in the request/response lifecycle for auth, logging, transformations, etc.

Core concepts

- Middleware pipeline: requests pass through ordered middleware before reaching controllers; middleware may handle, mutate, or short-circuit a request. Responses may also be processed by middleware on the return path.
- Order & priority: middleware are executed in registration order. Some frameworks offer priority hooks; in Cullinan the registration order determines execution order.
- Middleware contract: middleware should implement a contract (e.g., `process_request` / `process_response`) or inherit from a project base (see `cullinan/middleware`).

Registration & configuration

- Programmatic registration (recommended): register middleware during application startup.

```python
# register middleware (pseudocode)
from cullinan import application
from my_middleware import MyMiddleware

# Quick start: run framework entrypoint (recommended)
if __name__ == '__main__':
    application.run()

# Advanced (optional): programmatic registration
from cullinan.app import create_app
from my_middleware import MyMiddleware

application_instance = create_app()
application_instance.add_middleware(MyMiddleware())
# application_instance.run()
```

- DI integration: middleware may depend on services provided through the provider/registry system. Register services via provider registries and use injection in middleware classes.

Middleware example (with DI)

```python
# examples/controller_di_middleware.py (reference)
from cullinan.core import injectable, Inject, get_injection_registry
from cullinan.middleware import MiddlewareBase

@injectable
class AuditService:
    def record(self, request):
        print('Audit:', request.path)

class AuditMiddleware(MiddlewareBase):
    audit: AuditService = Inject()

    def process_request(self, request):
        self.audit.record(request)

# Register provider and middleware during application startup
```

Execution model & constraints

- Avoid long-blocking operations in middleware; use background tasks or async patterns where appropriate.
- Middleware must handle exceptions to avoid breaking the request chain.
- Ensure middleware lifecycle aligns with request context when using RequestScope or DI; do not store request-scoped objects at module scope.

Troubleshooting

- Middleware not invoked: confirm registration at startup and correct registration order; ensure no conditional config is skipping the middleware.
- Injection issues: if Inject in middleware is unresolved, confirm providers were registered to the InjectionRegistry before middleware instantiation; use `reset_injection_registry()` in tests to ensure a clean state.
- Performance: benchmark middleware to avoid expensive operations on critical paths.

Best practices

- Keep middleware thin; delegate heavy logic to injected services.
- Use the framework logger instead of prints for production readiness.
- Unit test middleware in isolation, mocking request objects and injection registry.

Next steps

- Extract a minimal runnable example from `examples/controller_di_middleware.py` into `examples/` and ensure it is covered by at least one automated test.
- Formalize a middleware base contract (if not present) and document the required methods and expected behaviors.

## Running the demo

Ensure you have a working Python environment (virtualenv, conda, or system Python).

On Windows (PowerShell):

```powershell
python -m pip install -U pip
pip install cullinan tornado
python examples\middleware_demo.py
```

On Linux / macOS:

```bash
python -m pip install -U pip
pip install cullinan tornado
python examples/middleware_demo.py
```

Typical output (example run):

```
INFO:__main__:Starting IOLoop for middleware demo
INFO:__main__:Performing request 1
INFO:__main__:Entered request context
INFO:__main__:Injected dependencies into handler
INFO:tornado.access:200 GET /middleware (127.0.0.1) 2.10ms
INFO:__main__:Exited request context
INFO:__main__:Response1: Hello from UserService (084297)  request_count=1
INFO:__main__:Performing request 2
INFO:__main__:Entered request context
INFO:__main__:Injected dependencies into handler
INFO:tornado.access:200 GET /middleware (127.0.0.1) 0.60ms
INFO:__main__:Exited request context
INFO:__main__:Response2: Hello from UserService (084297)  request_count=1
INFO:__main__:IOLoop stopped, exiting
```

Note: `RequestCounter` is request-scoped and resets per request, while `UserService` is a singleton and retains its instance id across requests.
