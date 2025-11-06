# Cullinan Framework Documentation

**[English](README.md)** | [中文](zh/README_zh.md)

Welcome to Cullinan! Complete documentation for building production-ready web applications with Python.

---

## 📖 Documentation Index

### Quick Start
- **[Complete Guide](00-complete-guide.md)** ⭐ **START HERE!**  
  Comprehensive tutorial covering all features with examples

### Core Documentation

0. [**Complete Guide**](00-complete-guide.md) 🌟  
   Full framework guide from basics to advanced topics
   - Installation & Setup
   - Quick Start Tutorial → [Example](../examples/basic/hello_world.py)
   - Controllers & Services → [Example](../examples/basic/crud_example.py)
   - Database, WebSocket, Hooks
   - API Reference & FAQ

1. [**Configuration Guide**](01-configuration.md)  
   Complete guide to configuring Cullinan
   - Basic configuration → [Example](../examples/config/config_example.py)
   - JSON configuration → [Example](../examples/config/cullinan.json)
   - Environment variables
   - Packaging configuration

2. [**Packaging Guide**](02-packaging.md)  
   Package your applications for deployment
   - Nuitka & PyInstaller support
   - Cross-platform builds → [Scripts](../scripts/)
   - Different packaging modes
   - Platform-specific instructions

3. [**Troubleshooting**](03-troubleshooting.md)  
   Common issues and solutions
   - Module not found errors
   - Controller/Service registration
   - Packaging problems
   - Debugging techniques → [Diagnostic Tool](../examples/packaging/diagnose_app.py)

4. [**Quick Reference**](04-quick-reference.md)  
   Quick reference card
   - Configuration syntax
   - Packaging commands
   - Common patterns

5. [**Build Scripts**](05-build-scripts.md)  
   Comprehensive build scripts guide
   - Universal builder → [build_app.py](../scripts/build_app.py)
   - Advanced Nuitka → [build_nuitka_advanced.py](../scripts/build_nuitka_advanced.py)
   - Advanced PyInstaller → [build_pyinstaller_advanced.py](../scripts/build_pyinstaller_advanced.py)
   - Cross-platform support
   - Compiler options

6. [**sys.path Auto Handling**](06-sys-path-auto-handling.md) 🆕  
   Automatic project root detection
   - No more manual `sys.path.append`
   - Simplified startup code
   - Auto-detection logic explained
   - Migration guide from old method

---

## 🚀 Quick Start

### 1. Install

```bash
pip install cullinan
```

### 2. Create Your First App

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

**📝 Full example:** [`examples/basic/hello_world.py`](../examples/basic/hello_world.py)

### 3. Run & Test

```bash
python app.py
# Visit: http://localhost:8080/api/hello
```

---

## 💡 Examples Directory

All examples are located in [`examples/`](../examples/):

### Basic Examples
- [`hello_world.py`](../examples/basic/hello_world.py) - Simplest possible app
- [`crud_example.py`](../examples/basic/crud_example.py) - Full CRUD API
- [`test_controller.py`](../examples/test_controller.py) - Controller patterns

### Configuration Examples
- [`config_example.py`](../examples/config/config_example.py) - Code configuration
- [`cullinan.json`](../examples/config/cullinan.json) - JSON configuration
- [`APP_CONFIG_EXAMPLE.md`](../examples/APP_CONFIG_EXAMPLE.md) - Configuration docs

### Packaging Examples
- [`packaging_test.py`](../examples/packaging/packaging_test.py) - Test packaged app
- [`diagnose_app.py`](../examples/packaging/diagnose_app.py) - Diagnostic tool

---

## 🔗 Quick Links by Task

### I want to...

**Get started quickly**  
→ [Complete Guide](00-complete-guide.md) → [Hello World](../examples/basic/hello_world.py)

**Configure my application**  
→ [Configuration Guide](01-configuration.md) → [Config Example](../examples/config/config_example.py)

**Build a REST API**  
→ [Complete Guide: Controllers](00-complete-guide.md#controllers--routing) → [CRUD Example](../examples/basic/crud_example.py)

**Package for deployment**  
→ [Packaging Guide](02-packaging.md) → [Build Scripts](05-build-scripts.md)

**Fix packaging issues**  
→ [Troubleshooting](03-troubleshooting.md) → [Diagnostic Tool](../examples/packaging/diagnose_app.py)

**Use a build script**  
→ [Build Scripts Guide](05-build-scripts.md) → [Scripts Directory](../scripts/)

---

## 🧪 Testing

Run the test suite:

```bash
# Basic test
python run_tests.py

# With coverage
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
├── README.md                    # This file - English documentation index
├── 00-complete-guide.md         # ⭐ Complete framework guide
├── 01-configuration.md          # Configuration system
├── 02-packaging.md              # Packaging & deployment
├── 03-troubleshooting.md        # Common issues & solutions
├── 04-quick-reference.md        # Quick command reference
├── 05-build-scripts.md          # Build scripts guide
├── 06-sys-path-auto-handling.md # sys.path auto handling
└── zh/                          # Chinese documentation
    ├── README_zh.md
    └── ...

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

- **GitHub Issues**: [Report bugs](https://github.com/plumeink/Cullinan/issues)
- **Discussions**: [Ask questions](https://github.com/plumeink/Cullinan/discussions)
- **Documentation**: [Read the docs](00-complete-guide.md)
- **Examples**: [Browse examples](../examples/)

---

## 📄 License

Cullinan is open-source software licensed under the MIT License.

See [LICENSE](../LICENSE) for details.

---

**Happy coding with Cullinan! 🎉**

### Quick Start
- **[Complete Guide](00-complete-guide.md)** ⭐ **START HERE!**  
  Comprehensive tutorial covering all features with examples

### Core Documentation

0. [**Complete Guide**](00-complete-guide.md) 🌟  
   Full framework guide from basics to advanced topics
   - Installation & Setup
   - Quick Start Tutorial → [Example](../examples/basic/hello_world.py)
   - Controllers & Services → [Example](../examples/basic/crud_example.py)
   - Database, WebSocket, Hooks
   - API Reference & FAQ

1. [**Configuration Guide**](zh/01-configuration.md)  
   Complete guide to configuring Cullinan
   - Basic configuration → [Example](../examples/config/config_example.py)
   - JSON configuration → [Example](../examples/config/cullinan.json)
   - Environment variables
   - Packaging configuration

2. [**Packaging Guide**](zh/02-packaging.md)  
   Package your applications for deployment
   - Nuitka & PyInstaller support
   - Cross-platform builds → [Scripts](../scripts/)
   - Different packaging modes
   - Platform-specific instructions

3. [**Troubleshooting**](zh/03-troubleshooting.md)  
   Common issues and solutions
   - Module not found errors
   - Controller/Service registration
   - Packaging problems
   - Debugging techniques → [Diagnostic Tool](../examples/packaging/diagnose_app.py)

4. [**Quick Reference**](zh/04-quick-reference.md)  
   Quick reference card
   - Configuration syntax
   - Packaging commands
   - Common patterns

5. [**Build Scripts**](zh/05-build-scripts.md)  
   Comprehensive build scripts guide
   - Universal builder → [build_app.py](../scripts/build_app.py)
   - Advanced Nuitka → [build_nuitka_advanced.py](../scripts/build_nuitka_advanced.py)
   - Advanced PyInstaller → [build_pyinstaller_advanced.py](../scripts/build_pyinstaller_advanced.py)
   - Cross-platform support
   - Compiler options

6. [**sys.path Auto Handling**](zh/06-sys-path-auto-handling.md) 🆕  
   Automatic project root detection
   - No more manual `sys.path.append`
   - Simplified startup code
   - Auto-detection logic explained
   - Migration guide from old method

---

## 🚀 Quick Start

### 1. Install

```bash
pip install cullinan
```

### 2. Create Your First App

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

**📝 Full example:** [`examples/basic/hello_world.py`](../examples/basic/hello_world.py)

### 3. Run & Test

```bash
python app.py
# Visit: http://localhost:8080/api/hello
```

---

## 📚 Learning Path

### For Beginners

1. Read [Complete Guide](00-complete-guide.md) - Start here!
2. Try [Hello World Example](../examples/basic/hello_world.py)
3. Build a [CRUD API](../examples/basic/crud_example.py)
4. Learn [Configuration](zh/01-configuration.md)
5. Package your app with [Build Scripts](zh/05-build-scripts.md)

### For Advanced Users

- [Configuration Internals](zh/01-configuration.md#advanced-usage)
- [Custom Build Options](zh/05-build-scripts.md#advanced-topics)
- [Compiler Selection](zh/05-build-scripts.md#compiler-comparison-nuitka)
- [Optimization Techniques](zh/05-build-scripts.md#optimized-builds)
- [CI/CD Integration](zh/05-build-scripts.md#cicd-integration)

---

## 💡 Examples Directory

All examples are located in [`examples/`](../examples/):

### Basic Examples
- [`hello_world.py`](../examples/basic/hello_world.py) - Simplest possible app
- [`crud_example.py`](../examples/basic/crud_example.py) - Full CRUD API
- [`test_controller.py`](../examples/basic/test_controller.py) - Controller patterns

### Configuration Examples
- [`config_example.py`](../examples/config/config_example.py) - Code configuration
- [`cullinan.json`](../examples/config/cullinan.json) - JSON configuration
- [`APP_CONFIG_EXAMPLE.md`](../examples/APP_CONFIG_EXAMPLE.md) - Configuration docs

### Packaging Examples
- [`packaging_test.py`](../examples/packaging/packaging_test.py) - Test packaged app
- [`diagnose_app.py`](../examples/packaging/diagnose_app.py) - Diagnostic tool
- [`diagnose.py`](../examples/packaging/diagnose.py) - Basic diagnostics

---

## 🔗 Quick Links by Task

### I want to...

**Get started quickly**  
→ [Complete Guide](00-complete-guide.md) → [Hello World](../examples/basic/hello_world.py)

**Configure my application**  
→ [Configuration Guide](zh/01-configuration.md) → [Config Example](../examples/config/config_example.py)

**Build a REST API**  
→ [Complete Guide: Controllers](00-complete-guide.md#controllers--routing) → [CRUD Example](../examples/basic/crud_example.py)

**Package for deployment**  
→ [Packaging Guide](zh/02-packaging.md) → [Build Scripts](zh/05-build-scripts.md)

**Fix packaging issues**  
→ [Troubleshooting](zh/03-troubleshooting.md) → [Diagnostic Tool](../examples/packaging/diagnose_app.py)

**Use a build script**  
→ [Build Scripts Guide](zh/05-build-scripts.md) → [Scripts Directory](../scripts/)

**Test my installation**  
→ Run `python run_tests.py` in project root

---

## 🧪 Testing

Run the test suite:

```bash
# Basic test
python run_tests.py

# With coverage
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
├── 00-complete-guide.md         # ⭐ Complete framework guide
├── 01-configuration.md          # Configuration system
├── 02-packaging.md              # Packaging & deployment
├── 03-troubleshooting.md        # Common issues & solutions
├── 04-quick-reference.md        # Quick command reference
└── 05-build-scripts.md          # Build scripts guide

examples/
├── basic/
│   ├── hello_world.py          # Simplest example
│   ├── crud_example.py         # Full CRUD API
│   └── test_controller.py      # Controller patterns
├── config/
│   ├── config_example.py       # Configuration examples
│   └── cullinan.json           # JSON config
└── packaging/
    ├── packaging_test.py       # Package testing
    └── diagnose_app.py         # Diagnostic tool

scripts/
├── build_app.py                # Universal builder
├── build_nuitka_advanced.py    # Advanced Nuitka
└── build_pyinstaller_advanced.py # Advanced PyInstaller
```

---

## 🤝 Contributing

### Documentation Guidelines

When updating documentation:

1. **Keep examples simple** - Use clear, minimal code
2. **Link to examples** - Connect docs to example files
3. **Cross-reference** - Link related sections
4. **Test code** - Ensure all examples work
5. **Follow style** - Use consistent formatting

### Example Template

```markdown
## Feature Name

Brief description of the feature.

### Basic Usage

\`\`\`python
# Simple code example
\`\`\`

**📝 Full example:** [\`examples/path/to/example.py\`](../examples/path/to/example.py)

### Advanced Usage

More details...
```

---

## 📝 Documentation Style

### File Naming
- Use numbers for ordering: `00-`, `01-`, `02-`
- Use descriptive names: `complete-guide`, `configuration`
- Use lowercase with hyphens

### Content Structure

```markdown
# Title

Brief description

## Quick Start
Minimal example

## Detailed Guide
In-depth explanation

## Examples
Real-world examples → [Link to example file]

## See Also
- [Related Doc 1](link)
- [Related Doc 2](link)
```

---

## 🆘 Getting Help

- **GitHub Issues**: [Report bugs](https://github.com/plumeink/Cullinan/issues)
- **Discussions**: [Ask questions](https://github.com/plumeink/Cullinan/discussions)
- **Documentation**: [Read the docs](00-complete-guide.md)
- **Examples**: [Browse examples](../examples/)

---

## 📄 License

Cullinan is open-source software licensed under the MIT License.

See [LICENSE](../LICENSE) for details.

---

**Happy coding with Cullinan! 🎉**

