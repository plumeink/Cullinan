# Cullinan Framework Documentation

**[English](README.md)** | [中文](zh/README_zh.md)

Welcome to Cullinan! The complete documentation for building production-ready web applications with Python.

---

## 📖 Documentation Index

### Quick Start
- **[Complete Guide](00-complete-guide.md)** ⭐ **Start here!**
  A comprehensive tutorial with examples covering all features.

### Core Documentation

0. [**Complete Guide**](00-complete-guide.md) 🌟
   A complete guide to the framework, from basics to advanced topics.
   - Installation & Setup
   - Quick Start Tutorial → [Example](../examples/basic/hello_world.py)
   - Controllers & Services → [Example](../examples/basic/crud_example.py)
   - Database, WebSockets, Hooks
   - API Reference & FAQ

1. [**Configuration Guide**](01-configuration.md)
   A complete guide to Cullinan's configuration system.
   - Basic Configuration → [Example](../examples/config/config_example.py)
   - JSON Configuration → [Example](../examples/config/cullinan.json)
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
   - Debugging Tips → [Diagnostic Tool](../examples/packaging/diagnose_app.py)

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

6. [**sys.path Auto-Handling**](06-sys-path-auto-handling.md) 🆕
   Automatic detection of the project root directory.
   - No more manual `sys.path.append`
   - Simplified startup code
   - Explanation of the auto-detection logic
   - Migration guide from the old method

7. [**Registry Center**](07-registry-center.md) 🆕
   Centralized handler and header registry system.
   - HandlerRegistry and HeaderRegistry APIs
   - Migration from global lists
   - Testing best practices
   - Performance improvements

---

## 🚀 Quick Start

### 1. Installation

```bash
pip install cullinan
```

### 2. Create Your First Application

```python
# app.py
from cullinan import configure, application
from cullinan.controller import controller, get_api

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

### 3. Run and Test

```bash
python app.py
# Visit: http://localhost:8080/api/hello
```

---

## 💡 Examples Directory

All examples are located in the [`examples/`](../examples/) directory:

### Basic Examples
- [`hello_world.py`](../examples/basic/hello_world.py) - The simplest application
- [`crud_example.py`](../examples/basic/crud_example.py) - A complete CRUD API
- [`test_controller.py`](../examples/test_controller.py) - Controller patterns

### Configuration Examples
- [`config_example.py`](../examples/config/config_example.py) - Code-based configuration
- [`cullinan.json`](../examples/config/cullinan.json) - JSON-based configuration
- [`APP_CONFIG_EXAMPLE.md`](../examples/APP_CONFIG_EXAMPLE.md) - Configuration documentation

### Packaging Examples
- [`packaging_test.py`](../examples/packaging/packaging_test.py) - Packaging test
- [`diagnose_app.py`](../examples/packaging/diagnose_app.py) - Diagnostic tool

---

## 🔗 Quick Links by Task

### I want to...

**Get Started Quickly**
→ [Complete Guide](00-complete-guide.md) → [Hello World](../examples/basic/hello_world.py)

**Configure My Application**
→ [Configuration Guide](01-configuration.md) → [Configuration Examples](../examples/config/config_example.py)

**Build a REST API**
→ [Complete Guide: Controllers](00-complete-guide.md#controllers--routing) → [CRUD Example](../examples/basic/crud_example.py)

**Package and Deploy**
→ [Packaging Guide](02-packaging.md) → [Build Scripts](05-build-scripts.md)

**Fix Packaging Issues**
→ [Troubleshooting](03-troubleshooting.md) → [Diagnostic Tool](../examples/packaging/diagnose_app.py)

**Use the Build Scripts**
→ [Build Scripts Guide](05-build-scripts.md) → [Scripts Directory](../scripts/)

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
├── README.md                    # English documentation index
├── 00-complete-guide.md         # Complete framework guide (English)
├── ... (other English documents)
└── zh/                          # Chinese documentation directory
    ├── README_zh.md             # This file - Chinese documentation index
    ├── 00-complete-guide_zh.md  # ⭐ Complete framework guide
    ├── 01-configuration_zh.md   # Configuration system
    ├── 02-packaging_zh.md       # Packaging and deployment
    ├── 03-troubleshooting_zh.md # Common issues and solutions
    ├── 04-quick-reference_zh.md # Quick command reference
    ├── 05-build-scripts_zh.md   # Build scripts guide
    └── 06-sys-path-auto-handling_zh.md # sys.path auto-handling

examples/
├── basic/
│   ├── hello_world.py
│   ├── crud_example.py
│   └── test_controller.py
├── config/
│   ├── config_example.py
│   └── cullinan.json
└── packaging/
    ├── packaging_test.py
    └── diagnose_app.py

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

---

## 📄 License

Cullinan is open-source software licensed under the MIT License.

See [LICENSE](../LICENSE) for details.

---

**Happy coding with Cullinan! 🎉**

