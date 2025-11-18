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

Cullinan is built on Tornado (HTTP/WebSocket) and focuses on:
- A unified registry model for controllers, services, handlers
- Built-in IoC/DI with request scope and service lifecycle hooks
- Production-friendly startup/shutdown flow on a default port **4080**

---

## ✨ Features

### Core Framework
- Simple decorator-based routing (`@controller`, `@get_api`, `@post_api`, ...)
- Modular architecture with registry, DI, and lifecycle management
- Built-in IoC/DI with `InjectByName` and `Inject` support
- Lifecycle hooks (e.g. `on_init`, `on_destroy`) on services
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
  - [IoC/DI details](https://plumeink.github.io/Cullinan/wiki/injection/)
  - [RESTful routing](https://plumeink.github.io/Cullinan/wiki/restful_api/)
- **[中文文档](https://plumeink.github.io/Cullinan/zh/)** – 完整中文文档
  - [快速开始](https://plumeink.github.io/Cullinan/zh/getting_started/)
  - [架构](https://plumeink.github.io/Cullinan/zh/architecture/) · [生命周期](https://plumeink.github.io/Cullinan/zh/wiki/lifecycle/)
  - [IoC/DI 说明](https://plumeink.github.io/Cullinan/zh/wiki/injection/)
  - [RESTful 路由](https://plumeink.github.io/Cullinan/zh/wiki/restful_api/)

### Version Notes

- Current series: **v0.7x+**
  - Core module with registry, DI, lifecycle management
  - Enhanced service layer with dependency injection
  - WebSocket support with unified registry
  - Request context management

- Deprecated modules removed:
  - `cullinan.registry` → use `cullinan.handler` and `cullinan.controller`
  - `cullinan.websocket` → use `cullinan.websocket_registry`

For older code, see the **API Migration Guide** in the docs.

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
# app.py
from cullinan import application
from cullinan.controller import controller, get_api

@controller(url='/api')
class HelloController:
    # Explicitly declare all query parameters used by this handler
    @get_api(url='/hello', query_params=['name'])
    def hello(self, query_params):
        name = query_params.get('name', 'World')
        return self.response_build(
            status=200,
            message=f"Hello, {name}!"
        )

if __name__ == '__main__':
    # Framework-level entrypoint, no manual app instantiation required
    application.run()
```

Run:

```bash
python app.py
# Visit: http://localhost:4080/api/hello?name=Cullinan
```

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

@controller(url='/api')
class UserController:
    # Inject the UserService by name
    user_service = InjectByName('UserService')

    @get_api(url='/users', query_params=['id'])
    def get_user(self, query_params):
        user_id = query_params.get('id')
        return self.response_build(
            status=200,
            message="User fetched successfully",
            data={"user_id": user_id},
        )

    @post_api(url='/users', body_params=['name', 'email'])
    def create_user(self, body_params):
        user = self.user_service.create_user(
            body_params['name'],
            body_params['email'],
        )
        return self.response_build(
            status=201,
            message="User created successfully",
            data=user,
        )
```

> Note: RESTful decorators are defined as `def get_api(**kwargs)` etc. Only **keyword arguments** are supported. Use `@get_api(url='/users')`, not `@get_api('/users')`.

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