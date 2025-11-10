# Registry Center

**[English](07-registry-center.md)** | [中文](zh/07-registry-center.md)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [HandlerRegistry - Request Handler Registry](#handlerregistry---request-handler-registry)
- [HeaderRegistry - Header Registry](#headerregistry---header-registry)
- [Usage Guide](#usage-guide)
- [Migration Guide](#migration-guide)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## Overview

The Cullinan Registry module (`cullinan.registry`) provides a centralized, testable, and maintainable way to manage HTTP handlers and global headers.

### Why Registry Center?

In earlier versions, Cullinan used global lists (`handler_list` and `header_list`) to manage handlers and headers. This approach had several issues:

- **Difficult to test**: Global state makes test isolation challenging
- **Lack of encapsulation**: Direct manipulation of global lists throughout codebase
- **Poor extensibility**: Hard to add features like middleware, hooks, etc.
- **Poor maintainability**: Global state increases code complexity

The Registry pattern solves these problems by providing:

- ✅ **Better testability**: Create isolated registry instances for testing
- ✅ **Better encapsulation**: Manage registration logic through class interfaces
- ✅ **Better extensibility**: Easy to add metadata, hooks, middleware, etc.
- ✅ **Better maintainability**: Clear boundaries and interfaces

### Version Information

The Registry module was introduced in **v0.65** and is planned for full integration in **v0.7x**.

Current status:
- ✅ Core implementation complete
- ✅ API design stable
- ✅ Full test coverage
- 🔄 Backward compatibility layer provided
- 📋 Full integration planned for v0.7x

---

## Core Concepts

The Cullinan Registry includes two main components:

### 1. HandlerRegistry (Request Handler Registry)

Manages URL routes and their associated handler classes (Controllers). Responsible for:

- URL pattern registration
- Handler class mapping
- Route sorting (supports static and dynamic routes)
- Handler lookup and retrieval

### 2. HeaderRegistry (Header Registry)

Manages global HTTP response headers. Responsible for:

- Global header registration
- Header list maintenance
- Header application to responses

---

## HandlerRegistry - Request Handler Registry

### Basic Usage

```python
from cullinan.registry import HandlerRegistry

# Create registry instance
registry = HandlerRegistry()

# Register handlers
from myapp.controllers import UserController
registry.register('/api/users', UserController)
registry.register('/api/users/([a-zA-Z0-9-]+)', UserDetailController)

# Get all handlers
handlers = registry.get_handlers()

# Get handler count
count = registry.count()

# Sort handlers (ensures correct route matching priority)
registry.sort()

# Clear registry (mainly for testing)
registry.clear()
```

### Route Sorting

`HandlerRegistry` implements an intelligent route sorting algorithm (O(n log n) complexity) that ensures:

1. **Static routes prioritized over dynamic routes**: `/api/users/profile` before `/api/users/([a-zA-Z0-9-]+)`
2. **Longer paths prioritized**: `/api/v1/users` before `/api/users`
3. **Lexicographic order within same priority**

Example:

```python
registry = HandlerRegistry()

# Register multiple routes
registry.register('/api/users', UsersController)
registry.register('/api/users/([a-zA-Z0-9-]+)', UserDetailController)
registry.register('/api/users/profile', ProfileController)
registry.register('/api', ApiRootController)

# After sorting:
registry.sort()
# 1. /api/users/profile        (longest static route)
# 2. /api/users/([a-zA-Z0-9-]+)  (dynamic route)
# 3. /api/users                (static route)
# 4. /api                      (shortest route)
```

### Performance Characteristics

- **Registration**: O(1) - constant time
- **Sorting**: O(n log n) - logarithmic linear time (using Python's Timsort)
- **Query**: O(n) - linear time (sequential matching)
- **Memory**: O(n) - linear space

Comparison with old implementation:

| Route Count | Old (O(n³)) | New (O(n log n)) | Speedup |
|-------------|-------------|------------------|---------|
| 10          | ~1ms       | ~0.023ms         | 43x     |
| 50          | ~125ms     | ~0.20ms          | 625x    |
| 100         | ~1000ms    | ~0.94ms          | 1064x   |
| 500         | ~125s      | ~3.1ms           | 40,323x |

---

## HeaderRegistry - Header Registry

### Basic Usage

```python
from cullinan.registry import HeaderRegistry

# Create registry instance
registry = HeaderRegistry()

# Register global headers
registry.register(('Access-Control-Allow-Origin', '*'))
registry.register(('X-Frame-Options', 'DENY'))
registry.register(('X-Content-Type-Options', 'nosniff'))

# Get all headers
headers = registry.get_headers()

# Check if headers are registered
if registry.has_headers():
    print(f"Registered {registry.count()} headers")

# Clear registry
registry.clear()
```

### Common Use Cases

#### 1. CORS Configuration

```python
header_registry = HeaderRegistry()

# Configure CORS
header_registry.register(('Access-Control-Allow-Origin', '*'))
header_registry.register(('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'))
header_registry.register(('Access-Control-Allow-Headers', 'Content-Type, Authorization'))
header_registry.register(('Access-Control-Max-Age', '3600'))
```

#### 2. Security Headers

```python
header_registry = HeaderRegistry()

# Security-related headers
header_registry.register(('X-Frame-Options', 'DENY'))
header_registry.register(('X-Content-Type-Options', 'nosniff'))
header_registry.register(('X-XSS-Protection', '1; mode=block'))
header_registry.register(('Strict-Transport-Security', 'max-age=31536000; includeSubDomains'))
header_registry.register(('Content-Security-Policy', "default-src 'self'"))
```

#### 3. Custom Application Headers

```python
header_registry = HeaderRegistry()

# Application identification
header_registry.register(('X-Powered-By', 'Cullinan/0.7x'))
header_registry.register(('X-App-Version', '1.0.0'))
header_registry.register(('X-Request-ID', '${request_id}'))  # Dynamic value
```

---

## Usage Guide

### Getting Global Registries

Cullinan provides global registry instances that can be used directly:

```python
from cullinan.registry import get_handler_registry, get_header_registry

# Get global handler registry
handler_registry = get_handler_registry()
handler_registry.register('/api/users', UserController)

# Get global header registry
header_registry = get_header_registry()
header_registry.register(('X-Custom-Header', 'value'))
```

### Dependency Injection Pattern (Recommended for Testing)

For scenarios requiring isolation (like unit tests), create independent registry instances:

```python
def create_app(handler_registry=None, header_registry=None):
    """Create application instance with injectable registries"""
    if handler_registry is None:
        handler_registry = get_handler_registry()
    if header_registry is None:
        header_registry = get_header_registry()
    
    # Use injected registries
    return Application(handler_registry, header_registry)

# In tests
def test_my_app():
    # Create isolated registries
    test_handler_registry = HandlerRegistry()
    test_header_registry = HeaderRegistry()
    
    # Register test handlers
    test_handler_registry.register('/test', TestController)
    
    # Create test application
    app = create_app(test_handler_registry, test_header_registry)
    
    # Test...
    
    # Cleanup
    test_handler_registry.clear()
    test_header_registry.clear()
```

### Resetting Registries

In testing or reinitialization scenarios, you can reset global registries:

```python
from cullinan.registry import reset_registries

# Clear all global registrations
reset_registries()
```

⚠️ **Warning**: Do not use `reset_registries()` in production environments as it clears all registered handlers and headers.

---

## Migration Guide

### Migrating from Global Lists to Registry

If your code uses the old global list approach, follow these steps to migrate:

#### Old Way (v0.6x and earlier)

```python
from cullinan.controller import handler_list, header_list

# Direct manipulation of global lists
handler_list.append(('/api/users', UserController))
header_list.append(('X-Custom-Header', 'value'))

# Manual sorting
from cullinan.application import sort_url
sort_url()
```

#### New Way (v0.7x recommended)

```python
from cullinan.registry import get_handler_registry, get_header_registry

# Use registry API
handler_registry = get_handler_registry()
handler_registry.register('/api/users', UserController)

header_registry = get_header_registry()
header_registry.register(('X-Custom-Header', 'value'))

# Sorting is integrated in registry
handler_registry.sort()
```

### Backward Compatibility

Current versions (0.65-0.7x) maintain backward compatibility. Global lists `handler_list` and `header_list` are still available, but new code should use the registry pattern.

In future major versions (1.0+), global lists may be deprecated.

---

## API Reference

### HandlerRegistry Class

#### `__init__()`
Create a new handler registry instance.

```python
registry = HandlerRegistry()
```

#### `register(url: str, servlet: Any) -> None`
Register a URL pattern with its handler class.

**Parameters:**
- `url` (str): URL pattern, may contain regex like `([a-zA-Z0-9-]+)`
- `servlet` (Any): Handler class (Controller class)

**Example:**
```python
registry.register('/api/users', UserController)
registry.register('/api/users/([a-zA-Z0-9-]+)', UserDetailController)
```

#### `get_handlers() -> List[Tuple[str, Any]]`
Get all registered handlers (copy).

**Returns:**
- List[Tuple[str, Any]]: List of (url_pattern, servlet) tuples

**Example:**
```python
handlers = registry.get_handlers()
for url, servlet in handlers:
    print(f"Route: {url} -> {servlet.__name__}")
```

#### `clear() -> None`
Clear all registered handlers.

**Usage:** Mainly for testing, use with caution in production.

**Example:**
```python
registry.clear()
```

#### `count() -> int`
Get the number of registered handlers.

**Returns:**
- int: Number of registered URL patterns

**Example:**
```python
print(f"Total routes: {registry.count()}")
```

#### `sort() -> None`
Sort handlers to ensure correct route matching priority.

**Time Complexity:** O(n log n)

**Example:**
```python
registry.sort()
```

---

### HeaderRegistry Class

#### `__init__()`
Create a new header registry instance.

```python
registry = HeaderRegistry()
```

#### `register(header: Any) -> None`
Register a global header.

**Parameters:**
- `header` (Any): Header object or tuple, typically `(header_name, header_value)` tuple

**Example:**
```python
registry.register(('Content-Type', 'application/json'))
registry.register(('X-Custom-Header', 'custom-value'))
```

#### `get_headers() -> List[Any]`
Get all registered headers (copy).

**Returns:**
- List[Any]: List of header objects/tuples

**Example:**
```python
headers = registry.get_headers()
for header in headers:
    print(f"Header: {header}")
```

#### `clear() -> None`
Clear all registered headers.

**Usage:** Mainly for testing, use with caution in production.

**Example:**
```python
registry.clear()
```

#### `count() -> int`
Get the number of registered headers.

**Returns:**
- int: Number of registered headers

**Example:**
```python
print(f"Total headers: {registry.count()}")
```

#### `has_headers() -> bool`
Check if any headers are registered.

**Returns:**
- bool: True if headers exist, False otherwise

**Example:**
```python
if registry.has_headers():
    print("Headers are configured")
```

---

### Global Functions

#### `get_handler_registry() -> HandlerRegistry`
Get the global default handler registry instance.

**Returns:**
- HandlerRegistry: Global handler registry

**Example:**
```python
from cullinan.registry import get_handler_registry

registry = get_handler_registry()
```

#### `get_header_registry() -> HeaderRegistry`
Get the global default header registry instance.

**Returns:**
- HeaderRegistry: Global header registry

**Example:**
```python
from cullinan.registry import get_header_registry

registry = get_header_registry()
```

#### `reset_registries() -> None`
Reset all global registries to empty state.

**Usage:** Mainly for testing to ensure isolation between tests.

**⚠️ Warning:** Do not use in production environments.

**Example:**
```python
from cullinan.registry import reset_registries

# Reset before each test
def setup():
    reset_registries()
```

---

## Best Practices

### 1. Use Global Registries in Production

In production applications, use global registry instances:

```python
from cullinan import configure, application
from cullinan.controller import controller, get_api
from cullinan.registry import get_handler_registry, get_header_registry

# Configure
configure(user_packages=['myapp'])

# Decorators automatically register to global registry
@controller(url='/api')
class UserController:
    @get_api(url='/users')
    def list_users(self):
        return {'users': []}

# Run application
if __name__ == '__main__':
    application.run()
```

### 2. Use Independent Instances in Tests

Create independent registry instances in tests:

```python
import unittest
from cullinan.registry import HandlerRegistry, HeaderRegistry, reset_registries

class TestMyController(unittest.TestCase):
    def setUp(self):
        """Create new registries before each test"""
        self.handler_registry = HandlerRegistry()
        self.header_registry = HeaderRegistry()
    
    def tearDown(self):
        """Clean up after each test"""
        self.handler_registry.clear()
        self.header_registry.clear()
    
    def test_registration(self):
        """Test handler registration"""
        from myapp.controllers import UserController
        
        self.handler_registry.register('/api/users', UserController)
        self.assertEqual(self.handler_registry.count(), 1)
```

### 3. Register Global Headers at Initialization

Register all global headers once during application startup:

```python
from cullinan import configure
from cullinan.registry import get_header_registry

def init_app():
    # Configure framework
    configure(user_packages=['myapp'])
    
    # Register global headers
    header_registry = get_header_registry()
    
    # CORS headers
    header_registry.register(('Access-Control-Allow-Origin', '*'))
    header_registry.register(('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE'))
    
    # Security headers
    header_registry.register(('X-Frame-Options', 'DENY'))
    header_registry.register(('X-Content-Type-Options', 'nosniff'))
    
    # Application info
    header_registry.register(('X-Powered-By', 'Cullinan'))

if __name__ == '__main__':
    init_app()
    from cullinan import application
    application.run()
```

### 4. Route Sorting Best Practices

Ensure sorting after all handlers are registered:

```python
from cullinan.registry import get_handler_registry

def register_all_routes():
    registry = get_handler_registry()
    
    # Register all routes
    registry.register('/api/users', UserListController)
    registry.register('/api/users/([a-zA-Z0-9-]+)', UserDetailController)
    registry.register('/api/users/profile', UserProfileController)
    registry.register('/api/posts', PostListController)
    registry.register('/api/posts/([0-9]+)', PostDetailController)
    
    # Sort after registration (ensures correct route matching priority)
    registry.sort()
```

### 5. Avoid Duplicate Registration

Check if route is already registered to avoid duplicates:

```python
from cullinan.registry import get_handler_registry

registry = get_handler_registry()

# registry.register() internally handles duplicate checking
# Duplicate registration of the same URL will be ignored with debug log
registry.register('/api/users', UserController)
registry.register('/api/users', UserController)  # Second call will be ignored
```

### 6. Logging and Debugging

Enable debug logging to track registry operations:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Registry operations will output debug information
# DEBUG:cullinan.registry:Registered handler for URL: /api/users
# DEBUG:cullinan.registry:Sorted 5 handlers
```

---

## FAQ

### Q1: What's the difference between registry and global lists?

**A:** The main differences are encapsulation and testability:

| Feature | Global Lists | Registry |
|---------|-------------|----------|
| Encapsulation | Poor (direct list manipulation) | Good (class interface) |
| Testability | Poor (hard to isolate) | Good (independent instances) |
| Extensibility | Poor (hard to add features) | Good (easy to extend) |
| Maintainability | Poor (unclear responsibilities) | Good (clear boundaries) |

### Q2: Do I need to migrate existing code?

**A:** Not mandatory. Current versions (0.65-0.7x) maintain backward compatibility, global lists still work. However, new code should use the registry pattern for better testability and maintainability.

### Q3: Is there any performance impact?

**A:** No negative impact, actually improved:

- Registration: Same performance (O(1))
- Sorting: Faster (O(n log n) vs O(n³))
- Query: Same performance (O(n))
- Memory: Slightly increased (encapsulation overhead), negligible

### Q4: How to use in multi-threaded environments?

**A:** Registry is designed for registration during startup (single-threaded) and read-only access during runtime (thread-safe):

```python
# Startup phase (single-threaded)
def init_app():
    registry = get_handler_registry()
    registry.register('/api/users', UserController)
    registry.sort()

# Runtime (multi-threaded) - read-only access is safe
def handle_request():
    handlers = registry.get_handlers()  # Returns copy, thread-safe
    # ...
```

If you need dynamic registration at runtime (not recommended), implement your own synchronization.

### Q5: Why is sorting important?

**A:** Sorting ensures correct route matching priority:

```python
# Unsorted may cause wrong matches
handlers = [
    ('/api/users/([a-zA-Z0-9-]+)', UserDetailController),  # Dynamic route
    ('/api/users/profile', ProfileController),              # Static route
]
# Visiting /api/users/profile would match UserDetailController (wrong!)

# After sorting
handlers = [
    ('/api/users/profile', ProfileController),              # Static route first
    ('/api/users/([a-zA-Z0-9-]+)', UserDetailController),  # Dynamic route
]
# Visiting /api/users/profile correctly matches ProfileController
```

### Q6: Can I dynamically add and remove routes?

**A:** Theoretically yes, but not recommended at runtime:

- ✅ **Recommended**: Register all routes once during startup
- ⚠️ **Not Recommended**: Dynamic modification at runtime (need to consider thread safety, re-sorting, etc.)

If you really need dynamic routes, consider using middleware or plugin mechanisms (planned for future versions).

### Q7: Does registry support middleware?

**A:** Current version (0.65-0.7x) focuses on core functionality (registration and sorting). Middleware support is planned for future versions.

Design preview (planned):

```python
# Possible API in future versions
registry.register(
    '/api/users',
    UserController,
    middleware=[AuthMiddleware, LoggingMiddleware],
    metadata={'auth_required': True, 'rate_limit': 100}
)
```

### Q8: How to avoid global state pollution in tests?

**A:** Use independent registry instances or reset between tests:

```python
# Method 1: Use independent instances (recommended)
class TestMyController(unittest.TestCase):
    def setUp(self):
        self.registry = HandlerRegistry()
    
    def tearDown(self):
        self.registry.clear()

# Method 2: Reset global registries
class TestMyController(unittest.TestCase):
    def setUp(self):
        from cullinan.registry import reset_registries
        reset_registries()
```

---

## Related Resources

### Documentation Links

- [Complete Guide](00-complete-guide.md) - Framework complete guide
- [Configuration Guide](01-configuration.md) - Configuration system
- [Quick Reference](04-quick-reference.md) - Quick command reference

### Source Code

- [registry.py](../cullinan/registry.py) - Registry implementation
- [test_registry.py](../tests/test_registry.py) - Unit tests

### Design Documents

- [REGISTRY_PATTERN_DESIGN.md](../REGISTRY_PATTERN_DESIGN.md) - Registry design document
- [opt_and_refactor_cullinan.md](../opt_and_refactor_cullinan.md) - Optimization and refactoring log

---

## Change History

| Version | Date | Changes |
|---------|------|---------|
| 0.65    | 2024 | Registry module introduced |
| 0.7x    | Planned | Full registry pattern integration |
| 1.0+    | Future | Possible deprecation of global lists |

---

**Feedback and Questions?**

- **GitHub Issues**: [Report a bug](https://github.com/plumeink/Cullinan/issues)
- **Discussions**: [Ask a question](https://github.com/plumeink/Cullinan/discussions)

---

[Back to Documentation Index](README.md)
