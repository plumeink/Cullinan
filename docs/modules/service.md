title: "cullinan.service"
slug: "modules-service"
module: ["cullinan.service"]
tags: ["api", "module", "service"]
author: "Plumeink"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/modules/service.md"
related_tests: ["tests/test_provider_system.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# cullinan.service

Summary: Service registration and provider patterns. Document how services are provided, scoped, and injected.

## Public API (auto-generated)

<!-- generated: docs/work/generated_modules/cullinan_service.md -->

### cullinan.service

| Name | Kind | Signature / Value |
| --- | --- | --- |
| `Service` | class | `Service()` |
| `ServiceRegistry` | class | `ServiceRegistry()` |
| `get_service_registry` | function | `get_service_registry() -> cullinan.service.registry.ServiceRegistry` |
| `reset_service_registry` | function | `reset_service_registry() -> None` |
| `service` | function | `service(cls: Optional[Type[cullinan.service.base.Service]] = None, *, dependencies: Optional[List[str]] = None)` |

## Example: register and use a service

```python
from cullinan.service import Service, service, get_service_registry

@service
class DatabaseService(Service):
    def __init__(self):
        self.connection = "db_connection_mock"
    
    def query(self, sql):
        return f"Result for: {sql}"

# Service is auto-registered via @service decorator
registry = get_service_registry()
db_service = registry.get('DatabaseService')
result = db_service.query("SELECT * FROM users")
print(result)  # Output: Result for: SELECT * FROM users
```

Notes:
- Use the `@service` decorator to register services automatically during module scanning or explicit initialization.
- Services are typically long-lived (singleton-scoped by default unless configured otherwise).
- Access services via `get_service_registry()` or through DI injection in controllers/handlers.
