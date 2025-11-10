# Cullinan 完整指南

[English](../en/00-complete-guide.md) | [中文](00-complete-guide.md)

---

欢迎使用 Cullinan！本指南将帮助你快速上手并掌握框架。

## 📚 目录

### 入门指南
1. [安装与设置](#安装与设置)
2. [快速开始教程](#快速开始教程) → [示例](../../examples/basic/hello_world.py)
3. [项目结构](#项目结构)

### 核心概念
4. [配置系统](01-configuration_zh.md) → [示例](../../examples/config/)
5. [控制器与路由](#控制器与路由) → [示例](../../examples/basic/test_controller.py)
6. [服务与业务逻辑](#服务与业务逻辑)
7. [请求与响应](#请求与响应)
8. [数据库集成](#数据库集成)

### 高级主题
9. [打包与部署](02-packaging_zh.md) → [脚本](../../scripts/)
10. [构建脚本](05-build-scripts_zh.md)
11. [WebSocket 支持](#websocket-支持)
12. [钩子与中间件](#钩子与中间件)

### 参考
13. [API 参考](#api-参考)
14. [故障排查](03-troubleshooting_zh.md)
15. [常见问题](#常见问题)

---

## 安装与设置

### 系统要求

- Python 3.7 或更高版本
- pip（Python 包管理器）

### 从 PyPI 安装

```bash
pip install cullinan
```

> **注意**: 如果 PyPI 上的版本较旧，请从源码安装最新版本。

### 从源码安装（推荐获取最新功能）

```bash
git clone https://github.com/plumeink/Cullinan.git
cd Cullinan
pip install -e .
```

### 验证安装

```bash
python -c "import cullinan; print('Cullinan 安装成功')"
```

---

## 快速开始教程

### 1. 创建第一个应用

创建名为 `app.py` 的文件：

```python
# app.py
from cullinan import configure, application
from cullinan.controller import controller, get_api

# 配置 Cullinan
configure(user_packages=['__main__'])

@controller(url='/api')
class HelloController:
    @get_api(url='/hello')
    def hello(self, query_params):
        return {'message': '你好，Cullinan！'}

if __name__ == '__main__':
    application.run()
```

**📝 完整示例：** [`examples/basic/hello_world.py`](../../examples/basic/hello_world.py)

### 2. 运行应用

```bash
python app.py
```

访问：http://localhost:8080/api/hello

### 3. 测试 API

```bash
curl http://localhost:8080/api/hello
# 输出: {"message": "你好，Cullinan！"}
```

---

## 项目结构

### 推荐的目录布局

```
my_app/
├── main.py                 # 应用入口
├── controllers/            # 控制器模块
│   ├── __init__.py
│   ├── user_controller.py
│   └── api_controller.py
├── services/               # 业务逻辑服务
│   ├── __init__.py
│   ├── user_service.py
│   └── auth_service.py
├── models/                 # 数据库模型
│   ├── __init__.py
│   └── user.py
├── config/                 # 配置文件
│   ├── __init__.py
│   └── settings.py
└── tests/                  # 单元测试
    └── test_api.py
```

**📝 查看示例结构：** [`examples/`](../../examples/)

---

## 控制器与路由

### 基础控制器

控制器处理 HTTP 请求并定义 API 端点。

```python
from cullinan.controller import controller, get_api, post_api

@controller(url='/users')
class UserController:
    """用户管理控制器"""
    
    @get_api(url='/', query_params=['id'])
    def get_user(self, query_params):
        """根据 ID 获取用户"""
        user_id = query_params.get('id')
        return self.service['UserService'].get_user(user_id)
    
    @post_api(url='/', body_params=['name', 'email'])
    def create_user(self, body_params):
        """创建新用户"""
        return self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
```

**📝 完整示例：** [`examples/basic/crud_example.py`](../../examples/basic/crud_example.py)

### 支持的 HTTP 方法

| 装饰器 | HTTP 方法 | 用途 |
|--------|-----------|------|
| `@get_api` | GET | 获取数据 |
| `@post_api` | POST | 创建资源 |
| `@put_api` | PUT | 更新资源 |
| `@delete_api` | DELETE | 删除资源 |
| `@patch_api` | PATCH | 部分更新 |

---

## 服务与业务逻辑

服务包含业务逻辑，与控制器分离。

### 创建服务

```python
from cullinan.service import Service, service
from cullinan.dao import Conn

@service
class UserService(Service):
    """用户业务逻辑"""
    
    def __init__(self):
        super().__init__()
        self.db = Conn.conn()
    
    def get_user(self, user_id):
        """根据 ID 获取用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user:
            self.response.set_body({'id': user.id, 'name': user.name})
        else:
            self.response.set_status(404)
            self.response.set_body({'error': '用户未找到'})
        
        return self.response
```

---

## API 参考

### 装饰器

| 装饰器 | 参数 | 示例 |
|--------|------|------|
| `@controller` | `url` | `@controller(url='/api')` |
| `@get_api` | `url`, `query_params`, `headers` | `@get_api(url='/users', query_params=['id'])` |
| `@post_api` | `url`, `body_params`, `query_params` | `@post_api(url='/users', body_params=['name'])` |
| `@service` | 无参数 | `@service` |

### Response 对象

| 方法 | 说明 |
|------|------|
| `set_status(status, msg='')` | 设置状态码 |
| `set_body(data)` | 设置响应体 |
| `add_header(name, value)` | 添加响应头 |

---

## 下一步

- **部署应用**���查看 [打包指南](02-packaging_zh.md)
- **优化性能**：查看 [构建脚本](05-build-scripts_zh.md)
- **获取帮助**：查看 [故障排查](03-troubleshooting_zh.md)

---

## 示例索引

所有示例位于 [`examples/`](../../examples/) 目录：

- **基础示例**
  - [Hello World](../../examples/basic/hello_world.py)
  - [CRUD API](../../examples/basic/crud_example.py)

- **配置示例**
  - [代码配置](../../examples/config/config_example.py)

---

**祝你使用 Cullinan 编码愉快！** 🎉

