title: "cullinan.service"
slug: "modules-service"
module: ["cullinan.service"]
tags: ["api", "module", "service"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/modules/service.md"
related_tests: ["tests/test_provider_system.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# cullinan.service

> **说明（v0.90）**：服务现在可以通过 `ApplicationContext` 注册。
> 新的 IoC/DI 2.0 架构请参阅 [IoC/DI 2.0 架构](../wiki/ioc_di_v2.md)。

摘要：服务注册与提供者模式。记录服务如何被提供、作用域及注入方式。

## 公共 API（自动生成）

<!-- generated: docs/work/generated_modules/cullinan_service.md -->

### cullinan.service

| 名称 | 类型 | 签名 / 值 |
| --- | --- | --- |
| `Service` | class | `Service()` |
| `ServiceRegistry` | class | `ServiceRegistry()` |
| `get_service_registry` | function | `get_service_registry() -> cullinan.service.registry.ServiceRegistry` |
| `reset_service_registry` | function | `reset_service_registry() -> None` |
| `service` | function | `service(cls: Optional[Type[cullinan.service.base.Service]] = None, *, dependencies: Optional[List[str]] = None)` |

## 说明与示例

占位：描述 Service 的注册、典型 `@service` 用法，以及如何从 registry 获取或重置 service registry；给出最小示例说明如何声明一个 Service 并从 registry 中检索它。

## 示例：注册并使用服务

```python
from cullinan.service import Service, service, get_service_registry

@service
class DatabaseService(Service):
    def __init__(self):
        self.connection = "db_connection_mock"
    
    def query(self, sql):
        return f"Result for: {sql}"

# 服务通过 @service 装饰器自动注册
registry = get_service_registry()
db_service = registry.get('DatabaseService')
result = db_service.query("SELECT * FROM users")
print(result)  # 输出: Result for: SELECT * FROM users
```

说明：
- 使用 `@service` 装饰器在模块扫描或显式初始化时自动注册服务。
- 服务通常为长期运行（默认单例作用域，除非另行配置）。
- 通过 `get_service_registry()` 访问服务，或在 controller/handler 中通过 DI 注入使用。
