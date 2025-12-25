title: "中间件"
slug: "middleware"
module: ["cullinan.middleware"]
tags: ["middleware"]
author: "Plumeink"
reviewers: []
status: updated
locale: zh
translation_pair: "docs/wiki/middleware.md"
related_tests: []
related_examples: ["examples/middleware_demo.py"]
estimate_pd: 1.5
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# 中间件

> **说明（v0.90）**：中间件的 DI 集成已在 0.90 版本中更新。
> 新的 IoC/DI 系统请参阅 [IoC/DI 2.0 架构](ioc_di_v2.md)。
> 中间件现在可以通过 `ApplicationContext` 获取依赖，而不是 `InjectionRegistry`。

本文档说明 Cullinan 中间件的作用、链路执行顺序、注册方式、与 DI 的集成，并提供最小示例与故障排查建议。中间件是处理请求／响应生命周期中的可插拔阶段，用于认证、授权、日志、请求/响应变换等场景。

核心概念

- 中间件链（pipeline）: 请求在进入控制器之前会经过一系列中间件，每个中间件可选择处理、修改或短路请求；响应也可以在返回路径上被中间件处理。
- 顺序与优先级: 中间件按注册顺序执行；某些框架允许为中间件指定优先级或阶段（pre/post）。在 Cullinan 中，注册顺序决定执行顺序，文档中示例遵循此惯例。
- 中间件契约: 中间件应实现一个约定的接口（类似 process_request / process_response），或遵循项目中间件基类（如有）。参考 `cullinan/middleware` 包实现。

注册与配置

- 程序化注册（推荐）: 在应用启动阶段显式注册中间件。
  - 示例（伪代码）:

```python
# 注册中间件（伪代码）
from cullinan import application
from my_middleware import MyMiddleware

# 快速启动并运行（推荐）
# 在入口脚本中导入模块以触发装饰器/自动注册，然后调用 application.run()
if __name__ == '__main__':
    application.run()

# 高级（可选）：以编程方式注册中间件并运行（需要 create_app）
from cullinan.app import create_app
from my_middleware import MyMiddleware

application_instance = create_app()
application_instance.add_middleware(MyMiddleware())
# application_instance.run()
```

- 依赖注入集成: 中间件可以依赖于框架的 provider/registry 系统。建议通过提供者注册需要的 service，并在中间件内部通过注入使用它们。

中间件示例（结合 DI）

下面示例演示一个中间件获取一个注入的服务并在每次请求前记录信息：

```python
# examples/controller_di_middleware.py (参考示例)
from cullinan.core import injectable, Inject, get_injection_registry
from cullinan.middleware import MiddlewareBase

@injectable
class AuditService:
    def record(self, request):
        print('Audit:', request.path)

class AuditMiddleware(MiddlewareBase):
    audit: AuditService = Inject()

    def process_request(self, request):
        # 使用注入的 audit 服务记录请求
        self.audit.record(request)

# 在应用启动时注册中间件与 provider
# registry = ProviderRegistry()...
```

中间件的执行模型与限制

- 中间件应尽量避免阻塞长时间操作；若需要耗时任务，使用后台任务队列或异步处理。
- 中间件应对异常进行防护，避免未捕获异常导致整个请求链中断。
- 在使用 RequestScope 或依赖注入时，确保中间件的生命周期与请求上下文兼容（例如不要在模块全局缓存 request-scoped 对象）。

故障排查

- 中间件不生效：确认中间件已在应用启动时注册，并且注册顺序正确；检查中间件是否被有条件的配置跳过。
- 注入失败：如果中间件中的 Inject 未解析，确保 provider 已在注入 registry 注册并在中间件实例化前可用；对测试请使用 `reset_injection_registry()` 在前置步骤中初始化。
- 性能问题：对中间件进行基准测试，避免在高频路径中调用大量 I/O 或阻塞代码。

最佳实践与建议

- 将中间件保持为轻量函数/类，核心逻辑委托给注入的服务。
- 在中间件中使用框架提供的日志记录器（logger）而不是直接打印，便于在生产环境中调整日志级别和收集方式。
- 为中间件编写独立单元测试并在 CI 中运行（可以模拟请求对象与注入 registry）。

下一步

- 从 `examples/controller_di_middleware.py` 提取一个最小可运行的示例并放入 `examples/` 目录，并确保至少由一个自动化测试覆盖。
- 将中间件契约文档化为代码接口（若项目中尚未有基础类），并在文档中引用实现示例。

## 运行示例

确保已经准备好可用的 Python 环境（virtualenv、conda、系统 Python 等均可）。

在 Windows（PowerShell）中：

```powershell
python -m pip install -U pip
pip install cullinan tornado
python examples\middleware_demo.py
```

在 Linux / macOS 中：

```bash
python -m pip install -U pip
pip install cullinan tornado
python examples/middleware_demo.py
```

典型输出（示例运行）：

```
INFO:__main__:Starting IOLoop for middleware demo
INFO:__main__:Performing request 1
INFO:__main__:Entered request context
INFO:__main__:Injected dependencies into handler
INFO:tornado.access:200 GET /middleware (127.0.0.1) 2.10ms
INFO:__main__:Exited request context
INFO:__main__:Response1: Hello from UserService (084297)  request_count=1
INFO:__main__:Performing request 2
INFO:__main__:Entered request context
INFO:__main__:Injected dependencies into handler
INFO:tornado.access:200 GET /middleware (127.0.0.1) 0.60ms
INFO:__main__:Exited request context
INFO:__main__:Response2: Hello from UserService (084297)  request_count=1
INFO:__main__:IOLoop stopped, exiting
```

说明：`RequestCounter` 为请求作用域类型，每次请求都会重置；`UserService` 为单例，其实例 id 在不同请求间保持不变。
