# Cullinan Framework - Documentation Index

Welcome to the Cullinan Framework documentation!

## 📚 Documentation Structure

### Getting Started
- [**Getting Started Guide**](./GETTING_STARTED.md) - Quick introduction to Cullinan
- [**Complete Tutorial**](./TUTORIAL.md) - Build a Todo API step-by-step
- [**FAQ**](./FAQ.md) - Frequently asked questions

### Core Concepts
- [**Dependency Injection**](./DEPENDENCY_INJECTION.md) - Spring-style DI system
- [**Lifecycle Management**](./LIFECYCLE_MANAGEMENT.md) - Service lifecycle hooks
- [**Controllers**](./CONTROLLERS.md) - HTTP request handling
- [**Services**](./SERVICES.md) - Business logic layer
- [**WebSocket**](./WEBSOCKET.md) - Real-time communication

### Advanced Topics
- [**Configuration**](./CONFIGURATION.md) - App configuration
- [**Middleware**](./MIDDLEWARE.md) - Request/response processing
- [**Error Handling**](./ERROR_HANDLING.md) - Exception management
- [**Testing**](./TESTING.md) - Testing your application
- [**Deployment**](./DEPLOYMENT.md) - Production deployment

### Reference
- [**API Reference**](./API_REFERENCE.md) - Complete API documentation
- [**Examples**](../examples/) - Code examples
- [**Migration Guide**](./MIGRATION_GUIDE.md) - Upgrading from older versions

## 🌏 Languages

- **English** - This directory (`docs/`)
- **中文** - Chinese version (`docs/zh/`)

## 🚀 Quick Links

### For Beginners
1. Start with [Getting Started Guide](./GETTING_STARTED.md)
2. Follow the [Complete Tutorial](./TUTORIAL.md)
3. Explore [Examples](../examples/)

### For Experienced Users
1. Check [API Reference](./API_REFERENCE.md)
2. Read [Architecture Guide](./ARCHITECTURE_MASTER.md)
3. See [Migration Guide](./MIGRATION_GUIDE.md) for upgrades

## 📖 Documentation by Feature

### Dependency Injection
- ✅ String type annotations (no imports needed)
- ✅ Automatic service discovery
- ✅ Constructor injection
- ✅ Field injection
- 📄 [Read More](./DEPENDENCY_INJECTION.md)

### Lifecycle Management
- ✅ Multiple lifecycle phases
- ✅ Phase-based startup order
- ✅ Async/sync hooks
- ✅ Graceful shutdown
- 📄 [Read More](./LIFECYCLE_MANAGEMENT.md)

### Controllers & Routing
- ✅ Decorator-based routing
- ✅ RESTful API support
- ✅ Path parameters
- ✅ Query/body parameters
- 📄 [Read More](./CONTROLLERS.md)

### WebSocket
- ✅ Easy WebSocket handlers
- ✅ Dependency injection support
- ✅ Event-based API
- 📄 [Read More](./WEBSOCKET.md)

## 🎯 Common Tasks

### Create a Simple API
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

### Use Dependency Injection
```python
from cullinan.service import service, Service
from cullinan.controller import controller, get_api
from cullinan.core import Inject

@service
class UserService(Service):
    def get_users(self):
        return ['Alice', 'Bob']

@controller(url='/api/users')
class UserController:
    user_service: 'UserService' = Inject()  # No import needed!
    
    @get_api(url='')
    def list_users(self, query_params):
        return {'users': self.user_service.get_users()}
```

### Add Lifecycle Hooks
```python
from cullinan.service import service, Service

@service
class DatabaseService(Service):
    def get_phase(self) -> int:
        return -100  # Start early
    
    def on_startup(self):
        print("Connecting to database...")
        # Initialize connection
    
    def on_shutdown(self):
        print("Closing database...")
        # Clean up
```

## 🔧 Configuration

### Environment Variables
```env
SERVER_PORT=4080
SERVER_THREAD=1
LOG_LEVEL=INFO
```

### Application Settings
```python
from cullinan import application

if __name__ == '__main__':
    application.run()  # Uses .env configuration
```

## 📝 Examples

Browse complete examples in the [`examples/`](../examples/) directory:

- `basic/` - Hello World
- `service_examples.py` - Service layer
- `core_injection_example.py` - Dependency injection
- `discord_bot_lifecycle_example.py` - Discord bot with lifecycle
- `websocket_injection_example.py` - WebSocket with DI

## 🤝 Contributing

Documentation improvements are welcome! See the root `README.md` for contribution guidelines.

## 📬 Support

- 📄 Check the [FAQ](./FAQ.md)
- 💬 Open an issue on GitHub
- 📧 Contact the maintainers

---

**Happy coding with Cullinan!** 🚀

