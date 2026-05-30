title: "IoC & DI"
slug: "wiki-ioc-di"
module: ["ioc", "di"]
tags: ["wiki", "ioc", "di"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/wiki/injection.md"
related_tests: ["tests/di/test_core_constructor_injection.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# IoC & DI

Cullinan's current dependency model is unified around `ApplicationContext` and the public `cullinan.core` facade.

## Preferred programming model

- register business types with `@service` and `@controller`
- inject dependencies with `Inject()`
- use `InjectByName()` only when name-based lookup is the better fit
- use `ApplicationContext` directly for explicit integration or custom definitions

## Example

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject
from cullinan.service import service

@service
class UserService:
    def get_user(self, user_id: int):
        return {"id": user_id}

@controller(url="/users")
class UserController:
    user_service: UserService = Inject()

    @get_api(url="/{user_id}")
    async def get_user(self, user_id: int):
        return self.user_service.get_user(user_id)
```

## Runtime model

- decorators produce container definitions
- `ApplicationContext.refresh()` materializes eager parts of the graph
- lifecycle hooks run on managed components
- request-scoped resolution is tied to the active request context

## Compatibility layer

Older constructor-injection helpers still exist, but only as compatibility shims:

- `injectable` — no-op compatibility decorator
- `inject_constructor` — no-op compatibility decorator
- `get_injection_registry()` — returns `None`
- `reset_injection_registry()` — safe no-op

New code should not build on those APIs.

## See also

- [Dependency Injection Guide](../dependency_injection_guide.md)
- [Application Lifecycle](lifecycle.md)
