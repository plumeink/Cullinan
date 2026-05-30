title: "cullinan.service"
slug: "modules-service"
module: ["cullinan.service"]
tags: ["api", "module", "service"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/modules/service.md"
related_tests: ["tests/integration/test_service_lifecycle_integration.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# cullinan.service

`cullinan.service` exposes the primary service decorator plus convenience re-exports for dependency markers.

## Main exports

- `service`
- `Service`
- `Inject`
- `InjectByName`
- `Lazy`

Compatibility registry exports:

- `ServiceRegistry`
- `get_service_registry()`
- `reset_service_registry()`

## Example

```python
from cullinan.service import Service, service
from cullinan.core import Inject

@service
class UserService(Service):
    repo: UserRepository = Inject()

    def get_user(self, user_id: int):
        return self.repo.find_by_id(user_id)
```

For most code, use `@service` plus dependency markers and let the active `ApplicationContext` manage creation and lifecycle.

## See also

- [Dependency Injection Guide](../dependency_injection_guide.md)
- [Application Lifecycle](../wiki/lifecycle.md)
