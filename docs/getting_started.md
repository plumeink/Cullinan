title: "Getting Started with Cullinan"
slug: "getting-started"
module: ["cullinan.application"]
tags: ["getting-started", "tutorial"]
author: "Plumeink"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/getting_started.md"
related_tests: ["tests/test_real_app_startup.py"]
related_examples: ["examples/hello_http.py"]
estimate_pd: 2.0
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# Getting Started with Cullinan

This page provides a minimal quick-start to install and run a small Cullinan application.

## Prerequisites
- Python 3.8+
- Git

## Install (PowerShell)

python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1; pip install -U pip; pip install -e .

## Quick start
1. Ensure you are in the repository root.
2. Activate the virtualenv (see above command).
3. Run the example server:

python examples\\hello_http.py

Expected: Server starts and listens on the configured port. Open http://localhost:8888 to see a response.

## Verified example (local run)

I ran the example locally in a Windows PowerShell session using the above commands. Observed log output (truncated):

INFO:__main__:Starting IOLoop... (will stop after one verification request)
INFO:__main__:Async Requesting http://127.0.0.1:8888/hello
INFO:tornado.access:200 GET /hello (127.0.0.1) 0.50ms
INFO:__main__:Response status: 200
INFO:__main__:Response body: Hello Cullinan
INFO:__main__:IOLoop stopped, exiting

Note: The example uses `cullinan.handler.registry.get_handler_registry()` to register a simple Tornado handler and performs a single verification request, then exits. This makes it suitable for smoke-testing in documentation.

## Minimal application example

Here's a minimal Cullinan application that demonstrates the core framework features:

```python
# minimal_app.py
from cullinan.app import create_app
from cullinan.controller import controller

@controller(path='/hello')
def hello_handler(request):
    """Simple HTTP handler."""
    return {'message': 'Hello from Cullinan!'}

if __name__ == '__main__':
    app = create_app()
    # Controllers are auto-discovered or explicitly registered
    app.run()  # Starts Tornado IOLoop on default port
```

To run this example:

```powershell
# Save the above code as minimal_app.py
.\\.venv\\Scripts\\Activate.ps1
python minimal_app.py
```

Then visit `http://localhost:8888/hello` in your browser.

## Understanding the basics

### Application lifecycle
1. **Creation**: `create_app()` initializes the application with default settings
2. **Registration**: Controllers and services are discovered via module scanning or explicit registration
3. **Startup**: `app.run()` starts the Tornado IOLoop and begins accepting requests
4. **Shutdown**: Graceful shutdown on SIGINT/SIGTERM

### Dependency Injection
Cullinan provides built-in IoC/DI support. Example with service injection:

```python
from cullinan.service import Service, service
from cullinan.core import injectable, Inject

@service
class DatabaseService(Service):
    def query(self, sql):
        return f"Results for: {sql}"

@injectable
class UserController:
    db: DatabaseService = Inject()
    
    def get_users(self):
        return self.db.query("SELECT * FROM users")
```

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
- If `Activate.ps1` fails, ensure PowerShell execution policy allows script execution: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

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
