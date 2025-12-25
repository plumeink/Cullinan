# Cullinan Extension Development Guide

> **Version**: v0.81+  
> **Author**: Plumeink  
> **Last Updated**: 2025-12-16

---

## Table of Contents

1. [Overview](#overview)
2. [Extension Categories](#extension-categories)
3. [Middleware Extensions](#middleware-extensions)
4. [Dependency Injection Extensions](#dependency-injection-extensions)
5. [Lifecycle Extensions](#lifecycle-extensions)
6. [Routing Extensions](#routing-extensions)
7. [Best Practices](#best-practices)
8. [FAQ](#faq)

---

## Overview

The Cullinan framework provides rich extension points, allowing developers to customize functionality without modifying the framework code. This guide introduces how to develop various types of extensions.

### Extension Philosophy

- **Non-invasive**: Extend through decorators, interface implementations, etc.
- **Unified Pattern**: All extensions use consistent registration methods
- **Discoverability**: Extension points are queryable via API
- **Backward Compatible**: Maintain compatibility without breaking existing functionality

### Query Available Extension Points

```python
from cullinan.extensions import list_extension_points

# Query all extension points
all_points = list_extension_points()
for point in all_points:
    print(f"{point['category']}: {point['name']}")
    print(f"  {point['description']}")

# Query specific category
middleware_points = list_extension_points(category='middleware')
```

---

## Extension Categories

Cullinan provides 6 major categories of extension points:

| Category | Description | Typical Use Cases |
|----------|-------------|-------------------|
| **Middleware** | Request/Response interception | Authentication, Logging, CORS |
| **Lifecycle** | Lifecycle hooks | Initialization, Startup, Shutdown |
| **Injection** | Dependency Injection | Custom Scope, Provider |
| **Routing** | Route handling | Custom Handler |
| **Configuration** | Configuration management | Config source, Environment adaptation |
| **Handler** | Request handler | Custom request processing logic |

---

## Middleware Extensions

### Basic Concepts

Middleware are interceptors in the request processing pipeline that can:
- Preprocess requests before they reach the Handler
- Post-process responses before they are returned to the client
- Short-circuit requests (e.g., return 401 on authentication failure)

### Creating Middleware

#### Method 1: Decorator Registration (Recommended)

```python
from cullinan.middleware import middleware, Middleware

@middleware(priority=100)
class LoggingMiddleware(Middleware):
    """Logging Middleware"""
    
    def process_request(self, handler):
        # Request preprocessing
        print(f"Request: {handler.request.uri}")
        return handler  # Return handler to continue processing
    
    def process_response(self, handler, response):
        # Response post-processing
        print(f"Response: {response}")
        return response
```

#### Method 2: Manual Registration

```python
from cullinan.middleware import Middleware, get_middleware_registry

class MyMiddleware(Middleware):
    def process_request(self, handler):
        return handler

# Manual registration
registry = get_middleware_registry()
registry.register(MyMiddleware, priority=100)
```

### Priority Rules

- **Lower numbers execute first**
- Recommended ranges:
  - `0-50`: Critical middleware (CORS, security)
  - `51-100`: Standard middleware (logging, metrics)
  - `101-200`: Application-specific middleware

### Lifecycle Hooks

```python
@middleware(priority=100)
class DatabaseMiddleware(Middleware):
    def on_init(self):
        """Execute during initialization (application startup)"""
        self.pool = create_connection_pool()
    
    def on_destroy(self):
        """Execute during destruction (application shutdown)"""
        self.pool.close()
    
    def process_request(self, handler):
        # Get connection for each request
        handler.db = self.pool.get_connection()
        return handler
    
    def process_response(self, handler, response):
        # Return connection
        if hasattr(handler, 'db'):
            self.pool.return_connection(handler.db)
        return response
```

### Short-circuiting Requests

Returning `None` indicates short-circuit - subsequent middleware and Handler will not execute:

```python
@middleware(priority=50)
class AuthMiddleware(Middleware):
    def process_request(self, handler):
        token = handler.request.headers.get('Authorization')
        if not token:
            # Authentication failed, short-circuit
            handler.set_status(401)
            handler.finish({'error': 'Unauthorized'})
            return None  # Stop processing
        
        # Authentication successful, continue
        handler.current_user = validate_token(token)
        return handler
```

### Complete Example

Reference: `examples/custom_auth_middleware.py`

---

## Dependency Injection Extensions

### Custom Scope

Scope defines the lifecycle of dependencies (singleton, request-level, session-level, etc.).

```python
from cullinan.core.scope import Scope
from typing import Any, Optional

class SessionScope(Scope):
    """Session-level scope"""
    
    def __init__(self):
        super().__init__('session')
        self._instances = {}  # {session_id: {key: instance}}
    
    def get(self, key: str) -> Optional[Any]:
        """Get instance"""
        session_id = self._get_current_session_id()
        if session_id and session_id in self._instances:
            return self._instances[session_id].get(key)
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set instance"""
        session_id = self._get_current_session_id()
        if session_id:
            if session_id not in self._instances:
                self._instances[session_id] = {}
            self._instances[session_id][key] = value
    
    def clear(self) -> None:
        """Clear current session"""
        session_id = self._get_current_session_id()
        if session_id and session_id in self._instances:
            del self._instances[session_id]
    
    def _get_current_session_id(self) -> Optional[str]:
        """Get session ID from request context"""
        from cullinan.core.context import get_current_context
        try:
            context = get_current_context()
            return context.get('session_id')
        except:
            return None
```

### Custom Provider

Provider is responsible for creating and managing dependency instances.

#### Factory Pattern Provider

```python
from cullinan.core.provider import Provider

class FactoryProvider(Provider):
    """Create new instance every time"""
    
    def __init__(self, factory: Callable[[], Any], name: str):
        self.factory = factory
        self.name = name
    
    def get(self, key: str) -> Optional[Any]:
        return self.factory()
    
    def set(self, key: str, value: Any) -> None:
        pass
```

#### Lazy Initialization Provider

```python
class LazyProvider(Provider):
    """Initialize only on first access"""
    
    def __init__(self, factory: Callable[[], Any], name: str):
        self.factory = factory
        self.name = name
        self._instance = None
        self._initialized = False
    
    def get(self, key: str) -> Optional[Any]:
        if not self._initialized:
            self._instance = self.factory()
            self._initialized = True
        return self._instance
    
    def set(self, key: str, value: Any) -> None:
        self._instance = value
        self._initialized = True
```

### Register Custom Provider

```python
from cullinan.service import service, Service
from cullinan.core.injection import get_injection_registry

@service
class ProviderRegistryService(Service):
    def on_init(self):
        """Register custom Providers during service initialization"""
        registry = get_injection_registry()
        
        # Register factory Provider
        factory_provider = FactoryProvider(
            factory=lambda: MyClass(),
            name='MyClassFactory'
        )
        registry.register_provider('MyClass', factory_provider)
        
        # Register lazy Provider
        lazy_provider = LazyProvider(
            factory=lambda: HeavyClass(),
            name='HeavyClassLazy'
        )
        registry.register_provider('HeavyClass', lazy_provider)
```

### Complete Example

Reference: `examples/custom_provider_demo.py`

---

## Lifecycle Extensions

### Service Lifecycle Hooks

```python
from cullinan.service import service, Service

@service
class DatabaseService(Service):
    def on_init(self):
        """Initialize resources (after Service instantiation)"""
        self.connection = connect_to_database()
        print("Database connected")
    
    def on_startup(self):
        """Execute after all Services are ready"""
        self.connection.execute("SELECT 1")  # Health check
        print("Database ready")
    
    def on_shutdown(self):
        """Execute during application shutdown"""
        self.connection.close()
        print("Database disconnected")
```

### Async Hooks

```python
@service
class AsyncService(Service):
    async def on_init(self):
        """Support async initialization"""
        self.client = await create_async_client()
    
    async def on_shutdown(self):
        """Support async cleanup"""
        await self.client.close()
```

### Hook Execution Order

1. **on_init()**: Execute immediately after Service instantiation
2. **on_startup()**: Execute after all Services are initialized
3. **on_shutdown()**: Execute during application shutdown (reverse order)

---

## Routing Extensions

### Custom Tornado Handler

```python
import tornado.web
from cullinan import configure, run

class CustomHandler(tornado.web.RequestHandler):
    """Custom request handler"""
    
    def get(self):
        self.write({"message": "Custom handler"})
    
    def post(self):
        data = self.get_json_argument()
        self.write({"received": data})

# Register custom Handler
if __name__ == '__main__':
    configure(
        handlers=[
            (r'/custom', CustomHandler),
            (r'/custom/(?P<id>[0-9]+)', CustomHandler),
        ]
    )
    run()
```

### Mixed Use with Controller

```python
from cullinan.controller import controller, get_api

@controller('/api/users')
class UserController:
    @get_api('/')
    def list_users(self):
        return {"users": []}

# CustomHandler and UserController can coexist
if __name__ == '__main__':
    configure(
        handlers=[
            (r'/health', HealthCheckHandler),  # Custom
        ]
    )
    run()  # UserController will be automatically registered
```

---

## Best Practices

### 1. Middleware Design Principles

✅ **Single Responsibility**: Each middleware does one thing
```python
# Good design
@middleware(priority=50)
class AuthMiddleware(Middleware):  # Only handles authentication
    pass

@middleware(priority=60)
class RoleMiddleware(Middleware):  # Only handles permission checks
    pass
```

❌ **Avoid Mixed Responsibilities**
```python
# Bad design
@middleware(priority=50)
class AuthAndLoggingMiddleware(Middleware):  # Mixed responsibilities
    pass
```

### 2. Priority Planning

- Sort by dependencies (later middleware depends on earlier results)
- Security-related middleware has highest priority
- Logging and monitoring middleware has moderate priority

```python
@middleware(priority=10)   # CORS (executes first)
class CorsMiddleware(Middleware):
    pass

@middleware(priority=40)   # Rate limiting (before authentication)
class RateLimitMiddleware(Middleware):
    pass

@middleware(priority=50)   # Authentication
class AuthMiddleware(Middleware):
    pass

@middleware(priority=60)   # Permissions (depends on authentication result)
class RoleMiddleware(Middleware):
    pass

@middleware(priority=100)  # Logging (executes last)
class LoggingMiddleware(Middleware):
    pass
```

### 3. Dependency Injection Principles

✅ **Prefer type injection**
```python
@service
class UserService(Service):
    email_service: EmailService = Inject()  # Recommended
```

✅ **Use name-based injection for special cases**
```python
@service
class UserService(Service):
    email_service = InjectByName('EmailService')  # Avoid circular imports
```

### 4. Lifecycle Management

- **on_init()**: Initialize required resources
- **on_startup()**: Execute logic that depends on other services
- **on_shutdown()**: Always clean up resources

```python
@service
class ResourceService(Service):
    def on_init(self):
        # Initialize independent resources
        self.connection = create_connection()
    
    def on_startup(self):
        # Initialization depending on other services
        self.cache = get_cache_service()
    
    def on_shutdown(self):
        # Cleanup (must implement)
        if self.connection:
            self.connection.close()
```

### 5. Error Handling

✅ **Always provide clear error messages**
```python
@middleware(priority=50)
class AuthMiddleware(Middleware):
    def process_request(self, handler):
        try:
            token = self._extract_token(handler)
            user = self._validate_token(token)
            handler.current_user = user
            return handler
        except TokenExpiredError:
            handler.set_status(401)
            handler.finish({
                'error': 'TokenExpired',
                'message': 'Your token has expired. Please login again.'
            })
            return None
        except InvalidTokenError:
            handler.set_status(401)
            handler.finish({
                'error': 'InvalidToken',
                'message': 'Invalid authentication token.'
            })
            return None
```

### 6. Logging Standards

- Use structured logging
- **No emoji allowed**
- Log critical operations and errors

```python
import logging

logger = logging.getLogger(__name__)

@middleware(priority=100)
class LoggingMiddleware(Middleware):
    def process_request(self, handler):
        logger.info(
            "Request started",
            extra={
                'method': handler.request.method,
                'path': handler.request.path,
                'remote_ip': handler.request.remote_ip,
            }
        )
        return handler
```

---

## FAQ

### Q1: How to access dependency-injected services in middleware?

A: Middleware doesn't support automatic injection, but you can manually retrieve:

```python
@middleware(priority=100)
class ServiceAwareMiddleware(Middleware):
    def on_init(self):
        # Get service from ServiceRegistry
        from cullinan.service import get_service_registry
        registry = get_service_registry()
        self.user_service = registry.get_instance('UserService')
    
    def process_request(self, handler):
        # Use service
        user = self.user_service.get_user(123)
        return handler
```

### Q2: Can middleware modify responses?

A: Yes, modify in `process_response`:

```python
@middleware(priority=100)
class ResponseModifierMiddleware(Middleware):
    def process_response(self, handler, response):
        # Add response headers
        handler.set_header('X-Custom-Header', 'value')
        
        # Modify response body (if dict)
        if isinstance(response, dict):
            response['timestamp'] = time.time()
        
        return response
```

### Q3: How to implement conditional middleware (only apply to specific paths)?

A: Check path in middleware:

```python
@middleware(priority=50)
class ConditionalMiddleware(Middleware):
    def process_request(self, handler):
        # Only apply to /api/ paths
        if not handler.request.path.startswith('/api/'):
            return handler  # Skip
        
        # Execute middleware logic
        # ...
        return handler
```

### Q4: What is the middleware execution order?

A: Request and response order are different:

- **Request Phase**: By priority from small to large (10 → 50 → 100)
- **Response Phase**: By priority from large to small (100 → 50 → 10, reverse)

```
Client Request
  ↓
Middleware A (priority=10)  →  process_request
  ↓
Middleware B (priority=50)  →  process_request
  ↓
Middleware C (priority=100) →  process_request
  ↓
Handler Processing
  ↓
Middleware C (priority=100) →  process_response
  ↓
Middleware B (priority=50)  →  process_response
  ↓
Middleware A (priority=10)  →  process_response
  ↓
Client Response
```

### Q5: How to test custom extensions?

A: Use Cullinan's testing tools:

```python
from cullinan.testing import ServiceTestCase

class TestMyMiddleware(ServiceTestCase):
    def test_process_request(self):
        middleware = MyMiddleware()
        
        # Mock handler
        class MockHandler:
            request = MockRequest()
        
        handler = MockHandler()
        result = middleware.process_request(handler)
        
        self.assertIsNotNone(result)
```

---

## Further Reading

- [Wiki Extensions](wiki/extensions.md) - Extension patterns and best practices
- [Dependency Injection Guide](dependency_injection_guide.md) - DI system documentation
- [Quick Start Extensions](quick_start_extensions.md) - Quick start guide for extensions

> **Note**: Example files can be found in the `examples/` directory of the repository:
> - `examples/custom_auth_middleware.py` - Middleware example
> - `examples/custom_provider_demo.py` - Provider example
> - `examples/extension_registration_demo.py` - Extension registration demo

---

## Get Help

- **GitHub Issues**: https://github.com/yourusername/cullinan/issues
- **Example Code**: `examples/` directory
- **API Documentation**: `docs/api_reference.md`

---

**Version**: v1.0  
**Author**: Plumeink  
**Last Updated**: 2025-12-16

