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
- 📋 **Registry Center** - Centralized, testable handler and header management

---

## 📚 Documentation

### Language / 语言

- **[English Documentation](docs/README.md)** - Complete English documentation
- **[中文文档](docs/zh/README_zh.md)** - 完整中文文档

---

## 🚀 Quick Start

## 📦 Installation

### From PyPI (Stable Release)

```bash
pip install cullinan
```

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
        return self.response_build(status=200, message="Hello, Cullinan!" + query_params)

if __name__ == '__main__':
    application.run()
```

### Run

```bash
python app.py
# Visit: http://localhost:4080/api/hello
```

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
        return self.response_build(status=200, message="User fetched successfully", data={"user_id": user_id})
    
    @post_api(url='/users', body_params=['name', 'email'])
    def create_user(self, body_params):
        self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
        return self.response_build(status=201, message="User created successfully")
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

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built on [Tornado](https://www.tornadoweb.org/)
- ORM powered by [SQLAlchemy](https://www.sqlalchemy.org/)
- Packaging powered by [Nuitka](https://nuitka.net/) and [PyInstaller](https://pyinstaller.org/)

---

## 💻 Maintainer

[<img src="https://avatars.githubusercontent.com/u/104434649?v=4" width = "40" height = "40"/>](https://github.com/plumeink)