# Cullinan 依赖注入指南

> **版本**：0.93a3  
> **最后更新**：2026-05-31  
> **状态**：已更新

## 概述

Cullinan 当前的 DI 模型以 `ApplicationContext` 为中心，并通过 `cullinan.core` 作为公开入口。装饰器仍然是推荐的编写方式；旧式 registry API 仅保留兼容意义。

## 推荐用法

### 1. 用装饰器注册服务

```python
from cullinan.core import Inject
from cullinan.service import service

@service
class DatabaseService:
    def query(self, sql: str):
        return {"sql": sql}

@service
class UserService:
    database: DatabaseService = Inject()

    def get_user(self, user_id: int):
        return self.database.query(f"select * from users where id = {user_id}")
```

### 2. 在控制器中复用同一套注入模型

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject
from cullinan.params import Path

@controller(url="/users")
class UserController:
    user_service: UserService = Inject()

    @get_api(url="/{user_id}")
    async def get_user(self, user_id: int = Path()):
        return self.user_service.get_user(user_id)
```

## 注入原语

### `Inject()` —— 首选

需要按类型解析、并获得更好的重构支持时，优先使用 `Inject()`。

```python
class AuditService:
    repo: Repository = Inject()
    cache: CacheService = Inject(required=False)
```

### `InjectByName()` —— 按名称解析

当依赖更适合按名称解析，或直接导入类型会引入不理想的依赖边时，使用 `InjectByName()`。

```python
from cullinan.core import InjectByName

class ReportController:
    report_service = InjectByName("ReportService")
```

## ApplicationContext 是唯一容器入口

装饰器注册已覆盖大多数业务代码。高级集成场景可直接使用 `ApplicationContext`。

```python
from cullinan.core import ApplicationContext, Definition, ScopeType

ctx = ApplicationContext()
ctx.register(Definition(
    name="CustomService",
    factory=lambda c: CustomService(),
    scope=ScopeType.SINGLETON,
    source="custom:CustomService",
))
ctx.refresh()
service = ctx.get("CustomService")
```

`cullinan.core.container.*` 路径现在只是同一公开容器 API 的兼容转发。

## 生命周期集成

DI 与生命周期属于同一运行时模型。受管组件可实现：

- `on_post_construct()`
- `on_startup()`
- `on_shutdown()`
- `on_pre_destroy()`

同样支持 `_async` 异步版本；如需控制顺序，可实现 `get_phase()`。

## 兼容性说明

Cullinan 仍导出部分旧名称，但不应再作为主要编程模型：

- `injectable` 当前是**空操作兼容装饰器**
- `inject_constructor` 当前是**空操作兼容装饰器**
- `get_injection_registry()` 当前返回 `None`
- `reset_injection_registry()` 是安全的兼容空操作

保留这些名称是为了降低旧代码的硬中断风险；新代码应依赖 `@service`、`@controller`、`Inject`、`InjectByName` 与 `ApplicationContext`。

## 故障排查

| 问题 | 检查点 |
| --- | --- |
| 依赖无法解析 | 确认类型或依赖名称与注册组件一致 |
| 可选依赖缺失 | 使用 `required=False` 并显式处理 `None` |
| 生命周期钩子未执行 | 确认组件受框架管理且已执行 `ApplicationContext.refresh()` |
| 高级注册行为不符合预期 | 检查 `Definition` 的 scope 与 factory/source 设置 |

## 相关文档

- [架构设计](architecture.md)
- [运行时整合概览](runtime_updates_v093.md)
- [IoC 与 DI wiki](wiki/injection.md)
- [应用生命周期](wiki/lifecycle.md)
