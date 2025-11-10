![Python version](https://img.shields.io/badge/python-3.7%20|%203.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-blue)
![PyPI version](https://img.shields.io/pypi/v/cullinan.svg?style=flat&logo=pypi&color=green)
![PyPI downloads](https://img.shields.io/pypi/dm/cullinan.svg?style=flat&logo=pypi&color=blue)
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

**A lightweight, modular Python web framework with enhanced architecture for v0.7.0+**

Cullinan is built on Tornado and SQLAlchemy, designed to help you quickly build production-ready web applications with modern patterns like dependency injection, lifecycle management, and unified registry.

---

## ✨ Features

### Core Framework
- 🚀 **Easy to Use** - Simple decorator-based routing and intuitive API
- 🏗️ **Modular Architecture** - Core module with registry, DI, and lifecycle management
- 🔌 **Dependency Injection** - Optional DI system for complex applications
- ♻️ **Lifecycle Hooks** - Proper initialization and cleanup with `on_init`/`on_destroy`
- 🧪 **Test-Friendly** - Built-in testing utilities with mocks and test registries

### Services & WebSocket
- 🎯 **Enhanced Service Layer** - Service registry with dependency resolution
- 🌐 **WebSocket Support** - Full WebSocket integration with registry pattern
- 📋 **Unified Registry** - Consistent registration across services, handlers, and WebSockets
- 🔄 **Request Context** - Thread-safe request-scoped data management

### Deployment & Production
- 📦 **Packaging Ready** - Full Nuitka & PyInstaller support
- ⚙️ **Flexible Configuration** - Multiple configuration options
- 🌍 **Cross-Platform** - Windows, Linux, macOS
- 🏭 **Production Ready** - Built on battle-tested Tornado
- 🗄️ **SQLAlchemy Integration** - Built-in ORM support
- 🔧 **Smart Module Loading** - Auto-discovery for development, configurable for packaging

---

## 📚 Documentation

### Language / 语言

- **[English Documentation](docs/README.md)** - Complete English documentation
- **[中文文档](docs/zh/README_zh.md)** - 完整中文文档

### Version-Specific Documentation

- **v0.7.0-alpha1 (Current)** - New architecture with enhanced features
  - Core module with registry, DI, and lifecycle management
  - Enhanced service layer with dependency injection
  - WebSocket support with unified registry
  - Request context management
  - See [CHANGELOG.md](CHANGELOG.md) for migration guide from v0.6.x

---

## 🚀 Quick Start

## 📦 Installation

### From PyPI (Stable Release)

```bash
pip install cullinan
```

### Basic Application

```python
# app.py
from cullinan import configure, application
from cullinan.controller import controller, get_api

# Configure for packaging (optional in development)
configure(user_packages=['your_app'])

@controller(url='/api')
class HelloController:
    @get_api(url='/hello')
    def hello(self, query_params):
        name = query_params.get('name', 'World')
        return self.response_build(
            status=200, 
            message=f"Hello, {name}!"
        )

if __name__ == '__main__':
    application.run()
```

### Run

```bash
python app.py
# Visit: http://localhost:4080/api/hello?name=Cullinan
```

---

## 💡 Full Example with Services

### Project Structure

```
my_app/
├── main.py              # Entry point
├── controllers/         # Controllers
│   ├── __init__.py
│   └── api.py
├── services/            # Services (NEW in v0.7.0)
│   ├── __init__.py
│   ├── user.py
│   └── email.py
└── models/              # Models
    ├── __init__.py
    └── user.py
```

### Service Layer (`services/email.py`)

```python
from cullinan import service, Service

@service
class EmailService(Service):
    """Service for sending emails."""
    
    def on_init(self):
        """Lifecycle hook - called when service is registered."""
        print("EmailService initialized")
    
    def send_email(self, to, subject, body):
        print(f"Sending email to {to}: {subject}")
        # Your email logic here
        return True
```

### Service with Dependencies (`services/user.py`)

```python
from cullinan import service, Service

@service(dependencies=['EmailService'])
class UserService(Service):
    """Service for user management with email dependency."""
    
    def on_init(self):
        """Access dependencies after initialization."""
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name, email):
        user = {'name': name, 'email': email}
        # Send welcome email using injected service
        self.email.send_email(email, "Welcome", f"Welcome {name}!")
        return user
    
    def on_destroy(self):
        """Cleanup hook - called on shutdown."""
        print("UserService shutting down")
```

### Controller (`controllers/api.py`)

```python
from cullinan.controller import controller, get_api, post_api

@controller(url='/api')
class UserController:
    
    @get_api(url='/users', query_params=['id'])
    def get_user(self, query_params):
        user_id = query_params.get('id')
        return self.response_build(
            status=200, 
            message="User fetched successfully",
            data={"user_id": user_id}
        )
    
    @post_api(url='/users', body_params=['name', 'email'])
    def create_user(self, body_params):
        # Access service through registry
        user = self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
        return self.response_build(
            status=201, 
            message="User created successfully",
            data=user
        )
```

### WebSocket Support (`controllers/chat.py`)

```python
from cullinan import websocket_handler

@websocket_handler(url='/ws/chat')
class ChatHandler:
    """WebSocket handler with registry integration."""
    
    def on_init(self):
        """Lifecycle hook for WebSocket handlers."""
        self.clients = set()
    
    def on_open(self):
        """Called when WebSocket connection opens."""
        self.clients.add(self)
        print(f"Client connected: {len(self.clients)} total")
    
    def on_message(self, message):
        """Handle incoming WebSocket message."""
        # Broadcast to all clients
        for client in self.clients:
            client.write_message(f"Broadcast: {message}")
    
    def on_close(self):
        """Called when WebSocket connection closes."""
        self.clients.remove(self)
        print(f"Client disconnected: {len(self.clients)} remaining")
```

### Application (`main.py`)

```python
from cullinan import configure, application

# Configure for packaging
configure(
    user_packages=['my_app'],
    verbose=True  # Enable logging
)

def main():
    application.run()

if __name__ == '__main__':
    main()
```

---

## 🆕 What's New in v0.7.0

### Core Module
- **Registry Pattern**: Unified registration for services, handlers, WebSockets
- **Dependency Injection**: Optional DI for managing complex dependencies
- **Lifecycle Management**: Hooks for initialization and cleanup
- **Request Context**: Thread-safe context for request-scoped data

### Enhanced Service Layer
```python
# Simple service (backward compatible)
@service
class SimpleService(Service):
    pass

# Service with dependencies
@service(dependencies=['DatabaseService'])
class AdvancedService(Service):
    def on_init(self):
        self.db = self.dependencies['DatabaseService']
```

### WebSocket Integration
```python
# WebSocket with lifecycle support
@websocket_handler(url='/ws/updates')
class UpdatesHandler:
    def on_init(self):
        # Initialize resources
        pass
```

### Testing Utilities
```python
from cullinan.testing import TestRegistry, MockService

def test_user_service():
    registry = TestRegistry()
    registry.register_mock('EmailService', MockEmailService())
    # Test with mocked dependencies
```

---

## 📖 Documentation Structure

```
docs/
├── README.md                    # Documentation index
├── index.md                     # Framework overview
├── 01-configuration.md          # Configuration guide
├── 02-packaging.md              # Packaging guide
├── 03-troubleshooting.md        # Troubleshooting
├── 04-quick-reference.md        # Quick reference
├── 05-build-scripts.md          # Build scripts guide
├── 07-registry-center.md        # Registry pattern guide (NEW)
├── 08-service-layer.md          # Service layer guide (NEW)
└── v0.6x/                       # v0.6.x documentation (legacy)
```

---

## 🔗 Links

- **Documentation**: [docs/README.md](docs/README.md)
- **GitHub**: https://github.com/plumeink/Cullinan
- **PyPI**: https://pypi.org/project/cullinan/
- **Issues**: https://github.com/plumeink/Cullinan/issues
- **Discussions**: https://github.com/plumeink/Cullinan/discussions

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built on [Tornado](https://www.tornadoweb.org/)
- ORM powered by [SQLAlchemy](https://www.sqlalchemy.org/)
- Packaging powered by [Nuitka](https://nuitka.net/) and [PyInstaller](https://pyinstaller.org/)

---

## 💻 Maintainer

[<img src="https://avatars.githubusercontent.com/u/104434649?v=4" width = "40" height = "40"/>](https://github.com/plumeink)