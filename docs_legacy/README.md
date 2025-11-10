# Cullinan Framework Documentation

**[English](README.md)** | [中文](zh/README_zh.md)

Welcome to Cullinan! The complete documentation for building production-ready web applications with Python.

---

## 📌 Version Information

**Current Version: v0.7.0-alpha1**

This documentation covers the new architecture introduced in v0.7.0 with enhanced services, WebSocket support, and unified registry pattern.

**Looking for v0.6.x documentation?** See the [v0.6.x Legacy Docs](#v06x-legacy-documentation) section below.

---

## 🆕 What's New in v0.7.0

- **Core Module**: Unified registry pattern, dependency injection, lifecycle management
- **Enhanced Services**: Service layer with DI and lifecycle hooks (`on_init`, `on_destroy`)
- **WebSocket Integration**: Full WebSocket support with registry pattern
- **Request Context**: Thread-safe request-scoped data management
- **Testing Utilities**: Mock services and test registries
- **Better Architecture**: Modular design with clear separation of concerns

**Migration Guide**: See [CHANGELOG.md](../CHANGELOG.md) for upgrading from v0.6.x

---

## 📖 Documentation Index

### Quick Start (v0.7.0)

- **[v0.7.0 Feature Demo](../examples/v070_demo.py)** ⭐ **New example showing all features!**
  Comprehensive demonstration of:
  - Service layer with dependency injection
  - Lifecycle hooks
  - WebSocket handlers
  - Request context management

### Core Documentation

0. [**Complete Guide**](00-complete-guide.md) 🌟
   A complete guide to the framework, from basics to advanced topics.
   - Installation & Setup
   - Quick Start Tutorial → [Example](../examples/basic/hello_world.py)
   - Controllers & Services → [Example](../examples/basic/crud_example.py)
   - Database, WebSockets, Hooks
   - API Reference & FAQ
   - **Note**: Being updated for v0.7.0 features

1. [**Configuration Guide**](01-configuration.md)
   A complete guide to Cullinan's configuration system.
   - Basic Configuration → [Example](../examples/config_example.py)
   - JSON Configuration → [Example](../examples/cullinan.json)
   - Environment Variables
   - Packaging Configuration

2. [**Packaging Guide**](02-packaging.md)
   A guide to packaging and deploying your application.
   - Nuitka and PyInstaller Support
   - Cross-Platform Builds → [Scripts](../scripts/)
   - Different Packaging Modes
   - Platform-Specific Instructions

3. [**Troubleshooting**](03-troubleshooting.md)
   Common issues and their solutions.
   - Module Not Found Errors
   - Controller/Service Registration
   - Packaging Problems
   - Debugging Tips → [Diagnostic Tool](../examples/diagnose_app.py)

4. [**Quick Reference**](04-quick-reference.md)
   A quick reference card for common tasks.
   - Configuration Syntax
   - Packaging Commands
   - Common Patterns

5. [**Build Scripts**](05-build-scripts.md)
   A complete guide to the build scripts.
   - Universal Builder → [build_app.py](../scripts/build_app.py)
   - Advanced Nuitka → [build_nuitka_advanced.py](../scripts/build_nuitka_advanced.py)
   - Advanced PyInstaller → [build_pyinstaller_advanced.py](../scripts/build_pyinstaller_advanced.py)
   - Cross-Platform Support
   - Compiler Options

6. [**sys.path Auto-Handling**](06-sys-path-auto-handling.md)
   Automatic detection of the project root directory.
   - No more manual `sys.path.append`
   - Simplified startup code
   - Explanation of the auto-detection logic
   - Migration guide from the old method

7. [**Registry Center**](07-registry-center.md)
   Centralized handler and header registry system.
   - HandlerRegistry and HeaderRegistry APIs
   - Migration from global lists
   - Testing best practices
   - Performance improvements

8. [**Service Layer Architecture Analysis**](08-service-layer-analysis.md) 📊
   Professional analysis of service layer patterns and dependency injection.
   - Service layer value proposition and responsibilities
   - Spring IoC vs lightweight approaches comparison
   - Service registry necessity analysis with decision matrices
   - Monitoring and tracking strategies
   - Architectural recommendations and best practices

### New in v0.7.0 🆕

- **[Architecture Master Document](../next_docs/ARCHITECTURE_MASTER.md)** 📖
  Consolidated analysis, design decisions, and implementation details for v0.7.0
  - Service layer analysis
  - Registry pattern evaluation
  - Core module design
  - Migration guide
  - Future roadmap

---

## 🚀 Quick Start (v0.7.0)

### 1. Installation

```bash
pip install cullinan
```

### 2. Create Your First Application with Services

```python
# app.py
from cullinan import configure, application, service, Service
from cullinan.controller import controller, get_api, post_api

configure(user_packages=['__main__'])

# Define a service
@service
class GreetingService(Service):
    def on_init(self):
        print("GreetingService initialized")
    
    def greet(self, name):
        return f"Hello, {name}!"

# Use service in controller
@controller(url='/api')
class HelloController:
    @get_api(url='/hello')
    def hello(self, query_params):
        name = query_params.get('name', 'World')
        greeting = self.service['GreetingService'].greet(name)
        return {'message': greeting}

if __name__ == '__main__':
    application.run()
```

**📝 Full Example:** [`examples/v070_demo.py`](../examples/v070_demo.py) - Shows all v0.7.0 features!

### 3. Run and Test

```bash
python app.py
# Visit: http://localhost:8080/api/hello?name=Cullinan
```

---

## 💡 Examples Directory

All examples are located in the [`examples/`](../examples/) directory:

### v0.7.0 Examples (New!)
- [`v070_demo.py`](../examples/v070_demo.py) - **Comprehensive v0.7.0 feature demo** ⭐
  - Service layer with dependency injection
  - Lifecycle hooks
  - WebSocket integration
  - Request context
  - Real-time notifications

### Basic Examples
- [`hello_world.py`](../examples/basic/hello_world.py) - The simplest application
- [`crud_example.py`](../examples/basic/crud_example.py) - A complete CRUD API
- [`test_controller.py`](../examples/test_controller.py) - Controller patterns

### Architecture Examples
- [`new_architecture_demo.py`](../examples/new_architecture_demo.py) - Architecture features
- [`service_examples.py`](../examples/service_examples.py) - Service patterns

### Configuration Examples
- [`config_example.py`](../examples/config_example.py) - Code-based configuration
- [`cullinan.json`](../examples/cullinan.json) - JSON-based configuration

### Packaging Examples
- [`packaging_test.py`](../examples/packaging_test.py) - Packaging test
- [`diagnose_app.py`](../examples/diagnose_app.py) - Diagnostic tool

---

## 🔗 Quick Links by Task

### I want to...

**Get Started Quickly with v0.7.0**
→ [v0.7.0 Demo](../examples/v070_demo.py) → [Architecture Master](../next_docs/ARCHITECTURE_MASTER.md)

**Learn About New Features**
→ [CHANGELOG v0.7.0](../CHANGELOG.md#070-alpha1---2025-11-10) → [Migration Guide](../CHANGELOG.md#migration-guide)

**Build a REST API with Services**
→ [v0.7.0 Demo](../examples/v070_demo.py) → [CRUD Example](../examples/basic/crud_example.py)

**Use Dependency Injection**
→ [v0.7.0 Demo: Service Layer](../examples/v070_demo.py) → [Architecture Doc](../next_docs/ARCHITECTURE_MASTER.md#service-layer-analysis)

**Add WebSocket Support**
→ [v0.7.0 Demo: WebSocket](../examples/v070_demo.py) → [WebSocket Registry](../cullinan/websocket_registry.py)

**Configure My Application**
→ [Configuration Guide](01-configuration.md) → [Configuration Examples](../examples/config_example.py)

**Package and Deploy**
→ [Packaging Guide](02-packaging.md) → [Build Scripts](05-build-scripts.md)

**Fix Packaging Issues**
→ [Troubleshooting](03-troubleshooting.md) → [Diagnostic Tool](../examples/diagnose_app.py)

**Use the Build Scripts**
→ [Build Scripts Guide](05-build-scripts.md) → [Scripts Directory](../scripts/)

---

## v0.6.x Legacy Documentation

Documentation for the older v0.6.x architecture (deprecated):

> **⚠️ Note**: v0.6.x documentation applies only to versions prior to v0.7.0. The architecture has changed significantly in v0.7.0.

### Key Differences from v0.6.x

| Feature | v0.6.x | v0.7.0 |
|---------|--------|--------|
| Service Layer | Simple `@service` | Enhanced with DI + lifecycle |
| WebSocket | Basic decorator | Registry integration |
| Context | None | Request context management |
| Registry | Handler only | Unified across all components |
| Dependencies | Manual | Automatic injection |
| Lifecycle | None | `on_init` / `on_destroy` hooks |

For detailed migration instructions, see [CHANGELOG.md](../CHANGELOG.md#migration-guide).

---

## 🧪 Testing

Run the test suite:

```bash
# Basic tests
python run_tests.py

# Generate coverage report
python run_tests.py --coverage

# Verbose output
python run_tests.py --verbose

# Check dependencies
python run_tests.py --check-deps
```

---

## 📦 File Structure

```
docs/
├── README.md                    # This file - Documentation index
├── 00-complete-guide.md         # Complete framework guide
├── 01-configuration.md          # Configuration system
├── 02-packaging.md              # Packaging and deployment
├── 03-troubleshooting.md        # Common issues and solutions
├── 04-quick-reference.md        # Quick command reference
├── 05-build-scripts.md          # Build scripts guide
├── 06-sys-path-auto-handling.md # sys.path auto-handling
├── 07-registry-center.md        # Registry pattern
├── 08-service-layer-analysis.md # Service layer analysis
└── zh/                          # Chinese documentation

next_docs/
└── ARCHITECTURE_MASTER.md       # 🆕 v0.7.0 architecture document

examples/
├── v070_demo.py                 # 🆕 v0.7.0 comprehensive demo
├── basic/
│   ├── hello_world.py
│   └── crud_example.py
├── config_example.py            # Configuration examples
├── cullinan.json                # JSON configuration
├── packaging_test.py            # Packaging test
└── diagnose_app.py              # Diagnostic tool

scripts/
├── build_app.py                # Universal builder
├── build_nuitka_advanced.py    # Advanced Nuitka
└── build_pyinstaller_advanced.py # Advanced PyInstaller
```

---

## 🆘 Getting Help

- **GitHub Issues**: [Report a bug](https://github.com/plumeink/Cullinan/issues)
- **Discussions**: [Ask a question](https://github.com/plumeink/Cullinan/discussions)
- **Documentation**: [Read the docs](00-complete-guide.md)
- **Examples**: [Browse examples](../examples/)
- **Architecture**: [v0.7.0 Design](../next_docs/ARCHITECTURE_MASTER.md)

---

## 📄 License

Cullinan is open-source software licensed under the MIT License.

See [LICENSE](../LICENSE) for details.

---

**Happy coding with Cullinan v0.7.0! 🎉**

