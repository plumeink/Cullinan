![Python version](https://img.shields.io/badge/python-3.7%20|%203.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-blue)
![PyPI version](https://img.shields.io/pypi/v/cullinan.svg?style=flat&logo=pypi&color=green)
![PyPI downloads](https://img.shields.io/pypi/dm/cullinan.svg?style=flat&logo=pypi&color=blue)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/plumeink/Cullinan)
![GitHub stars](https://img.shields.io/github/stars/plumeink/cullinan.svg?style=flat&logo=github&color=white)
![License](https://img.shields.io/github/license/plumeink/cullinan.svg?style=flat&color=white)

```
   _____      _ _ _
  / ____|    | | (_)
 | |    _   _| | |_ _ __   __ _ _ __
 | |   | | | | | | | '_ \ / _` | '_ \
 | |___| |_| | | | | | | | (_| | | | |
  \_____\__,_|_|_|_|_| |_|\__,_|_| |_|
```

# Cullinan

**A business-first Python web framework for building applications through decorators, module boundaries, and built-in IoC/DI.**

Cullinan is a Python Web Framework for developers who want to organize applications around
business services, controllers, and methods instead of manually wiring an app object.
Its default path is decorator-first discovery plus `configure(root_module=...)` and `run()`,
with `@module` used as the application boundary when ownership, runtime structure, and
stability matter.

---

## What is Cullinan?

Cullinan is designed to make the framework work around your business architecture, not the
other way around.

- **Business-first application model** - write services, controllers, middleware, and methods first
- **Decorator-first discovery** - let Python imports and decorator metadata assemble the runtime
- **Structured module boundaries** - use `@module` to express ownership and runtime boundaries
- **Built-in IoC/DI and lifecycle** - keep application wiring inside the framework model
- **Public semantic path** - build, run, test, and extend applications through stable public APIs

Cullinan is not centered on treating an app object as a manual registration hub. The
recommended development flow is to declare business components, define a root module when
structure matters, and let the framework assemble the application runtime.

---

## Why Cullinan?

### 1. Framework semantics before manual wiring

Cullinan gives you a clear application model: declare components with decorators, let the
framework discover them, and keep explicit runtime internals as an advanced path rather than
the default onboarding path.

### 2. Application boundaries that scale past toy examples

`@module` is more than a naming convention. It is the structured boundary for owned packages,
runtime composition, and higher-level lifecycle behavior when your application grows.

### 3. Web, DI, lifecycle, and testing in one model

Routing, parameter binding, dependency injection, lifecycle hooks, middleware, and test flow
all sit inside one framework vocabulary instead of forcing developers to stitch together
multiple unrelated patterns.

### 4. A Pythonic path for business applications

Cullinan is designed to keep developers focused on business architecture and business methods.
You can stay on the public path for most application work and only move into internals when
you intentionally need advanced extension behavior.

---

## Framework capabilities

| Capability layer | What Cullinan provides |
| --- | --- |
| **Application composition** | `configure(root_module=...)`, decorator-driven discovery, structured runtime assembly |
| **Web API model** | `@controller`, RESTful decorators, WebResponse, middleware pipeline, WebSocket support |
| **Parameter system** | Typed `Path`, `Query`, `Body`, validation, conversion, and controller-method binding |
| **IoC/DI and lifecycle** | `Inject()`, `InjectByName()`, request scope, startup/shutdown hooks, component lifecycle |
| **Runtime boundaries** | `@module` ownership, clearer package structure, better runtime organization |
| **Testing and delivery** | `get_asgi_app()`, resettable registries, packaging-friendly runtime, cross-platform support |

Cullinan's goal is not to expose every internal knob on the README homepage. The goal is to
provide a coherent framework model that remains readable from first contact through production use.

---

## Install

Cullinan is published on PyPI and currently supports **Python 3.7+**.

```bash
pip install -U pip
pip install cullinan
```

After installation, start from the minimal example in [`examples/minimal_app/`](examples/minimal_app)
or the repository guide in [`docs/examples.md`](docs/examples.md).

---

## Quick Start

The recommended starting point is: define business components, declare the root boundary,
configure the app, then run it.

```python
from cullinan import Inject, configure, controller, get_api, module, run, service


@service
class GreetingService:
    def greet(self) -> str:
        return "Hello from Cullinan!"


@controller(url="/hello")
class HelloController:
    greeting_service: "GreetingService" = Inject()

    @get_api(url="")
    def hello(self):
        return {"message": self.greeting_service.greet()}


@module
class RootModule:
    """Declare the application boundary when structure matters."""


def create_app():
    return configure(root_module=RootModule)


if __name__ == "__main__":
    create_app()
    run()
```

Run it:

```bash
python minimal_app.py
```

Then open:

```text
http://localhost:4080/hello
```

This example shows the default Cullinan path:

- business service first
- controller methods as the public web surface
- `Inject()` for framework-managed wiring
- `@module` as the runtime boundary
- `configure(root_module=...)` plus `run()` as the startup flow

---

## Learning path

If you are new to Cullinan, use this order:

1. [`examples/minimal_app/`](examples/minimal_app) - shortest public entrypoint
2. [`examples/controller_service_inject/`](examples/controller_service_inject) - service/controller layering with `Inject()`
3. [`examples/middleware_and_module/`](examples/middleware_and_module) - `@module` boundaries and middleware semantics
4. [`examples/parameter_handling/`](examples/parameter_handling) - method-level `Path`, `Query`, and `Body`
5. [`examples/testing_flow/`](examples/testing_flow) - public-API testing with `get_asgi_app()`

Then move into the documentation knowledge base:

- [`docs/README.md`](docs/README.md) - English knowledge base home
- [`docs/zh/README.md`](docs/zh/README.md) - 中文知识库首页
- [`docs/getting_started.md`](docs/getting_started.md) - recommended application entry
- [`docs/framework_semantics.md`](docs/framework_semantics.md) - framework concepts and semantics
- [`docs/examples.md`](docs/examples.md) - example navigation page

---

## Documentation

### English

- [Documentation home](https://plumeink.github.io/Cullinan/)
- [Getting Started](https://plumeink.github.io/Cullinan/getting_started/)
- [Framework Semantics](https://plumeink.github.io/Cullinan/framework_semantics/)
- [Examples](https://plumeink.github.io/Cullinan/examples/)
- [Dependency Injection Guide](https://plumeink.github.io/Cullinan/dependency_injection_guide/)
- [Web Runtime Guide](https://plumeink.github.io/Cullinan/web_runtime_guide/)
- [Parameter System Guide](https://plumeink.github.io/Cullinan/parameter_system_guide/)
- [Testing & Verification](https://plumeink.github.io/Cullinan/testing/)

### 中文

- [文档首页](https://plumeink.github.io/Cullinan/zh/)
- [快速开始](https://plumeink.github.io/Cullinan/zh/getting_started/)
- [框架语义](https://plumeink.github.io/Cullinan/zh/framework_semantics/)
- [示例导航](https://plumeink.github.io/Cullinan/zh/examples/)
- [依赖注入指南](https://plumeink.github.io/Cullinan/zh/dependency_injection_guide/)
- [Web Runtime 指南](https://plumeink.github.io/Cullinan/zh/web_runtime_guide/)
- [参数系统指南](https://plumeink.github.io/Cullinan/zh/parameter_system_guide/)
- [测试与验证](https://plumeink.github.io/Cullinan/zh/testing/)

---

## Current series

**v0.93a6.post1** focuses the public application path around:

- `configure(root_module=...)` and `run()`
- decorator-first discovery through Python imports
- `@module` as the structured boundary for runtime ownership
- built-in IoC/DI, lifecycle, and semantic diagnostics
- unified example and documentation guidance around the current public API
- consistency fixes for high-level public runtime entrypoints

Version-specific details and migration notes live in the documentation knowledge base rather
than in the homepage narrative.

---

## Project links

- **GitHub**: https://github.com/plumeink/Cullinan
- **PyPI**: https://pypi.org/project/cullinan/
- **Issues**: https://github.com/plumeink/Cullinan/issues
- **Discussions**: https://github.com/plumeink/Cullinan/discussions

---

## License

MIT License - see [LICENSE](LICENSE) for details.
