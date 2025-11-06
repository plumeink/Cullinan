![Python version](https://img.shields.io/badge/python-3.7%20|%203.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-blue)
![PyPI version](https://img.shields.io/pypi/v/cullinan.svg?style=flat&logo=pypi&color=green)
![PyPI downloads](https://img.shields.io/pypi/dm/cullinan.svg?style=flat&logo=pypi&color=blue)
![GitHub stars](https://img.shields.io/github/stars/plumeink/cullinan.svg?style=flat&logo=github&color=white)
![License](https://img.shields.io/github/license/plumeink/cullinan.svg?style=flat&color=white)

```                                              
   _____      _ _ _                      
  / ____|    | | (_)                     
 | |    _   _| | |_ _ __   __ _ _ __     
 | |   | | | | | | | '_ \ / _` | '_ \    
 | |___| |_| | | | | | | | (_| | | | |   
 \_____\__, _|_|_|_|_| |_|\__,_|_| |_|  
```

# Cullinan

**A lightweight, production-ready Python web framework with full packaging support.**

Cullinan is built on Tornado and SQLAlchemy, designed to help you quickly build web applications with easy packaging for deployment.

---

## ✨ Features

- 🚀 **Easy to Use** - Simple decorator-based routing
- 📦 **Packaging Ready** - Full Nuitka & PyInstaller support
- ⚙️ **Flexible Configuration** - Multiple configuration options
- 🌍 **Cross-Platform** - Windows, Linux, macOS
- 🏭 **Production Ready** - Built on battle-tested Tornado
- 🗄️ **SQLAlchemy Integration** - Built-in ORM support
- 🔧 **Smart Module Loading** - Auto-discovery for development, configurable for packaging

---

## 📚 Documentation

**[📖 Complete Documentation](docs/README.md)** | **[📖 完整文档](docs/zh/README_zh.md)**

### Language / 语言

- **[English Documentation](docs/README.md)** - Complete English documentation
- **[中文文档](docs/zh/README_zh.md)** - 完整中文文档

### Quick Links

| Guide | Description |
|-------|-------------|
| [Complete Guide](docs/00-complete-guide.md) / [完整指南](docs/zh/00-complete-guide_zh.md) | Full framework tutorial |
| [Configuration](docs/01-configuration.md) / [配置](docs/zh/01-configuration_zh.md) | Configure your application |
| [Packaging](docs/02-packaging.md) / [打包](docs/zh/02-packaging_zh.md) | Package for deployment |
| [Troubleshooting](docs/03-troubleshooting.md) / [故障排查](docs/zh/03-troubleshooting_zh.md) | Common issues |
| [Build Scripts](docs/05-build-scripts.md) / [构建脚本](docs/zh/05-build-scripts_zh.md) | Advanced packaging |

---

## 🚀 Quick Start

## 📦 Installation

### From PyPI (Stable Release)

```bash
pip install cullinan
```

### From Source (Latest Features)

```bash
git clone https://github.com/plumeink/Cullinan.git
cd Cullinan
pip install -e .
```

> **💡 Tip**: For the latest features and bug fixes, install from source.

### Basic Application

```python
# app.py
from cullinan import configure, application
from cullinan.controller import controller, get_api

# Configure for packaging (optional in development)
configure(user_packages=['your_app'])

@controller(url='/api')
class HelloController:
    @get_api(url='/hello')
    def hello(self, query_params):
        return {'message': 'Hello, Cullinan!'}

if __name__ == '__main__':
    application.run()
```

### Run

```bash
python app.py
# Visit: http://localhost:8080/api/hello
```

---

## 📦 Packaging Support

### New Configuration System

Cullinan 2.0+ introduces a **configuration-driven** packaging system:

```python
from cullinan import configure

# Tell Cullinan which packages to scan
configure(user_packages=['your_app'])
```

### Package Your Application

**Option 1: Universal Builder (Recommended)**

```bash
# Interactive mode
python scripts/build_app.py

# Quick builds
python scripts/build_app.py --tool nuitka --mode onefile
python scripts/build_app.py --tool pyinstaller
```

**Option 2: Direct Commands**

```bash
# Nuitka
nuitka --standalone --include-package=your_app --include-package=cullinan app.py

# PyInstaller
pyinstaller --onedir --hidden-import=your_app --collect-all=cullinan app.py
```

📖 **[Full Packaging Guide](docs/zh/02-packaging.md)** | **[Build Scripts Guide](docs/zh/05-build-scripts.md)**

---

## 💡 Full Example

### Project Structure

```
my_app/
├── main.py              # Entry point
├── controllers/         # Controllers
│   ├── __init__.py
│   └── api.py
├── services/            # Services
│   ├── __init__.py
│   └── data.py
└── models/              # Models
    ├── __init__.py
    └── user.py
```

### Controller (`controllers/api.py`)

```python
from cullinan.controller import controller, get_api, post_api

@controller(url='/api')
class UserController:
    
    @get_api(url='/users', query_params=['id'])
    def get_user(self, query_params):
        user_id = query_params.get('id')
        return self.service['UserService'].get_user(user_id)
    
    @post_api(url='/users', body_params=['name', 'email'])
    def create_user(self, body_params):
        return self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
```

### Service (`services/data.py`)

```python
from cullinan.service import Service, service
from cullinan.dao import Conn

@service
class UserService(Service):
    
    def __init__(self):
        super().__init__()
        self.db = Conn.conn()
    
    def get_user(self, user_id):
        # Your business logic here
        user = {'id': user_id, 'name': 'John Doe'}
        self.response.set_body(user)
        return self.response
    
    def create_user(self, name, email):
        # Your business logic here
        user = {'name': name, 'email': email}
        self.response.set_body(user)
        return self.response
```

### Application (`main.py`)

```python
from cullinan import configure, application

# Configure for packaging
configure(
    user_packages=['my_app'],
    verbose=True  # Enable logging
)

def main():
    application.run()

if __name__ == '__main__':
    main()
```

### Build for Production

```bash
# Development
python main.py

# Production (Nuitka)
python scripts/build_nuitka_advanced.py --entry main.py --onefile --optimize

# Distribution (PyInstaller)
python scripts/build_pyinstaller_advanced.py --entry main.py --onefile --upx
```

---

## 🔧 Advanced Features

### Multiple Configuration Methods

**1. Code Configuration (Recommended)**

```python
from cullinan import configure

configure(user_packages=['your_app'])
```

**2. JSON Configuration**

```json
{
  "user_packages": ["your_app"],
  "verbose": true,
  "auto_scan": false
}
```

```python
import json
from cullinan import get_config

with open('cullinan.json') as f:
    get_config().from_dict(json.load(f))
```

**3. Environment Variables**

```bash
export CULLINAN_USER_PACKAGES=your_app
```

### Build Scripts

Cullinan provides three powerful build scripts:

1. **`build_app.py`** - Universal builder (auto-detect, interactive)
2. **`build_nuitka_advanced.py`** - Advanced Nuitka features (GCC, LTO, optimization)
3. **`build_pyinstaller_advanced.py`** - Advanced PyInstaller features (UPX, icons)

📖 **[Build Scripts Guide](docs/zh/05-build-scripts.md)**

---

## 🎯 Why Cullinan?

| Feature | Cullinan | Flask | FastAPI | Django |
|---------|----------|-------|---------|--------|
| **Easy Packaging** | ✅ Built-in | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual |
| **Async Support** | ✅ Tornado | ❌ | ✅ | ⚠️ Limited |
| **Learning Curve** | 🟢 Low | 🟢 Low | 🟡 Medium | 🔴 High |
| **ORM Integration** | ✅ SQLAlchemy | ⚠️ Extensions | ⚠️ External | ✅ Built-in |
| **Decorator Routing** | ✅ | ✅ | ✅ | ⚠️ Class-based |
| **Build Scripts** | ✅ Included | ❌ | ❌ | ❌ |

---

## 📖 Documentation Structure

```
docs/
├── README.md                    # Documentation index
├── index.md                     # Framework overview
├── 01-configuration.md          # Configuration guide
├── 02-packaging.md              # Packaging guide
├── 03-troubleshooting.md        # Troubleshooting
├── 04-quick-reference.md        # Quick reference
└── 05-build-scripts.md          # Build scripts guide
```

---

## 🔗 Links

- **Documentation**: [docs/README.md](docs/README.md)
- **GitHub**: https://github.com/plumeink/Cullinan
- **PyPI**: https://pypi.org/project/cullinan/
- **Issues**: https://github.com/plumeink/Cullinan/issues
- **Discussions**: https://github.com/plumeink/Cullinan/discussions

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [Contributing Guidelines](docs/README.md#contributing-to-documentation) for details.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built on [Tornado](https://www.tornadoweb.org/)
- ORM powered by [SQLAlchemy](https://www.sqlalchemy.org/)
- Packaging powered by [Nuitka](https://nuitka.net/) and [PyInstaller](https://pyinstaller.org/)

---

## 📊 Statistics

![GitHub stars](https://img.shields.io/github/stars/plumeink/cullinan?style=social)
![GitHub forks](https://img.shields.io/github/forks/plumeink/cullinan?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/plumeink/cullinan?style=social)

---

**Made with ❤️ by the Cullinan Team**

