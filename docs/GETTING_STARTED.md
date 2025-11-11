# Cullinan Framework - Getting Started Guide

Welcome to Cullinan! This guide will help you get started with the Cullinan web framework.

## What is Cullinan?

Cullinan is a Python web framework built on top of Tornado, inspired by Spring Boot. It provides:

- 🎯 **Dependency Injection** - Spring-style automatic dependency management
- 🔄 **Lifecycle Management** - Complete service lifecycle with hooks
- 🚀 **Easy Routing** - Decorator-based route registration
- 📦 **Service Layer** - Built-in service architecture
- 🔌 **WebSocket Support** - First-class WebSocket integration
- ⚡ **High Performance** - Built on Tornado's async architecture

## Quick Start

### Installation

```bash
# Install from source
pip install path/to/Cullinan

# Or install in development mode
cd path/to/Cullinan
pip install -e .
```

### Your First Application

Create a file `app.py`:

```python
from cullinan import application
from cullinan.controller import controller, get_api

@controller(url='/api')
class HelloController:
    @get_api(url='/hello')
    def hello(self, query_params):
        return {'message': 'Hello, World!'}

if __name__ == '__main__':
    application.run()
```

Run your application:

```bash
python app.py
```

Visit `http://localhost:4080/api/hello` - you should see:

```json
{"message": "Hello, World!"}
```

## Core Concepts

### 1. Controllers

Controllers handle HTTP requests. Use decorators to define routes:

```python
from cullinan.controller import controller, get_api, post_api

@controller(url='/api/users')
class UserController:
    @get_api(url='')
    def list_users(self, query_params):
        return {'users': ['Alice', 'Bob']}
    
    @post_api(url='')
    def create_user(self, body_params):
        name = body_params.get('name')
        return {'created': True, 'name': name}
```

### 2. Services

Services contain business logic. Use `@service` decorator:

```python
from cullinan.service import service, Service

@service
class UserService(Service):
    def get_all_users(self):
        return ['Alice', 'Bob', 'Charlie']
    
    def create_user(self, name):
        # Business logic here
        return {'id': 1, 'name': name}
```

### 3. Dependency Injection

Inject services into controllers automatically:

```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject

@controller(url='/api/users')
class UserController:
    # Inject service using string annotation (no import needed!)
    user_service: 'UserService' = Inject()
    
    @get_api(url='')
    def list_users(self, query_params):
        # Use injected service directly
        users = self.user_service.get_all_users()
        return {'users': users}
```

**No need to import the Service class!** Just use string annotation.

### 4. Lifecycle Hooks

Services can hook into the application lifecycle:

```python
from cullinan.service import service, Service

@service
class DatabaseService(Service):
    def get_phase(self) -> int:
        return -100  # Start early (lower = earlier)
    
    def on_startup(self):
        """Called before web server starts"""
        print("Connecting to database...")
        self._connect()
    
    def on_shutdown(self):
        """Called when shutting down"""
        print("Closing database connection...")
        self._disconnect()
```

**Phase order**:
- `-200`: Configuration services (earliest)
- `-100`: Database, cache services
- `-50`: Background workers, bots
- `0`: Business services (default)
- `50`: Web-related services (latest)

## Project Structure

Recommended structure for a Cullinan project:

```
my-project/
├── app.py                 # Application entry point
├── .env                   # Environment variables
├── controllers/           # HTTP request handlers
│   ├── __init__.py
│   ├── user_controller.py
│   └── product_controller.py
├── services/              # Business logic
│   ├── __init__.py
│   ├── user_service.py
│   └── email_service.py
├── models/                # Data models
│   └── user.py
├── templates/             # HTML templates (optional)
└── static/                # Static files (optional)
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
SERVER_PORT=4080
SERVER_THREAD=1
DISCORD_TOKEN=your_token_here
DATABASE_URL=postgresql://localhost/mydb
```

Access in code:

```python
import os
token = os.getenv('DISCORD_TOKEN')
```

### Application Settings

Configure in your main file:

```python
from cullinan import application

if __name__ == '__main__':
    application.run()  # Uses default settings
```

## Next Steps

- 📖 [Complete Tutorial](./TUTORIAL.md) - Build a real application
- 🎯 [Dependency Injection Guide](./DEPENDENCY_INJECTION.md) - Master DI
- 🔄 [Lifecycle Management](./LIFECYCLE_MANAGEMENT.md) - Service lifecycle
- 🌐 [WebSocket Guide](./WEBSOCKET.md) - Real-time communication
- 📚 [API Reference](./API_REFERENCE.md) - Complete API docs
- 💡 [Examples](../examples/) - Code examples

## Getting Help

- 📄 Check the [FAQ](./FAQ.md)
- 💬 Ask questions in GitHub Issues
- 📖 Read the full documentation

## Examples

See the [examples directory](../examples/) for complete working examples:

- `basic/` - Simple Hello World application
- `service_examples.py` - Service layer examples
- `core_injection_example.py` - Dependency injection
- `discord_bot_lifecycle_example.py` - Discord bot with lifecycle
- `websocket_injection_example.py` - WebSocket with DI

---

**Ready to build?** Start with the [Complete Tutorial](./TUTORIAL.md)!

