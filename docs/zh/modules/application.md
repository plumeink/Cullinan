title: "cullinan.application 模块"
slug: "modules-application"
module: ["cullinan.application"]
tags: ["api", "module", "application"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/modules/application.md"
related_tests: ["tests/core/test_application_model_refactor.py", "tests/core/test_decorators.py", "tests/di/test_global_container_manager.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-05-31T00:00:00Z"
pr_links: []

# cullinan.application

`cullinan.application` 现在提供推荐的运行时装配入口：

- `Application.run(RootModule)`：构建、预热并激活一套已装配运行时
- `@module`：当你需要模块归属、reload 与热插拔运行时能力时，用来声明结构边界
- `current_app()`：返回当前活动应用；当旧 runtime 正在 draining 时，会优先返回请求绑定的应用快照
- 旧的 `run(handlers=None, engine=None)` 入口仍保留，用于兼容已有调用

这里的启动契约同时依赖[框架语义规则](../framework_semantics.md)：组件发现基于导入执行、自动扫描只保证模块顶层装饰器组件、`refresh()` 之后结构性注册会被冻结。

在实际开发里，开发者主要写的是业务装饰器和业务方法。`@module`
不是手工注册 app 的中心，而是把归属、reload、draining 与运行时切换明确化并稳定化的结构边界。

## 推荐启动方式

```python
from cullinan import Application, controller, current_app, get_api, module, service
from cullinan.core import Inject


@service
class GreetingService:
    def greet(self) -> str:
        return "hello"


@controller(url="/api")
class GreetingController:
    greeting_service: GreetingService = Inject()

    @get_api(url="/whoami")
    def whoami(self):
        return {
            "root": current_app().root_module.__name__,
            "message": self.greeting_service.greet(),
        }


@module
class RootModule:
    pass


app = Application.run(RootModule)
```

## 模块归属与边界

`@module` 基于 Python 包归属发现组件。若某个组件同时匹配多个模块包，启动会立即失败；对有意共享的重叠区域，请用 `ownership_overrides` 显式指定归属。

```python
@module(
    imports=[SharedModule, OrdersModule],
    ownership_overrides={"myapp.shared": SharedModule},
)
class RootModule:
    pass
```

## Runtime 切换

`Application.reload()` 会先构建新的候选 runtime，完成校验与预热，再原子切换当前活动应用。旧 runtime 会进入 draining 状态，而 `current_app()` 在请求结束前仍会返回该请求绑定的旧应用快照。

## 兼容性说明

`ApplicationContext` 仍然是底层容器 / 运行时原语。已有依赖 `register()`、`refresh()`、`get()` 或旧 `cullinan.application.run()` 的代码仍可继续工作，但新的应用代码应先从业务装饰器出发，并在需要明确运行时边界时使用 `Application` + `@module`。

## 相关文档

- [应用运行时模型](../wiki/application_runtime.md)
- [应用生命周期](../wiki/lifecycle.md)
