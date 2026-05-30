title: "cullinan.service"
slug: "modules-service"
module: ["cullinan.service"]
tags: ["api", "module", "service"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/modules/service.md"
related_tests: ["tests/integration/test_service_lifecycle_integration.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# cullinan.service

`cullinan.service` 暴露主服务装饰器，并便捷重导出常用依赖标记。

## 主要导出

- `service`
- `Service`
- `Inject`
- `InjectByName`
- `Lazy`

兼容 registry 导出：

- `ServiceRegistry`
- `get_service_registry()`
- `reset_service_registry()`

## 示例

```python
from cullinan.service import Service, service
from cullinan.core import Inject

@service
class UserService(Service):
    repo: UserRepository = Inject()

    def get_user(self, user_id: int):
        return self.repo.find_by_id(user_id)
```

对大多数代码来说，直接使用 `@service` 与依赖标记，并让当前 `ApplicationContext` 负责实例创建与生命周期即可。

## 另见

- [依赖注入指南](../dependency_injection_guide.md)
- [应用生命周期](../wiki/lifecycle.md)
