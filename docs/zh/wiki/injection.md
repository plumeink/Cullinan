title: "IoC 与 DI（注入）"
slug: "injection"
module: ["cullinan.core"]
tags: ["ioc", "di", "injection"]
author: "Plumeink"
reviewers: []
status: draft
locale: zh
translation_pair: "docs/wiki/injection.md"
related_tests: ["tests/test_core_injection.py"]
related_examples: ["docs/work/core_examples.py"]
estimate_pd: 2.0
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# IoC 与 DI（注入）

本文档基于 `cullinan/core` 源码（以源码实现为准）介绍 Cullinan 的 IoC（控制反转）与 DI（依赖注入）原语。目标：展示常见用法、provider/registry/scope 概念，并提供最小可运行示例。

关键概念与组件

- Provider 与 ProviderRegistry：用于生成服务实例的提供者。提供者可以是类提供者、工厂提供者或实例提供者。`ProviderRegistry` 保存已注册的提供者，并常通过 `InjectionRegistry` 进行协调解析。
- Scope：控制提供者的生命周期。常用的作用域包括 `SingletonScope`、`TransientScope` 与 `RequestScope`。
- 注入标记与装饰器：
  - 使用 `Inject` 与 `InjectByName` 进行属性注入标记。
  - 使用 `@injectable` 标记类以启用属性注入。
  - 使用 `@inject_constructor` 启用构造器注入（参数注入）。
- InjectionRegistry：负责协调 provider registry 并解析注入点的中心注册表。
- RequestContext：与 `create_context()` 配合使用的上下文管理器，用于请求范围的对象（配合 `RequestScope`）。

源码位置建议阅读

- `cullinan/core/injection.py` — 注入注册与解析实现。
- `cullinan/core/provider.py` — 提供者实现（ClassProvider、FactoryProvider、InstanceProvider）。
- `cullinan/core/registry.py` — ProviderRegistry 与通用 Registry 模式实现。
- `cullinan/core/scope.py` — Scope 实现（SingletonScope、RequestScope、TransientScope）。
- 测试示例：`tests/test_core_injection.py`, `tests/test_core_scope_integration.py`。

最小可运行示例（可执行）

属性注入：

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

构造器注入：

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

常见模式与建议

- 当类由使用者直接实例化时，优先使用 `@injectable` + `Inject()` 做属性注入；需要更显式的注入或更严格的控制时使用 `@inject_constructor`。
- 将提供者注册进 `ProviderRegistry`，并在全局 `InjectionRegistry` 中注册 ProviderRegistry，以便注入点能够解析依赖。
- 在需要请求范围生命周期时，使用 `RequestScope` 与 `create_context()`。

故障排查

- 若注入为 None，确保在测试设置中调用 `reset_injection_registry()` 并在注册 provider 之后实例化目标类。
- 使用 `InjectByName` 时确认提供者名称与注入点名称匹配。

下一步

- 为该页添加注入解析时序图、循环依赖错误示例与生命周期 hook 的完整示例（on_init/on_shutdown）。
