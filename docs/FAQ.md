# Frequently Asked Questions (FAQ)

## General Questions

### What is Cullinan?

Cullinan is a Python web framework built on Tornado, inspired by Spring Boot. It provides dependency injection, lifecycle management, and a clean architecture for building web applications and APIs.

### Why choose Cullinan over Flask/Django/FastAPI?

**Cullinan offers**:
- Spring Boot-style dependency injection
- Built-in lifecycle management
- High performance (Tornado-based)
- Clean separation of concerns (Controller/Service/Repository)
- WebSocket support out of the box

**Choose Cullinan if**:
- You love Spring Boot and want similar patterns in Python
- You need both HTTP and WebSocket in one framework
- You want strong architectural patterns

### Is Cullinan production-ready?

Yes! Cullinan is used in production applications. It includes:
- ✅ Complete lifecycle management
- ✅ Error handling
- ✅ Graceful shutdown
- ✅ Comprehensive testing

## Installation & Setup

### How do I install Cullinan?

```bash
pip install path/to/Cullinan
```

Or in development mode:
```bash
cd path/to/Cullinan
pip install -e .
```

### What are the minimum requirements?

- Python 3.8 or higher
- Tornado (installed automatically)

### How do I configure the server port?

Create a `.env` file:
```env
SERVER_PORT=4080
```

Or set environment variable:
```bash
export SERVER_PORT=8080
python app.py
```

## Dependency Injection

### Do I need to import Service classes?

**No!** Use string type annotations:

```python
from cullinan.core import Inject

@controller(url='/api')
class MyController:
    # No import needed!
    my_service: 'MyService' = Inject()
```

### Why is my injected service still an `Inject` object?

**Problem**: You forgot the type annotation.

```python
# ✗ Wrong - no type annotation
my_service = Inject(name='MyService')

# ✓ Correct - with type annotation
my_service: 'MyService' = Inject()
```

### Can I inject services into services?

**Yes!** Services can depend on other services:

```python
@service
class UserService(Service):
    database: 'DatabaseService' = Inject()
    email: 'EmailService' = Inject()
```

### How does circular dependency work?

Cullinan uses **lazy loading** to handle circular dependencies:

```python
@service
class ServiceA(Service):
    service_b: 'ServiceB' = Inject()  # Lazy loaded

@service
class ServiceB(Service):
    service_a: 'ServiceA' = Inject()  # Lazy loaded
```

## Lifecycle Management

### When is `on_startup()` called?

**Before the web server starts**. This ensures your services are fully initialized before accepting requests.

### My `on_startup()` is not being called. Why?

Make sure you're using the standard `application.run()` function:

```python
from cullinan import application

if __name__ == '__main__':
    application.run()  # This triggers lifecycle
```

### What's the difference between `on_post_construct()` and `on_startup()`?

- **`on_post_construct()`**: Quick initialization (after dependency injection)
- **`on_startup()`**: Can take time (connect to database, login bot, etc.)

```python
@service
class BotService(Service):
    def on_post_construct(self):
        # Quick: create client object
        self._client = discord.Client()
    
    def on_startup(self):
        # Slow: login and wait for ready
        self.initialize_bot(token)
```

### How do I control startup order?

Use `get_phase()`:

```python
@service
class DatabaseService(Service):
    def get_phase(self) -> int:
        return -100  # Starts early

@service
class BotService(Service):
    def get_phase(self) -> int:
        return -50  # Starts after database

@service
class UserService(Service):
    # Default phase = 0, starts last
    pass
```

**Lower phase number = starts earlier**

## Controllers

### How do I capture path parameters?

Use regex groups:

```python
@get_api(url='/users/([0-9]+)')
def get_user(self, user_id):
    # user_id will be the captured number
    pass

@get_api(url='/posts/([a-z]+)/comments/([0-9]+)')
def get_comment(self, post_slug, comment_id):
    # Multiple parameters
    pass
```

### How do I get query parameters?

```python
@get_api(url='/users')
def list_users(self, query_params):
    page = query_params.get('page', 1)
    limit = query_params.get('limit', 10)
    return {'users': [...]}
```

Call: `GET /users?page=2&limit=20`

### How do I get request body?

```python
@post_api(url='/users')
def create_user(self, body_params):
    name = body_params.get('name')
    email = body_params.get('email')
    return {'created': True}
```

### How do I get headers?

```python
@get_api(url='/protected', headers=['Authorization'])
def protected_route(self, query_params, headers):
    token = headers.get('Authorization')
    # Verify token...
```

### Can I return different status codes?

```python
from cullinan.controller import get_api

@get_api(url='/users/([0-9]+)')
def get_user(self, user_id):
    user = self.user_service.get(user_id)
    
    if not user:
        self.set_status(404)
        return {'error': 'User not found'}
    
    return {'user': user}
```

## Services

### What's the difference between Service and Controller?

- **Controller**: Handles HTTP requests, validates input, returns responses
- **Service**: Contains business logic, independent of HTTP

```python
# Controller - HTTP concerns
@controller(url='/api/users')
class UserController:
    user_service: 'UserService' = Inject()
    
    @post_api(url='')
    def create(self, body_params):
        # Validate HTTP input
        if not body_params.get('email'):
            return {'error': 'Email required'}
        
        # Call service
        user = self.user_service.create(body_params)
        return {'user': user}

# Service - Business logic
@service
class UserService(Service):
    def create(self, data):
        # Business rules
        # Database operations
        return user
```

### Do I always need to inherit from `Service`?

**Yes**, if you want lifecycle hooks and automatic registration:

```python
@service
class MyService(Service):  # ← Inherit from Service
    def on_startup(self):
        # Lifecycle hook
        pass
```

## WebSocket

### How do I create a WebSocket handler?

```python
from cullinan.websocket_registry import websocket_handler

@websocket_handler(url='/ws/chat')
class ChatWebSocket:
    def on_open(self):
        print("Client connected")
    
    def on_message(self, message):
        self.write_message(f"Echo: {message}")
    
    def on_close(self):
        print("Client disconnected")
```

### Can I use dependency injection in WebSocket?

**Yes!**

```python
@websocket_handler(url='/ws/notifications')
class NotificationWebSocket:
    user_service: 'UserService' = Inject()
    
    def on_open(self):
        users = self.user_service.get_all()
        self.write_message({'users': users})
```

## Errors & Debugging

### I get "Service not found" error

**Solution**: Make sure the Service is registered:

```python
# Import the service so @service decorator runs
from services.my_service import MyService

# Or import in __init__.py
```

### My changes aren't taking effect

**Solution**: Restart the server. Cullinan doesn't have auto-reload in production mode.

For development, you can use:
```bash
# Use watchdog or similar for auto-reload
watchmedo auto-restart -p "*.py" -- python app.py
```

### How do I enable debug logging?

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Performance

### Is Cullinan fast?

Yes! Built on Tornado's async I/O:
- Handles thousands of concurrent connections
- Non-blocking I/O
- Efficient WebSocket support

### Should I use async/await?

Use async when you have I/O operations:

```python
@service
class DatabaseService(Service):
    async def on_startup_async(self):
        # Async I/O
        await self.connect()
    
    async def query(self, sql):
        # Async query
        return await self.execute(sql)
```

Use sync for CPU-bound or simple operations:

```python
@service
class UserService(Service):
    def validate_email(self, email):
        # Simple validation - sync is fine
        return '@' in email
```

## Deployment

### How do I run in production?

```bash
# Set production environment
export SERVER_PORT=80
export SERVER_THREAD=4  # Use multiple workers

# Run
python app.py
```

### Can I use Gunicorn/uWSGI?

Cullinan uses Tornado's built-in server which is production-ready. Just set `SERVER_THREAD` for multiple workers.

### How do I handle HTTPS?

Use a reverse proxy (nginx/Caddy) in front of Cullinan:

```nginx
server {
    listen 443 ssl;
    
    location / {
        proxy_pass http://localhost:4080;
    }
}
```

## Still Have Questions?

- 📖 Check the [complete documentation](./INDEX.md)
- 💡 Browse [examples](../examples/)
- 💬 Open an issue on GitHub
- 📧 Contact maintainers

---

**Updated**: 2025-11-11

