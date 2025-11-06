# Cullinan Framework - Complete Guide

Welcome to Cullinan! This guide will help you get started and master the framework.

## 📚 Table of Contents

### Getting Started
1. [Installation & Setup](#installation--setup)
2. [Quick Start Tutorial](#quick-start-tutorial) → [Example](../examples/basic/hello_world.py)
3. [Project Structure](#project-structure)

### Core Concepts
4. [Configuration System](zh/01-configuration.md) → [Examples](../examples/config/)
5. [Controllers & Routing](#controllers--routing) → [Example](../examples/basic/test_controller.py)
6. [Services & Business Logic](#services--business-logic)
7. [Request & Response](#request--response)
8. [Database Integration](#database-integration)

### Advanced Topics
9. [Packaging & Deployment](zh/02-packaging.md) → [Scripts](../scripts/)
10. [Build Scripts](zh/05-build-scripts.md)
11. [WebSocket Support](#websocket-support)
12. [Hooks & Middleware](#hooks--middleware)
13. [Method Injection](#method-injection)

### Reference
14. [API Reference](#api-reference)
15. [Troubleshooting](zh/03-troubleshooting.md)
16. [FAQ](#faq)

---

## Installation & Setup

### Requirements

- Python 3.7 or higher
- pip (Python package installer)

### Install from PyPI

```bash
pip install cullinan
```

> **注意**: 如果 PyPI 上的版本较旧，请从源码安装最新版本。

### Install from Source (Recommended for Latest Features)

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

**📝 See complete example:** [`examples/basic/hello_world.py`](../examples/basic/hello_world.py)

### 2. Run Your Application

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

### Recommended Layout

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

Controllers handle HTTP requests and define your API endpoints.

```python
from cullinan.controller import controller, get_api, post_api

@controller(url='/users')
class UserController:
    """User management controller"""
    
    @get_api(url='/', query_params=['id'])
    def get_user(self, query_params):
        """Get user by ID"""
        user_id = query_params.get('id')
        return self.service['UserService'].get_user(user_id)
    
    @post_api(url='/', body_params=['name', 'email'])
    def create_user(self, body_params):
        """Create new user"""
        return self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
```

**📝 Full example:** [`examples/basic/test_controller.py`](../examples/basic/test_controller.py)

### Supported HTTP Methods

| Decorator | HTTP Method | Usage |
|-----------|-------------|-------|
| `@get_api` | GET | Retrieve data |
| `@post_api` | POST | Create new resource |
| `@put_api` | PUT | Update resource |
| `@delete_api` | DELETE | Delete resource |
| `@patch_api` | PATCH | Partial update |

### URL Parameters

#### Query Parameters

```python
@get_api(url='/search', query_params=['keyword', 'page'])
def search(self, query_params):
    keyword = query_params.get('keyword')
    page = query_params.get('page', 1)
    # ...
```

**Usage:** `/search?keyword=python&page=2`

#### Body Parameters (JSON)

```python
@post_api(url='/create', body_params=['name', 'age'])
def create(self, body_params):
    name = body_params['name']
    age = body_params['age']
    # ...
```

**Request:**
```bash
curl -X POST http://localhost:8080/create \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "age": 30}'
```

#### Path Parameters

```python
@controller(url='/api')
class ArticleController:
    @get_api(url='/articles/([0-9]+)')
    def get_article(self, article_id):
        # article_id from URL path
        return {'id': article_id}
```

**Usage:** `/api/articles/123`

---

## Services & Business Logic

Services contain your business logic, separated from controllers.

### Creating a Service

```python
from cullinan.service import Service, service

@service
class UserService(Service):
    """User business logic"""
    
    def __init__(self):
        super().__init__()
        from cullinan.dao import Conn
        self.db = Conn.conn()
    
    def get_user(self, user_id):
        """Get user by ID"""
        # Access database directly
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user:
            self.response.set_body({'id': user.id, 'name': user.name})
        else:
            self.response.set_status(404)
            self.response.set_body({'error': 'User not found'})
        
        return self.response
    
    def create_user(self, name, email):
        """Create new user"""
        user = User(name=name, email=email)
        self.db.add(user)
        self.db.commit()
        
        self.response.set_body({'id': user.id, 'name': user.name})
        return self.response
```

### Using Services in Controllers

Services are automatically injected into controllers:

```python
@controller(url='/api')
class UserController:
    @get_api(url='/user')
    def get_user(self, query_params):
        # Access service through self.service
        return self.service['UserService'].get_user(
            query_params['id']
        )
```

---

## Request & Response

### Request Object

The request object provides access to request data:

```python
def my_handler(self, query_params):
    # Get query parameters
    name = query_params.get('name')
    
    # Access raw request (Tornado HTTPServerRequest)
    headers = self.request.headers
    method = self.request.method
    uri = self.request.uri
```

### Response Object

Control your API responses:

```python
from cullinan.service import Service, service

@service
class MyService(Service):
    def process(self, data):
        # Set response status
        self.response.set_status(200)
        
        # Add response headers
        self.response.add_header('Content-Type', 'application/json')
        
        # Set response body
        self.response.set_body({
            'success': True,
            'data': data
        })
        
        return self.response
```

### Status Codes

Common HTTP status codes:

```python
# Success
self.response.set_status(200)  # OK
self.response.set_status(201)  # Created

# Client Errors
self.response.set_status(400)  # Bad Request
self.response.set_status(401)  # Unauthorized
self.response.set_status(404)  # Not Found

# Server Errors
self.response.set_status(500)  # Internal Server Error
```

---

## Database Integration

Cullinan integrates with SQLAlchemy for database operations.

### Setup Database

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = "sqlite:///./app.db"
# Or PostgreSQL: "postgresql://user:pass@localhost/dbname"
# Or MySQL: "mysql://user:pass@localhost/dbname"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
```

### Define Models

```python
# models/user.py
from sqlalchemy import Column, Integer, String
from config.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
```

### Database Access

Cullinan provides `Conn` class for database connections using SQLAlchemy:

```python
from cullinan.dao import Conn
from models.user import User

class UserDAO:
    """用户数据访问类"""
    
    def __init__(self):
        self.session = Conn.conn()
    
    def get_user(self, user_id):
        return self.session.query(User).filter(
            User.id == user_id
        ).first()
    
    def create_user(self, name, email):
        user = User(name=name, email=email)
        self.session.add(user)
        self.session.commit()
        return user
    
    def close(self):
        self.session.close()
```

**Note**: Configure database connection via environment variables:
- `DB_TYPE` - Database type ('mysql' or 'sqlite')
- `DB_USERNAME`, `DB_PASSWORD` - Credentials
- `DB_HOST`, `DB_PORT` - Connection info
- `DB_NAME` - Database name
- `DB_CODING` - Character encoding

---

## WebSocket Support

Cullinan supports WebSocket connections for real-time communication.

### Creating a WebSocket Handler

```python
from cullinan.websocket import WebSocketController, websocket

@websocket(url='/ws')
class ChatWebSocket(WebSocketController):
    def on_open(self):
        """Called when connection is opened"""
        print(f"Client connected: {self.request.remote_ip}")
    
    def on_message(self, message):
        """Called when message is received"""
        print(f"Received: {message}")
        # Echo message back
        self.write_message(f"Echo: {message}")
    
    def on_close(self):
        """Called when connection is closed"""
        print("Client disconnected")
```

### Client-side Usage

```javascript
// JavaScript WebSocket client
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = () => {
    console.log('Connected');
    ws.send('Hello Server!');
};

ws.onmessage = (event) => {
    console.log('Received:', event.data);
};

ws.onclose = () => {
    console.log('Disconnected');
};
```

---

## Hooks & Middleware

Hooks allow you to execute code before or after request handling.

### Global Hooks

```python
from cullinan.hooks import before_request, after_request

@before_request
def auth_check(request):
    """Check authentication before processing request"""
    token = request.headers.get('Authorization')
    if not token:
        raise UnauthorizedException()

@after_request
def add_cors_headers(response):
    """Add CORS headers to all responses"""
    response.add_header('Access-Control-Allow-Origin', '*')
    return response
```

### Controller-level Hooks

```python
from cullinan.controller import controller, before_action, after_action

@controller(url='/api')
class SecureController:
    @before_action
    def check_auth(self):
        """Run before every action in this controller"""
        if not self.is_authenticated():
            raise UnauthorizedException()
    
    @get_api(url='/data')
    def get_data(self, query_params):
        return {'data': 'sensitive'}
```

---

## Method Injection

Cullinan automatically injects dependencies into your services.

### Available Injections

```python
@service
class MyService(Service):
    def __init__(self):
        super().__init__()
        # These are automatically injected:
        # self.response - Response object
        # self.service - Access to other services
        
        # Database access (manual setup)
        from cullinan.dao import Conn
        self.db = Conn.conn()
```

### Cross-Service Communication

```python
@service
class OrderService(Service):
    def __init__(self):
        super().__init__()
        from cullinan.dao import Conn
        self.db = Conn.conn()
    
    def create_order(self, user_id, product_id):
        # Use other services
        user = self.service['UserService'].get_user(user_id)
        product = self.service['ProductService'].get_product(product_id)
        
        # Business logic with database
        order = Order(user_id=user_id, product_id=product_id)
        self.db.add(order)
        self.db.commit()
        
        self.response.set_body({'order_id': order.id})
        return self.response
```

---

## API Reference

### Application Module

```python
from cullinan import application

# Run the application
application.run()
```

**Configuration via environment variables:**
- `SERVER_PORT` - Port number (default: 4080)
- `SERVER_THREAD` - Number of threads (optional)
- `.env` file - Automatically loaded from current directory

### Controller Decorators

- `@controller(url='/path')` - Define a controller
- `@get_api(url='/path', query_params=[], headers=[])` - GET endpoint
- `@post_api(url='/path', body_params=[], query_params=[], headers=[])` - POST endpoint
- `@put_api(url='/path', body_params=[], query_params=[], headers=[])` - PUT endpoint
- `@delete_api(url='/path', query_params=[], headers=[])` - DELETE endpoint
- `@patch_api(url='/path', body_params=[], query_params=[], headers=[])` - PATCH endpoint

### Service Decorator

- `@service` - Register a service class (no parameters required)

### Database Access

- `Conn.conn()` - Get database session
- `Conn.save()` - Create all tables defined in models
- `Conn.Base` - SQLAlchemy declarative base for models

### WebSocket Decorator

- `@websocket(url='/ws')` - Register WebSocket handler

---

## FAQ

### Q: How do I handle errors globally?

A: Use exception handlers:

```python
from cullinan.exceptions import CullinanException

class NotFoundException(CullinanException):
    def __init__(self, message="Not Found"):
        super().__init__(404, message)

# In your service:
raise NotFoundException("User not found")
```

### Q: Can I use async/await?

A: Yes, Cullinan is built on Tornado which supports async:

```python
@get_api(url='/async-data')
async def get_async_data(self, query_params):
    data = await self.async_fetch_data()
    return data
```

### Q: How do I add CORS support?

A: Use hooks:

```python
from cullinan.hooks import after_request

@after_request
def add_cors(response):
    response.add_header('Access-Control-Allow-Origin', '*')
    response.add_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
    return response
```

### Q: How do I serve static files?

A: Static files are automatically served from `./static` and `./templates` directories in your working directory. Configure paths via:

```python
# In your application setup
# Static files will be served from:
# - ./static/  → /static/
# - ./templates/ → template rendering
```

---

## Next Steps

- **Deploy your app**: See [Packaging Guide](zh/02-packaging.md)
- **Optimize performance**: See [Build Scripts](zh/05-build-scripts.md)
- **Get help**: Check [Troubleshooting](zh/03-troubleshooting.md)

---

## Examples Index

All examples are available in the [`examples/`](../examples/) directory:

- **Basic Examples**
  - [Hello World](../examples/basic/hello_world.py)
  - [Test Controller](../examples/basic/test_controller.py)

- **Configuration Examples**
  - [Code Configuration](../examples/config/config_example.py)
  - [JSON Configuration](../examples/config/cullinan.json)

- **Packaging Examples**
  - [Packaging Test](../examples/packaging/packaging_test.py)
  - [Diagnostic Tool](../examples/packaging/diagnose_app.py)

---

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](../CONTRIBUTING.md).

---

## License

MIT License - see [LICENSE](../LICENSE) for details.

