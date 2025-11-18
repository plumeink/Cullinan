title: "cullinan.core"
slug: "modules-core"
module: ["cullinan.core"]
tags: ["api", "module", "core"]
author: "Plumeink"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/modules/core.md"
related_tests: ["tests/test_core_injection.py","tests/test_core.py"]
related_examples: []
estimate_pd: 2.0
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# cullinan.core

Summary: Core IoC/DI primitives, provider, scope, registry, and lifecycle helpers. This page should reference concrete files in `cullinan/core/` and include usage examples.

Public symbols to document: provider, registry, scope, injection APIs

## Public API (auto-generated)

<!-- generated: docs/work/generated_modules/cullinan_core.md -->

### cullinan.core

| Name | Kind | Signature / Value |
| --- | --- | --- |
| `Inject` | class | `Inject(name: Optional[str] = None, required: bool = True)` |
| `InjectByName` | class | `InjectByName(service_name: Optional[str] = None, required: bool = True)` |
| `InjectionRegistry` | class | `InjectionRegistry()` |
| `ProviderRegistry` | class | `ProviderRegistry()` |
| `RequestScope` | class | `RequestScope(storage_key: str = '_scoped_instances')` |
| `SingletonScope` | class | `SingletonScope()` |
| `TransientScope` | class | `TransientScope()` |
| `create_context` | function | `create_context() -> cullinan.core.context.RequestContext` |
| `destroy_context` | function | `destroy_context() -> None` |
| `get_context_value` | function | `get_context_value(key: str, default: Any = None) -> Any` |
| `get_current_context` | function | `get_current_context() -> Optional[cullinan.core.context.RequestContext]` |
| `get_injection_registry` | function | `get_injection_registry() -> cullinan.core.injection.InjectionRegistry` |
| `get_request_scope` | function | `get_request_scope() -> cullinan.core.scope.RequestScope` |
| `get_singleton_scope` | function | `get_singleton_scope() -> cullinan.core.scope.SingletonScope` |
| `get_transient_scope` | function | `get_transient_scope() -> cullinan.core.scope.TransientScope` |
| `inject_constructor` | function | `inject_constructor(cls: Optional[Type] = None)` |
| `injectable` | function | `injectable(cls: Optional[Type] = None)` |
| `reset_injection_registry` | function | `reset_injection_registry() -> None` |
| `set_context_value` | function | `set_context_value(key: str, value: Any) -> None` |
| `set_current_context` | function | `set_current_context(context: Optional[cullinan.core.context.RequestContext]) -> None` |

## Examples

Property injection example (request-scoped provider):

```python
from cullinan.core import (
    ProviderRegistry, ScopedProvider, get_request_scope,
    injectable, Inject, get_injection_registry, reset_injection_registry
)

class Database:
    def __init__(self):
        self.id = object()

reset_injection_registry()
registry = ProviderRegistry()
request_scope = get_request_scope()
registry.register_provider('Database', ScopedProvider(lambda: Database(), request_scope, 'Database'))
get_injection_registry().add_provider_registry(registry)

@injectable
class Service:
    db: Database = Inject()

s = Service()
assert s.db is not None
```

Constructor injection example:

```python
from cullinan.core import inject_constructor, reset_injection_registry, ProviderRegistry, ScopedProvider, get_request_scope, get_injection_registry

class Config:
    pass

reset_injection_registry()
pr = ProviderRegistry()
pr.register_provider('Config', ScopedProvider(lambda: Config(), get_request_scope(), 'Config'))
get_injection_registry().add_provider_registry(pr)

@inject_constructor
class Controller:
    def __init__(self, config: Config):
        self.config = config

c = Controller()
assert c.config is not None
```

Notes:
- Use `reset_injection_registry()` in tests/setup to ensure a clean injection state.
- Prefer `@injectable` for property injection and `@inject_constructor` for constructor-based patterns. Ensure ProviderRegistry entries are available before resolving injections.
