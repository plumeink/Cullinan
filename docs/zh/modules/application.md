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

`cullinan.application` 现在提供推荐的 application-first 启动面：

- `Application.run(RootModule)`：构建、预热并激活根模块
- `@module`：声明根模块、功能模块和共享模块及其导入关系
- `current_app()`：返回当前活动应用；当旧 runtime 正在 draining 时，会优先返回请求绑定的应用快照
- 旧的 `run(handlers=None, engine=None)` 入口仍保留，用于兼容已有调用

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

## 模块归属

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

`ApplicationContext` 仍然是底层容器 / 运行时原语。已有依赖 `register()`、`refresh()`、`get()` 或旧 `cullinan.application.run()` 的代码仍可继续工作，但新的应用装配应优先使用 `Application` + `@module`。

## 相关文档

- [应用运行时模型](../wiki/application_runtime.md)
- [应用生命周期](../wiki/lifecycle.md)
