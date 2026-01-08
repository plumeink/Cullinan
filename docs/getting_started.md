title: "Getting Started with Cullinan"
slug: "getting-started"
module: ["cullinan.application"]
tags: ["getting-started", "tutorial"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/getting_started.md"
related_tests: ["tests/test_real_app_startup.py"]
related_examples: ["examples/hello_http.py"]
estimate_pd: 2.0
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# Getting Started with Cullinan

This page provides a minimal quick-start to install and run a small Cullinan application.

## Prerequisites
- Python 3.8+
- Git

## Install

Before you start, make sure Python 3.8+ is installed and that `python` and `pip` are available on your PATH.

On most systems, you can upgrade pip and install Cullinan with the following commands (valid on Windows, Linux, and macOS):

```bash
python -m pip install -U pip
python -m pip install cullinan
```

## Quick start
1. Create a new project directory and change into it:

On all platforms:

```bash
mkdir my_cullinan_project
cd my_cullinan_project
```

2. Ensure you have a Python environment (virtualenv, conda, system Python, etc.). Install the published package:

```bash
python -m pip install -U pip
python -m pip install cullinan
```

3. Create a minimal application file `minimal_app.py` in your project with the following content:

```python
# minimal_app.py
from cullinan.application import run
from cullinan.controller import controller, get_api

@controller(url='/hello')
class HelloController:
    """Simple HTTP controller."""
    
    @get_api(url='')
    def hello(self):
        return {'message': 'Hello from Cullinan!'}

if __name__ == '__main__':
    run()
```

4. Run your app:

On Windows (PowerShell):

```powershell
python minimal_app.py
```

On Linux / macOS:

```bash
python minimal_app.py
```

Then open `http://localhost:4080/hello` in your browser to verify the server is running.

## Sample run output

The following log output illustrates a successful run of the example in a local environment (Windows PowerShell session). Timestamps and durations will vary between environments:

```
|||||||||||||||||||||||||||||||||||||||||||||||||
|||                                           |||
|||    _____      _ _ _                       |||
|||   / ____|    | | (_)                      |||
|||  | |    _   _| | |_ _ __   __ _ _ __      |||
|||  | |   | | | | | | | '_ \ / _` | '_ \     |||
|||  | |___| |_| | | | | | | | (_| | | | |    |||
|||   \_____\__,_|_|_|_|_| |_|\__,_|_| |_|    |||
|||                                           |||
|||||||||||||||||||||||||||||||||||||||||||||||||
	|||

2025-11-19 04:18:50,209 INFO cullinan.application: loading env...
2025-11-19 04:18:50,210 INFO cullinan.application: └---configuring dependency injection...
2025-11-19 04:18:50,210 INFO cullinan.application: └---dependency injection configured
2025-11-19 04:18:50,210 INFO cullinan.application: └---scanning services...
2025-11-19 04:18:50,210 INFO cullinan.application: ...
2025-11-19 04:18:50,223 INFO cullinan.application: └---found 31 modules to scan
2025-11-19 04:18:50,228 INFO cullinan.application: └---scanning controllers...
2025-11-19 04:18:50,260 INFO cullinan.application: └---found 31 modules to scan
2025-11-19 04:18:50,261 INFO cullinan.application: └---initializing services...
2025-11-19 04:18:50,261 INFO cullinan.application: └---no services registered
2025-11-19 04:18:50,261 INFO cullinan.application: └---loading controller finish

2025-11-19 04:18:50,261 INFO cullinan.application: loading env finish

2025-11-19 04:18:50,262 INFO cullinan.application: server is starting
2025-11-19 04:18:50,262 INFO cullinan.application: port is 4080
```

At this point, the server is running and listening on `http://localhost:4080`. Use Ctrl+C to gracefully stop the server.

## Minimal application example

Here's a minimal Cullinan application that demonstrates the core framework features:

```python
# minimal_app.py
from cullinan.application import run
from cullinan.controller import controller, get_api

@controller(url='/hello')
class HelloController:
    """Simple HTTP controller."""
    
    @get_api(url='')
    def hello(self):
        return {'message': 'Hello from Cullinan!'}

if __name__ == '__main__':
    run()
```

To run this example:

```powershell
# Save the above code as minimal_app.py
python minimal_app.py
```

Then visit `http://localhost:4080/hello` in your browser.

## Understanding the basics

### Application lifecycle
1. **Creation**: `create_app()` initializes the application with default settings
2. **Registration**: Controllers and services are discovered via module scanning or explicit registration
3. **Startup**: `app.run()` starts the Tornado IOLoop and begins accepting requests
4. **Shutdown**: Graceful shutdown on SIGINT/SIGTERM

### Dependency Injection
Cullinan provides built-in IoC/DI support. 

#### Decorators Explained: `@injectable` vs `@controller()`

**`@injectable`** - General-purpose dependency injection decorator
- Applicable to any class that needs dependency injection (Service, Repository, utility classes, etc.)
- Must be manually applied, does not auto-register to any registry
- Automatically injects marked dependencies after class instantiation
- Use cases: Service layer, Repository layer, utility classes, etc.

**`@controller()`** - Controller-specific auto-registration decorator
- Specifically for HTTP Controller classes
- **Automatically applies `@injectable`**, no need to add manually
- Auto-registers Controller and its routes to ControllerRegistry
- Auto-scans methods decorated with `@get_api`, `@post_api`, etc.
- Use cases: HTTP Controllers only

```python
from cullinan.controller import controller, get_api
from cullinan.service import Service, service
from cullinan.core import injectable, InjectByName
from cullinan.params import Path

# Service uses @service (inherits from Service base class)
@service
class UserService(Service):
    def get_user(self, user_id):
        return {'id': user_id, 'name': 'John'}

# Repository uses @injectable
@injectable
class UserRepository:
    def find_by_id(self, user_id):
        return {'id': user_id}

# Controller uses @controller() - automatically includes @injectable
@controller(url='/api/users')
class UserController:
    # Dependency injection in Controller
    user_service = InjectByName('UserService')
    
    @get_api(url='/{user_id}')
    async def get_user(self, user_id: Path(int)):
        return self.user_service.get_user(user_id)
```
    
**Important:** Do **not** use `@injectable` on Controllers, as `@controller()` already includes it automatically.

---

#### RESTful API decorators (quick overview)

Cullinan provides a set of REST-style decorators that bind controller methods to HTTP routes:

- `get_api`
- `post_api`
- `patch_api`
- `delete_api`
- `put_api`

Key points:

- These decorators **only accept keyword arguments** (they are defined as `def get_api(**kwargs)` etc.).
  - `@get_api('/user')` is **invalid** and will raise a `TypeError` at import time.
  - Always use the keyword form: `@get_api(url='/user')`.
- The `url` argument uses a lightweight template syntax with `{param}` placeholders.

**v0.90+ Recommended: Type-Safe Parameter System**

```python
from cullinan.params import Path, Query, Body, DynamicBody

@controller(url='/api/users')
class UserController:
    # Type-safe path and query parameters
    @get_api(url='/{id}')
    async def get_user(self, id: Path(int), include_posts: Query(bool, default=False)):
        return {"id": id, "include_posts": include_posts}
    
    # Query parameters with validation
    @get_api(url='/')
    async def list_users(
        self,
        page: Query(int, default=1, ge=1),
        size: Query(int, default=10, ge=1, le=100),
    ):
        return {"page": page, "size": size}
    
    # Type-safe body parameters with validation
    @post_api(url='/')
    async def create_user(
        self,
        name: Body(str, required=True),
        age: Body(int, default=0, ge=0, le=150),
    ):
        return {"name": name, "age": age}
    
    # DynamicBody for flexible access
    @post_api(url='/dynamic')
    async def create_dynamic(self, body: DynamicBody):
        return {"name": body.name, "age": body.get('age', 0)}
```

See [Parameter System Guide](parameter_system_guide.md) for full details, including:
- File uploads with `FileInfo`/`FileList`
- Dataclass validation with `@field_validator`
- Pydantic integration (optional, install with `pip install pydantic`)
- Custom model handlers

<details>
<summary><strong>Legacy Style (still supported)</strong></summary>

The traditional parameter style is still supported for backward compatibility:

Common options:
- `url`: Route pattern (string). Supports `{param}` placeholders, e.g. `'/users/{user_id}'`.
- `query_params`: Iterable of query parameter names, e.g. `('page', 'size')`.
- `body_params` (POST/PATCH only): Iterable of body field names for JSON/form parsing.
- `file_params`: Iterable of file field names for file uploads.
- `headers`: Iterable of required HTTP header names.
- `get_request_body` (POST/PATCH only): If `True`, passes the raw request body to your method.

```python
@controller(url='/api/users')
class UserController:
    @get_api(url='/{user_id}')
    def get_user(self, url_params):
        user_id = url_params.get('user_id') if url_params else None
        return {"id": user_id}

    @get_api(url='/', query_params=('page', 'size'))
    def list_users(self, query_params):
        page = query_params.get('page') if query_params else None
        size = query_params.get('size') if query_params else None
        return {"page": page, "size": size}

    @post_api(url='/', body_params=('name', 'email'))
    def create_user(self, body_params):
        name = body_params.get('name') if body_params else None
        email = body_params.get('email') if body_params else None
        return {"name": name, "email": email}
```

</details>

For a deeper dive into URL patterns and all decorator options, see `docs/wiki/restful_api.md`.

---

#### Recommended Dependency Injection Approaches

**Approach 1: InjectByName (Recommended, Simplest)**

Inject by name without importing dependencies, avoiding circular import issues:

```python
from cullinan.service import Service, service
from cullinan.core import injectable, InjectByName

@service
class DatabaseService(Service):
    def query(self, sql):
        return f"Results for: {sql}"

@injectable
class UserRepository:
    # Recommended: InjectByName doesn't need type annotation, just use string name
    db = InjectByName('DatabaseService')
    
    def get_users(self):
        return self.db.query("SELECT * FROM users")
```

**Approach 2: Inject + TYPE_CHECKING (IDE autocomplete support)**

If you need IDE autocomplete and type checking, use `Inject` with TYPE_CHECKING:

```python
from typing import TYPE_CHECKING
from cullinan.core import injectable, Inject
from cullinan.service import Service, service

# TYPE_CHECKING imports are not executed at runtime, avoiding circular imports
if TYPE_CHECKING:
    from cullinan.service import DatabaseService

@service
class DatabaseService(Service):
    def query(self, sql):
        return f"Results for: {sql}"

@injectable
class UserRepository:
    # With TYPE_CHECKING import, you get IDE autocomplete support
    db: 'DatabaseService' = Inject()
    
    def get_users(self):
        # IDE can suggest db.query method
        return self.db.query("SELECT * FROM users")
```

**Approach 3: Inject + Pure String Annotation (No IDE autocomplete)**

If you don't need IDE autocomplete, use string annotations directly:

```python
from cullinan.core import injectable, Inject

@injectable
class UserRepository:
    # Pure string annotation, no import needed, but no IDE autocomplete
    db: 'DatabaseService' = Inject()
    
    def get_users(self):
        return self.db.query("SELECT * FROM users")
```

**Summary:**
- **InjectByName**: Recommended for most cases, simple and straightforward, no type annotation needed
- **Inject + TYPE_CHECKING**: Best for development experience, provides IDE autocomplete
- **Inject + String annotation**: Simplest but no IDE support

For detailed information on injection patterns, see `docs/wiki/injection.md`.

## Common patterns

### Adding middleware
```python
from cullinan.middleware import MiddlewareBase

class LoggingMiddleware(MiddlewareBase):
    def process_request(self, request):
        print(f"Request: {request.method} {request.path}")

# Register during app initialization
app.add_middleware(LoggingMiddleware())
```

### Configuration
```python
from cullinan.config import Config

config = Config()
config.set('database.url', 'postgresql://localhost/mydb')
config.set('server.port', 8080)
```

## Troubleshooting
- If you encounter errors installing packages, ensure your Python and pip are up to date and that you have network access to PyPI.

## Next steps
- Read `docs/wiki/injection.md` for IoC/DI details.
- Explore `examples/` for runnable samples.

## Additional resources

- **Architecture**: See `docs/architecture.md` for system design overview
- **Components**: Read `docs/wiki/components.md` for component responsibilities
- **Lifecycle**: Learn about application lifecycle in `docs/wiki/lifecycle.md`
- **Middleware**: Understand middleware in `docs/wiki/middleware.md`
- **API Reference**: Browse `docs/api_reference.md` for complete API documentation
- **Examples**: Explore `examples/` directory for more samples

## Community and support

- **Issues**: Report bugs at [GitHub Issues](https://github.com/your-org/cullinan/issues)
- **Contributing**: See `docs/contributing.md` for contribution guidelines
- **Testing**: Read `docs/testing.md` for testing best practices
