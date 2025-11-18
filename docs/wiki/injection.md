title: "IoC & DI (Injection)"
slug: "injection"
module: ["cullinan.core"]
tags: ["ioc", "di", "injection"]
author: "Plumeink"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/wiki/injection.md"
related_tests: ["tests/test_core_injection.py"]
related_examples: ["docs/work/core_examples.py"]
estimate_pd: 2.0
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# IoC & DI (Injection)

This page documents the IoC (Inversion of Control) and DI (Dependency Injection) primitives used by Cullinan, based on the source code in `cullinan/core`. The goal is to present concrete usage patterns, explain provider/registry/scope concepts, and show minimal runnable examples.

Key concepts and components

- Provider & ProviderRegistry: producers of service instances. Providers can be class-based, factory-based, or instance-based. The `ProviderRegistry` holds registered providers and is often bridged into the `InjectionRegistry` for application-wide resolution.
- Scopes: control provider lifetimes. Common scopes include `SingletonScope`, `TransientScope`, and `RequestScope`.
- Injection markers & decorators:
  - `Inject` and `InjectByName` are used as markers for property injection.
  - `@injectable` marks a class to receive property injection when instantiated.
  - `@inject_constructor` enables constructor (parameter) injection.
- InjectionRegistry: central registry that coordinates provider registries and resolves dependencies for injection points.
- RequestContext: a context manager used with `create_context()` to scope request-local objects (used with `RequestScope`).

Where to look in the source

- `cullinan/core/injection.py` — injection registration and resolution mechanics.
- `cullinan/core/provider.py` — provider implementations (ClassProvider, FactoryProvider, InstanceProvider).
- `cullinan/core/registry.py` — registry patterns used by ProviderRegistry and general Registry classes.
- `cullinan/core/scope.py` — scope implementations (SingletonScope, RequestScope, TransientScope).
- tests: `tests/test_core_injection.py`, `tests/test_core_scope_integration.py` — real usage examples and assertions.

Minimal usage examples (runnable)

Property injection (example):

```python
from cullinan.core import (
    SingletonScope, ScopedProvider, ProviderRegistry,
    injectable, Inject, get_injection_registry, reset_injection_registry
)

class Database:
    _instance_count = 0
    def __init__(self):
        Database._instance_count += 1
        self.id = Database._instance_count

reset_injection_registry()
registry = ProviderRegistry()
scope = SingletonScope()
registry.register_provider('Database', ScopedProvider(lambda: Database(), scope, 'Database'))
get_injection_registry().add_provider_registry(registry)

@injectable
class Service:
    database: Database = Inject()

s1 = Service()
s2 = Service()
assert s1.database is s2.database
```

Constructor injection (example):

```python
from cullinan.core import (
    SingletonScope, ScopedProvider, ProviderRegistry,
    inject_constructor, get_injection_registry, reset_injection_registry
)

class Database:
    _instance_count = 0
    def __init__(self):
        Database._instance_count += 1
        self.id = Database._instance_count

reset_injection_registry()
registry = ProviderRegistry()
scope = SingletonScope()
registry.register_provider('Database', ScopedProvider(lambda: Database(), scope, 'Database'))
get_injection_registry().add_provider_registry(registry)

@inject_constructor
class Controller:
    def __init__(self, database: Database):
        self.database = database

c1 = Controller()
c2 = Controller()
assert c1.database is c2.database
```

Common patterns and tips

- Prefer `@injectable` + `Inject()` for property injection when classes are instantiated by user code; use `@inject_constructor` where constructor injection is more explicit or required.
- Register providers into a `ProviderRegistry` and add that registry to the global `InjectionRegistry` so injection points can resolve dependencies.
- Use `RequestScope` with `create_context()` when you need request-scoped lifetimes (HTTP handlers).

Troubleshooting

- If injections are None, ensure `reset_injection_registry()` is called before registering providers during test setup.
- Verify provider keys (names) match the expected injection points (by type name or by explicit name when using `InjectByName`).

Next steps

- Expand this page with diagrams showing provider -> registry -> injection resolution flow and common error modes (circular dependency, missing provider).
- Add more complex examples (provider ordering, lifecycle hooks `on_init`, `on_shutdown`).
