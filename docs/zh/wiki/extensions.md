title: "扩展与插件"
slug: "extensions"
module: ["cullinan"]
tags: ["extensions", "plugins"]
author: "Plumeink"
reviewers: []
status: draft
locale: zh
translation_pair: "docs/wiki/extensions.md"
related_tests: []
related_examples: []
estimate_pd: 1.5
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# 扩展与插件

本文档说明如何通过自定义插件扩展 Cullinan。内容包括扩展点、提供者注册、典型插件模式，以及一个最小示例（展示如何注册自定义 provider 并挂接到应用生命周期）。

设计原则

- 非侵入式：优先通过注册 provider、controller 或 middleware 扩展，而不是修改框架内部。
- 可撤销：暴露的扩展点应可移除/取消注册，便于测试与运行时重新配置。
- 可发现性：插件应可通过模块扫描或显式注册 API 被发现。

扩展点

1. Provider 与 ServiceRegistry
   - 使用 `ProviderRegistry` 与提供者实现（`ClassProvider`、`FactoryProvider`、`InstanceProvider`）来提供服务。先注册 provider，然后把 provider registry 添加到全局的 `InjectionRegistry`，这样注入点才能解析依赖。
   - 关键 API：`cullinan.core.ProviderRegistry`、`cullinan.core.ScopedProvider`、`cullinan.service.registry.ServiceRegistry`。

2. 控制器
   - 使用 `controller` 装饰器或显式注册 API 注册 controller 函数/类。添加路由的插件应在应用启动阶段注册控制器。
   - 关键 API：`cullinan.controller.controller`、`cullinan.controller.get_controller_registry()`。

3. 中间件
   - 实现遵循项目中间件约定的中间件类/函数，并在应用配置或启动期间注册，以影响请求/响应处理。
   - 关键 API：`cullinan.middleware` 包（参见示例）。

4. 生命周期钩子
   - 插件可以通过 `CullinanApplication.add_shutdown_handler` 注册启动/关闭处理器，也可以实现 `LifecycleAware` 接口以集成生命周期管理。
   - 关键 API：`CullinanApplication.add_shutdown_handler`、`cullinan.core.lifecycle` 工具函数。

发现与注册模式

- 显式注册（推荐）：插件提供 `register(app_or_registry)` 函数，应用在启动时调用该函数进行注册。示例：

```python
# my_plugin.py
from cullinan.service import Service, service
from cullinan.core import ProviderRegistry, ScopedProvider, SingletonScope

class MyService(Service):
    def __init__(self):
        self.value = 'my plugin service'

def register_service(provider_registry: ProviderRegistry):
    provider_registry.register_provider(
        'MyService',
        ScopedProvider(lambda: MyService(), SingletonScope(), 'MyService')
    )

# 应用启动：
# provider_registry = ProviderRegistry()
# register_service(provider_registry)
# injection_registry.add_provider_registry(provider_registry)
```

- 自动发现（便捷）：启用模块扫描时可以在预定义命名空间下发现插件包（例如 `myproject.plugins.*`）。生产环境建议使用显式注册。

打包与分发

- 将插件打包为标准 Python 包，暴露 `register()` 入口或约定模块路径以供发现。
- 可选：在 `setup.cfg` / `setup.py` 中使用 `entry_points`（例如 `cullinan.plugins`）并通过 `pkg_resources` 或 `importlib.metadata` 发现已安装插件。

最小插件示例 — 日志中间件

```python
# my_logging_plugin.py
import logging
from cullinan.middleware import MiddlewareBase

logger = logging.getLogger('my_plugin')

class RequestLogger(MiddlewareBase):
    def process_request(self, request):
        logger.info('Incoming %s %s', request.method, request.path)

def register(app):
    # app-specific registration, pseudocode
    app.add_middleware(RequestLogger())
```

插件测试

- 在隔离环境中单元测试插件，模拟 provider registry 与应用生命周期。
- 确保 `register()` 是幂等的，或在函数内加入防重复注册的保护逻辑。

安全与兼容性注意

- 插件在应用进程中运行；避免执行不受信任的代码或允许插件运行任意启动脚本。
- 在插件包中记录对 Cullinan 版本的兼容性与升级说明。

下一步

- 提供插件脚手架（cookiecutter）以简化插件开发。
- 在 `examples/` 目录添加插件示例包，并在 CI 中运行这些示例以做验证。
