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
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# IoC 与 DI

Cullinan 当前的依赖模型已经统一到 `ApplicationContext` 与公开的 `cullinan.core` 门面之上。

若要理解发现、类型绑定、`refresh()` 与兼容 API 背后的硬约束，请把本文与[框架语义规则](../framework_semantics.md)一起阅读。

## 推荐编程模型

- 用 `@service` 和 `@controller` 注册业务类型
- 用 `Inject()` 注入依赖
- 当运行时 import 类型不合适时，使用 `InjectByName()`
- 当希望第一次访问时再解析时，使用 `Lazy("Name")`
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

## 运行时类型解析规则

当前版本里的 `Inject()` 依然是严格模式，但已经支持更完整的类型契约：

- 直接运行时类型
- `TYPE_CHECKING` 前向引用（前提是最终能唯一命中一个目标）
- `Optional[T]`、`Annotated[T, ...]`、`Final[T]`
- `Provider[T]`
- `list[T]`、`set[T]`、`tuple[T, ...]`
- `Union[A, B]`（前提是恰好只有一个分支可绑定）

Cullinan 仍然拒绝属性名猜测和存在歧义的组合。只要类型契约无法被安全归一化，启动就会抛出 `DependencyTypeResolutionError`。

如果你本来就希望显式按名称控制依赖，请使用 `InjectByName("Name")` 或 `Lazy("Name")`。

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
