# Cullinan Complete Guide

[English](00-complete-guide.md) | [中文](zh/00-complete-guide_zh.md)

---

Welcome to Cullinan! This guide will help you get started and master the framework.

## 📚 Table of Contents

### Getting Started
1. [Installation & Setup](#installation--setup)
2. [Quick Start Tutorial](#quick-start-tutorial) → [Example](../examples/basic/hello_world.py)
3. [Project Structure](#project-structure)

### Core Concepts
4. [Configuration System](01-configuration.md) → [Examples](../examples/config/)
5. [Controllers & Routing](#controllers--routing) → [Example](../examples/basic/test_controller.py)
6. [Services & Business Logic](#services--business-logic)
7. [Request & Response](#request--response)
8. [Database Integration](#database-integration)

### Advanced Topics
9. [Packaging & Deployment](02-packaging.md) → [Scripts](../scripts/)
10. [Build Scripts](05-build-scripts.md)
11. [WebSocket Support](#websocket-support)
12. [Hooks & Middleware](#hooks--middleware)

### Reference
13. [API Reference](#api-reference)
14. [Troubleshooting](03-troubleshooting.md)
15. [FAQ](#faq)

---

## Installation & Setup

### System Requirements

- Python 3.7 or higher
- pip (Python package manager)

### Install from PyPI

```bash
pip install cullinan
```

> **Note**: If the version on PyPI is outdated, please install the latest version from the source.

### Install from Source (Recommended for the latest features)

```bash
git clone https://github.com/plumeink/Cullinan.git
cd Cullinan
pip install -e .
```

### Verify Installation

```bash
python -c "import cullinan; print('Cullinan installed successfully')"
```

---

## Quick Start Tutorial

### 1. Create Your First Application

Create a file named `app.py`:

```python
# app.py
from cullinan import configure, application
from cullinan.controller import controller, get_api

# Configure Cullinan
configure(user_packages=['__main__'])

@controller(url='/api')
class HelloController:
    @get_api(url='/hello')
    def hello(self, query_params):
        return {'message': 'Hello, Cullinan!'}

if __name__ == '__main__':
    application.run()
```

**📝 Full Example:** [`examples/basic/hello_world.py`](../examples/basic/hello_world.py)

### 2. Run the Application

```bash
python app.py
```

Visit: http://localhost:8080/api/hello

### 3. Test the API

```bash
curl http://localhost:8080/api/hello
# Output: {"message": "Hello, Cullinan!"}
```

---

## Project Structure

### Recommended Directory Layout

```
my_app/
├── main.py                 # Application entry point
├── controllers/            # Controller modules
│   ├── __init__.py
│   ├── user_controller.py
│   └── api_controller.py
├── services/               # Business logic services
│   ├── __init__.py
│   ├── user_service.py
│   └── auth_service.py
├── models/                 # Database models
│   ├── __init__.py
│   └── user.py
├── config/                 # Configuration files
│   ├── __init__.py
│   └── settings.py
└── tests/                  # Unit tests
    └── test_api.py
```

**📝 See example structure:** [`examples/`](../examples/)

---

## Controllers & Routing

### Basic Controller

Controllers handle HTTP requests and define API endpoints.

```python
from cullinan.controller import controller, get_api, post_api

@controller(url='/users')
class UserController:
    """User management controller"""
    
    @get_api(url='/', query_params=['id'])
    def get_user(self, query_params):
        """Get a user by ID"""
        user_id = query_params.get('id')
        return self.service['UserService'].get_user(user_id)
    
    @post_api(url='/', body_params=['name', 'email'])
    def create_user(self, body_params):
        """Create a new user"""
        return self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
```

**📝 Full Example:** [`examples/basic/crud_example.py`](../examples/basic/crud_example.py)

### Supported HTTP Methods

| Decorator | HTTP Method | Purpose |
|---|---|---|
| `@get_api` | GET | Retrieve data |
| `@post_api` | POST | Create a resource |
| `@put_api` | PUT | Update a resource |
| `@delete_api` | DELETE | Delete a resource |
| `@patch_api` | PATCH | Partially update |

---

## Services & Business Logic

Services contain business logic, separate from controllers.

### Creating a Service

```python
from cullinan.service import Service, service
from cullinan.dao import Conn

@service
class UserService(Service):
    """User business logic"""
    
    def __init__(self):
        super().__init__()
        self.db = Conn.conn()
    
    def get_user(self, user_id):
        """Get a user by ID"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user:
            self.response.set_body({'id': user.id, 'name': user.name})
        else:
            self.response.set_status(404)
            self.response.set_body({'error': 'User not found'})
        
        return self.response
```

---

## API Reference

### Decorators

| Decorator | Parameters | Example |
|---|---|---|
| `@controller` | `url` | `@controller(url='/api')` |
| `@get_api` | `url`, `query_params`, `headers` | `@get_api(url='/users', query_params=['id'])` |
| `@post_api` | `url`, `body_params`, `query_params` | `@post_api(url='/users', body_params=['name'])` |
| `@service` | No parameters | `@service` |

### Response Object

| Method | Description |
|---|---|
| `set_status(status, msg='')` | Set the status code |
| `set_body(data)` | Set the response body |
| `add_header(name, value)` | Add a response header |

---

## Next Steps

- **Deploy Your Application**: See the [Packaging Guide](02-packaging.md)
- **Optimize Performance**: See the [Build Scripts](05-build-scripts.md)
- **Get Help**: See the [Troubleshooting Guide](03-troubleshooting.md)

---

## Example Index

All examples are located in the [`examples/`](../examples/) directory:

- **Basic Examples**
  - [Hello World](../examples/basic/hello_world.py)
  - [CRUD API](../examples/basic/crud_example.py)

- **Configuration Examples**
  - [Code-based Configuration](../examples/config/config_example.py)

---

**Happy coding with Cullinan!** 🎉

