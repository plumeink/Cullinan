title: "cullinan.core"
slug: "modules-core"
module: ["cullinan.core"]
tags: ["api", "module", "core"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/modules/core.md"
related_tests: ["tests/test_core_injection.py","tests/test_core.py"]
related_examples: []
estimate_pd: 2.0
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# cullinan.core

> **说明（v0.90）**：核心模块已在 0.90 版本中重新组织。
> 新的 IoC/DI 2.0 API 请参阅 [依赖注入指南](../dependency_injection_guide.md)。
> 新项目应使用 `cullinan.core.container` 中的 `ApplicationContext`。
>
> **新模块结构**：
> - `cullinan.core.container` - ApplicationContext、Definition、ScopeType
> - `cullinan.core.diagnostics` - 异常与错误渲染
> - `cullinan.core.lifecycle` - 生命周期管理
> - `cullinan.core.request` - 请求上下文

摘要：核心 IoC/DI 原语，provider、scope、registry 与生命周期帮助器。本页应引用 `cullinan/core/` 下的具体文件并包含使用示例。

建议记录的公有符号：provider、registry、scope、注入相关 API

## 示例

属性注入示例（请求作用域的 provider）：

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

构造器注入示例：

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

说明：
- 在测试/设置中使用 `reset_injection_registry()` 以确保注入状态干净。
- 对于属性注入优先使用 `@injectable`，需要构造器注入时使用 `@inject_constructor`。确保在解析注入前 ProviderRegistry 中已注册相应提供者。
