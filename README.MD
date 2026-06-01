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
 \_____\__, _|_|_|_|_| |_|\__,_|_| |_|  
```

# Cullinan

**A lightweight, modular Python web framework with built-in IoC/DI**

Cullinan is built on Tornado (HTTP/WebSocket), but the developer-facing model is
not "grab an app object and register everything by hand". Instead, Cullinan
focuses on:
- Decorator-first business development with `@service`, `@controller`, `@get_api`, ...
- Runtime assembly from Python imports and decorator metadata, rather than manual app wiring
- Optional module boundaries with `@module` when you need ownership, reload, hot-plugging, and higher runtime stability
- Built-in IoC/DI with request scope and service lifecycle hooks

---

## ✨ Features

### Core Framework
- Simple decorator-based routing (`@controller`, `@get_api`, `@post_api`, ...)
- **Type-safe parameter system** with `Path`, `Query`, `Body`, `Header`, `File` (v0.90+)
- **Unified parameter syntax**: `param: Type = Type(...)` (v0.90a5+)
- **Pure type annotation as Query**: `page: int` automatically becomes Query parameter (v0.90a5+)
- **as_required() shortcut**: `File.as_required()`, `Body.as_required()` (v0.90a5+)
- **DynamicBody** for flexible request body access with safe accessors (v0.90a4+)
- **RawBody** for raw unparsed request body (bytes) (v0.90a5+)
- **FileInfo/FileList** for file upload with validation (v0.90a5+)
- **@field_validator** for dataclass field validation (v0.90a5+)
- **ResponseSerializer** for automatic response serialization (v0.90a5+)
- **Pluggable model handlers** for Pydantic and custom model integration (v0.90a5+)
- **Auto type conversion** and validation (ge, le, min_length, regex, etc.)
- Modular runtime with decorator metadata, DI, lifecycle management, and runtime switching
- Built-in IoC/DI with `InjectByName` and `Inject` support
- Unified lifecycle hooks (`on_post_construct`, `on_startup`, `on_shutdown`, `on_pre_destroy`) on all components
- Duck Typing lifecycle: no base class inheritance required (v0.92+)
- Designed for tests: resettable registries and request-scoped dependencies

### Services & WebSocket
- Service registry with dependency resolution
- WebSocket support via `@websocket_handler` and registry pattern
- Request context / request scope for per-request objects

### Deployment & Production
- Packaging-friendly (Nuitka, PyInstaller)
- Cross-platform: Windows, Linux, macOS
- Based on production-tested Tornado

---

## 📚 Documentation

### Language / 语言

- **[English Documentation](https://plumeink.github.io/Cullinan/)** – complete English docs
  - [Quick start](https://plumeink.github.io/Cullinan/getting_started/)
  - [Architecture](https://plumeink.github.io/Cullinan/architecture/) · [Lifecycle](https://plumeink.github.io/Cullinan/wiki/lifecycle/)
  - [IoC/DI 2.0](https://plumeink.github.io/Cullinan/wiki/ioc_di_v2/) · [Migration Guide](https://plumeink.github.io/Cullinan/import_migration_090/)
  - [RESTful routing](https://plumeink.github.io/Cullinan/wiki/restful_api/)
- **[中文文档](https://plumeink.github.io/Cullinan/zh/)** – 完整中文文档
  - [快速开始](https://plumeink.github.io/Cullinan/zh/getting_started/)
  - [架构](https://plumeink.github.io/Cullinan/zh/architecture/) · [生命周期](https://plumeink.github.io/Cullinan/zh/wiki/lifecycle/)
  - [IoC/DI 2.0](https://plumeink.github.io/Cullinan/zh/wiki/ioc_di_v2/) · [迁移指南](https://plumeink.github.io/Cullinan/zh/import_migration_090/)
  - [RESTful 路由](https://plumeink.github.io/Cullinan/zh/wiki/restful_api/)

### Version Notes

- Current series: **v0.93a5**
  - Application/runtime model centered on `Application`, `current_app()`, and the unified Web Runtime
  - Decorator-first component discovery based on Python import execution
  - `@module` as the structured boundary for ownership, reload, draining, and hot-pluggable runtime assembly
  - Unified lifecycle management with `on_post_construct`, `on_startup`, `on_shutdown`, `on_pre_destroy`
  - Built-in IoC/DI with `Inject()` and `InjectByName()`
  - Structured semantic diagnostics for discovery, injection, lifecycle, and compatibility APIs

---

## 🚀 Quick Start

### Install

Use pip from PyPI:

```bash
pip install -U pip
pip install cullinan
```

Ensure you have a working Python 3.8+ environment (virtualenv/conda/system Python are all fine).

### Minimal Application

```python
# minimal_app.py
from cullinan import Application, controller, get_api, module, service
from cullinan.adapter import TornadoAdapter
from cullinan.core import Inject


@service
class GreetingService:
    def greet(self) -> str:
        return "Hello from Cullinan!"


@controller(url="/hello")
class HelloController:
    greeting_service: GreetingService = Inject()

    @get_api(url="")
    def hello(self):
        return {"message": self.greeting_service.greet()}


@module
class RootModule:
    """Boundary declaration for owned packages and runtime assembly."""


app = Application.run(RootModule)
server = TornadoAdapter(dispatcher=app.web_runtime.dispatcher, runtime=app.web_runtime)

if __name__ == "__main__":
    server.run()
```

Run:

```bash
python minimal_app.py
# GET: http://localhost:4080/hello
```

In this model, you mainly write business services, controllers, and methods.
The `app` object above is the assembled runtime handle, not a manual registration center.
When you need clearer module ownership, reload, draining, and hot-plugging semantics,
`@module` becomes the boundary declaration that keeps the runtime stable.

For a more detailed onboarding, follow `docs/getting_started.md` (or `docs/zh/getting_started.md`).

---

## 💡 Dependency Injection Patterns

Cullinan ships with a core IoC/DI system. Recommended patterns:

### 1. InjectByName (recommended default)

```python
from cullinan import service, Service
from cullinan.core import InjectByName

@service
class EmailService(Service):
    def send_email(self, to, subject, body):
        print(f"Sending email to {to}: {subject}")
        return True

@service
class UserService(Service):
    """Service for user management with email dependency."""

    # Name-based injection, no direct import needed
    email_service = InjectByName('EmailService')

    def create_user(self, name, email):
        user = {'name': name, 'email': email}
        self.email_service.send_email(email, "Welcome", f"Welcome {name}!")
        return user
```

### 2. Inject + TYPE_CHECKING (IDE autocomplete)

```python
from typing import TYPE_CHECKING
from cullinan import service, Service
from cullinan.core import Inject

if TYPE_CHECKING:
    from services.email import EmailService

@service
class UserService(Service):
    # Type-hinted injection for better IDE support
    email_service: 'EmailService' = Inject()

    def create_user(self, name, email):
        self.email_service.send_email(email, "Welcome", f"Welcome {name}!")
        return {"name": name, "email": email}
```

### Controllers and RESTful decorators

```python
from cullinan.controller import controller, get_api, post_api
from cullinan.core import InjectByName
from cullinan.params import Query, Body

@controller(url='/api')
class UserController:
    # Inject the UserService by name
    user_service = InjectByName('UserService')

    # Type-safe query parameter (v0.90+)
    @get_api(url='/users')
    def get_user(self, id: Query(str)):
        return self.response_factory(
            status=200,
            body={"message": "User fetched successfully", "user_id": id},
        )

    # Type-safe body parameters (v0.90+)
    @post_api(url='/users')
    def create_user(self, name: Body(str, required=True), email: Body(str, required=True)):
        user = self.user_service.create_user(name, email)
        return self.response_factory(
            status=201,
            body={"message": "User created successfully", "data": user},
        )
```

> Note: RESTful decorators are defined as `def get_api(**kwargs)` etc. Only **keyword arguments** are supported. Use `@get_api(url='/users')`, not `@get_api('/users')`.

For full parameter system documentation, see `docs/parameter_system_guide.md`.

More DI patterns and controller examples are documented in `docs/wiki/injection.md` and `docs/wiki/restful_api.md` (and their Chinese counterparts).

---

## 📖 More Examples

The `examples/` folder contains additional runnable demos (HTTP, middleware, DI). Refer to:

- `examples/hello_http.py` – minimal HTTP example using the handler registry
- `examples/controller_di_middleware.py` – controller + DI + middleware integration

Each example is referenced from the docs so you can cross-check behavior with tests (`tests/` directory).

---

## 📖 Additional Documentation

For advanced topics, see the docs:

- **Configuration** – environment and config options
- **Packaging** – building executables with Nuitka/PyInstaller
- **Service Layer** – service patterns and DI
- **Registry Pattern** – unified registry behavior
- **Testing** – running tests and using test registries
- **Troubleshooting** – common issues and diagnostics

---

## 🔗 Links

- **Documentation**: [docs/README.md](docs/README.md)
- **GitHub**: https://github.com/plumeink/Cullinan
- **PyPI**: https://pypi.org/project/cullinan/
- **Issues**: https://github.com/plumeink/Cullinan/issues
- **Discussions**: https://github.com/plumeink/Cullinan/discussions

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.

---

## 💻 Maintainer

Plumeink

[<img src="https://avatars.githubusercontent.com/u/104434649?v=4" width = "40" height = "40"/>](https://github.com/plumeink)