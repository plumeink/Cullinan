title: "IoC 与 DI"
slug: "wiki-ioc-di"
module: ["ioc", "di"]
tags: ["wiki", "ioc", "di"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/wiki/injection.md"
related_tests: ["tests/di/test_core_constructor_injection.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-30T00:00:00Z"
pr_links: []

# IoC 与 DI

Cullinan 当前的依赖模型已经统一到 `ApplicationContext` 与公开的 `cullinan.core` 门面之上。

## 推荐编程模型

- 用 `@service` 和 `@controller` 注册业务类型
- 用 `Inject()` 注入依赖
- 只有在按名称解析更合适时才使用 `InjectByName()`
- 需要显式集成或自定义 Definition 时直接使用 `ApplicationContext`

## 示例

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

## 运行时模型

- 装饰器最终生成容器定义
- `ApplicationContext.refresh()` 会实例化 eager 部分依赖图
- 生命周期钩子在受管组件上统一执行
- request scope 解析依赖当前活动请求上下文

## 兼容层

旧构造器注入辅助 API 仍存在，但仅作为兼容 shim：

- `injectable` —— 空操作兼容装饰器
- `inject_constructor` —— 空操作兼容装饰器
- `get_injection_registry()` —— 返回 `None`
- `reset_injection_registry()` —— 安全空操作

新代码不应继续建立在这些 API 之上。

## 另见

- [依赖注入指南](../dependency_injection_guide.md)
- [应用生命周期](lifecycle.md)
