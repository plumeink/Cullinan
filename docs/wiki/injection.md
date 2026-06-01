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
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# IoC & DI

Cullinan's current dependency model is unified around `ApplicationContext` and the public `cullinan.core` facade.

For the hard contract behind discovery, typed binding, `refresh()`, and compatibility APIs, read [Framework Semantics](../framework_semantics.md) together with this page.

## Preferred programming model

- register business types with `@service` and `@controller`
- inject dependencies with `Inject()`
- use `InjectByName()` when runtime type imports are undesirable
- use `Lazy("Name")` when lookup should be deferred until first access
- use `ApplicationContext` directly for explicit integration or custom definitions

## Example

```python
from cullinan.web.controller import controller, get_api
from cullinan.core import Inject
from cullinan.core.services import service

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

## Runtime type resolution rule

`Inject()` is still strict, but it now understands a wider set of typed contracts:

- direct runtime types
- `TYPE_CHECKING` forward references when they map to one unique target
- `Optional[T]`, `Annotated[T, ...]`, `Final[T]`
- `Provider[T]`
- `list[T]`, `set[T]`, `tuple[T, ...]`
- `Union[A, B]` when exactly one branch is bindable

Cullinan still rejects attribute-name guesses and ambiguous combinations. If the type contract cannot be normalized safely, startup fails with `DependencyTypeResolutionError`.

Use `InjectByName("Name")` or `Lazy("Name")` when you want explicit, name-based control instead.

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
