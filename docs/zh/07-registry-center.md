# 注册中心 (Registry Center)

[English](../07-registry-center.md) | **[中文](07-registry-center.md)**

---

## 📖 目录

- [概述](#概述)
- [核心概念](#核心概念)
- [HandlerRegistry - 处理器注册中心](#handlerregistry---处理器注册中心)
- [HeaderRegistry - 头部注册中心](#headerregistry---头部注册中心)
- [使用指南](#使用指南)
- [迁移指南](#迁移指南)
- [API 参考](#api-参考)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 概述

Cullinan 的注册中心模块 (`cullinan.registry`) 提供了一个集中化的、可测试的、可维护的方式来管理 HTTP 处理器和全局头部信息。

### 为什么需要注册中心？

在早期版本中，Cullinan 使用全局列表（`handler_list` 和 `header_list`）来管理处理器和头部。这种方式存在以下问题：

- **测试困难**：全局状态使得测试隔离变得困难
- **缺乏封装**：代码中直接操作全局列表
- **扩展性差**：难以添加新功能如中间件、钩子等
- **维护性差**：全局状态增加了代码理解和维护的难度

注册中心模式解决了这些问题，提供了：

- ✅ **更好的测试性**：可以创建独立的注册中心实例进行测试
- ✅ **更好的封装**：通过类接口管理注册逻辑
- ✅ **更好的扩展性**：易于添加元数据、钩子、中间件等
- ✅ **更好的可维护性**：清晰的职责边界和接口

### 版本信息

注册中心模块在 **v0.65** 版本中引入，计划在 **v0.7x** 版本中完全启用和集成。

当前状态：
- ✅ 核心实现已完成
- ✅ API 设计已稳定
- ✅ 测试覆盖完整
- 🔄 向后兼容层已提供
- 📋 完全集成计划在 0.7x 版本

---

## 核心概念

Cullinan 注册中心包含两个主要组件：

### 1. HandlerRegistry（处理器注册中心）

管理 URL 路由和对应的处理器类（Controller）。负责：

- URL 模式注册
- 处理器类映射
- 路由排序（支持静态和动态路由）
- 处理器查找和检索

### 2. HeaderRegistry（头部注册中心）

管理全局 HTTP 响应头部。负责：

- 全局头部注册
- 头部列表维护
- 头部应用到响应

---

## HandlerRegistry - 处理器注册中心

### 基本用法

```python
from cullinan.registry import HandlerRegistry

# 创建注册中心实例
registry = HandlerRegistry()

# 注册处理器
from myapp.controllers import UserController
registry.register('/api/users', UserController)
registry.register('/api/users/([a-zA-Z0-9-]+)', UserDetailController)

# 获取所有处理器
handlers = registry.get_handlers()

# 获取处理器数量
count = registry.count()

# 排序处理器（确保路由匹配优先级正确）
registry.sort()

# 清空注册（主要用于测试）
registry.clear()
```

### 路由排序

`HandlerRegistry` 实现了智能的路由排序算法（O(n log n) 复杂度），确保：

1. **静态路由优先于动态路由**：`/api/users/profile` 优先于 `/api/users/([a-zA-Z0-9-]+)`
2. **更长的路径优先**：`/api/v1/users` 优先于 `/api/users`
3. **同级别按字典序排序**

示例：

```python
registry = HandlerRegistry()

# 注册多个路由
registry.register('/api/users', UsersController)
registry.register('/api/users/([a-zA-Z0-9-]+)', UserDetailController)
registry.register('/api/users/profile', ProfileController)
registry.register('/api', ApiRootController)

# 排序后的顺序：
registry.sort()
# 1. /api/users/profile        (最长静态路由)
# 2. /api/users/([a-zA-Z0-9-]+)  (动态路由)
# 3. /api/users                (静态路由)
# 4. /api                      (最短路由)
```

### 性能特点

- **注册操作**：O(1) - 常数时间
- **排序操作**：O(n log n) - 对数线性时间（使用 Python 的 Timsort）
- **查询操作**：O(n) - 线性时间（顺序匹配）
- **内存占用**：O(n) - 线性空间

对比旧的排序实现：

| 路由数量 | 旧算法 (O(n³)) | 新算法 (O(n log n)) | 加速比 |
|---------|----------------|---------------------|--------|
| 10      | ~1ms          | ~0.023ms            | 43x    |
| 50      | ~125ms        | ~0.20ms             | 625x   |
| 100     | ~1000ms       | ~0.94ms             | 1064x  |
| 500     | ~125s         | ~3.1ms              | 40,323x|

---

## HeaderRegistry - 头部注册中心

### 基本用法

```python
from cullinan.registry import HeaderRegistry

# 创建注册中心实例
registry = HeaderRegistry()

# 注册全局头部
registry.register(('Access-Control-Allow-Origin', '*'))
registry.register(('X-Frame-Options', 'DENY'))
registry.register(('X-Content-Type-Options', 'nosniff'))

# 获取所有头部
headers = registry.get_headers()

# 检查是否有头部注册
if registry.has_headers():
    print(f"已注册 {registry.count()} 个头部")

# 清空注册
registry.clear()
```

### 常见使用场景

#### 1. CORS 配置

```python
header_registry = HeaderRegistry()

# 配置 CORS
header_registry.register(('Access-Control-Allow-Origin', '*'))
header_registry.register(('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'))
header_registry.register(('Access-Control-Allow-Headers', 'Content-Type, Authorization'))
header_registry.register(('Access-Control-Max-Age', '3600'))
```

#### 2. 安全头部

```python
header_registry = HeaderRegistry()

# 安全相关头部
header_registry.register(('X-Frame-Options', 'DENY'))
header_registry.register(('X-Content-Type-Options', 'nosniff'))
header_registry.register(('X-XSS-Protection', '1; mode=block'))
header_registry.register(('Strict-Transport-Security', 'max-age=31536000; includeSubDomains'))
header_registry.register(('Content-Security-Policy', "default-src 'self'"))
```

#### 3. 自定义应用头部

```python
header_registry = HeaderRegistry()

# 应用标识
header_registry.register(('X-Powered-By', 'Cullinan/0.7x'))
header_registry.register(('X-App-Version', '1.0.0'))
header_registry.register(('X-Request-ID', '${request_id}'))  # 动态值
```

---

## 使用指南

### 获取全局注册中心

Cullinan 提供了全局注册中心实例，可以直接使用：

```python
from cullinan.registry import get_handler_registry, get_header_registry

# 获取全局处理器注册中心
handler_registry = get_handler_registry()
handler_registry.register('/api/users', UserController)

# 获取全局头部注册中心
header_registry = get_header_registry()
header_registry.register(('X-Custom-Header', 'value'))
```

### 依赖注入模式（推荐用于测试）

对于需要隔离的场景（如单元测试），可以创建独立的注册中心实例：

```python
def create_app(handler_registry=None, header_registry=None):
    """创建应用实例，支持注入自定义注册中心"""
    if handler_registry is None:
        handler_registry = get_handler_registry()
    if header_registry is None:
        header_registry = get_header_registry()
    
    # 使用注入的注册中心
    return Application(handler_registry, header_registry)

# 测试时
def test_my_app():
    # 创建隔离的注册中心
    test_handler_registry = HandlerRegistry()
    test_header_registry = HeaderRegistry()
    
    # 注册测试处理器
    test_handler_registry.register('/test', TestController)
    
    # 创建测试应用
    app = create_app(test_handler_registry, test_header_registry)
    
    # 测试...
    
    # 清理
    test_handler_registry.clear()
    test_header_registry.clear()
```

### 重置注册中心

在测试或重新初始化场景中，可以重置全局注册中心：

```python
from cullinan.registry import reset_registries

# 清空所有全局注册
reset_registries()
```

⚠️ **注意**：在生产环境中不要使用 `reset_registries()`，这会清空所有已注册的处理器和头部。

---

## 迁移指南

### 从全局列表迁移到注册中心

如果你的代码使用了旧的全局列表方式，可以按照以下步骤迁移：

#### 旧方式（0.6x 及更早版本）

```python
from cullinan.controller import handler_list, header_list

# 直接操作全局列表
handler_list.append(('/api/users', UserController))
header_list.append(('X-Custom-Header', 'value'))

# 手动排序
from cullinan.application import sort_url
sort_url()
```

#### 新方式（0.7x 版本推荐）

```python
from cullinan.registry import get_handler_registry, get_header_registry

# 使用注册中心 API
handler_registry = get_handler_registry()
handler_registry.register('/api/users', UserController)

header_registry = get_header_registry()
header_registry.register(('X-Custom-Header', 'value'))

# 排序集成在注册中心中
handler_registry.sort()
```

### 向后兼容

当前版本（0.65-0.7x）保持了向后兼容性。全局列表 `handler_list` 和 `header_list` 仍然可用，但建议新代码使用注册中心模式。

在未来的主要版本（1.0+）中，全局列表可能会被弃用。

---

## API 参考

### HandlerRegistry 类

#### `__init__()`
创建一个新的处理器注册中心实例。

```python
registry = HandlerRegistry()
```

#### `register(url: str, servlet: Any) -> None`
注册一个 URL 模式和对应的处理器类。

**参数：**
- `url` (str): URL 模式，可包含正则表达式如 `([a-zA-Z0-9-]+)`
- `servlet` (Any): 处理器类（Controller 类）

**示例：**
```python
registry.register('/api/users', UserController)
registry.register('/api/users/([a-zA-Z0-9-]+)', UserDetailController)
```

#### `get_handlers() -> List[Tuple[str, Any]]`
获取所有已注册的处理器列表（副本）。

**返回：**
- List[Tuple[str, Any]]: (url_pattern, servlet) 元组列表

**示例：**
```python
handlers = registry.get_handlers()
for url, servlet in handlers:
    print(f"Route: {url} -> {servlet.__name__}")
```

#### `clear() -> None`
清空所有已注册的处理器。

**用途：** 主要用于测试，在生产环境慎用。

**示例：**
```python
registry.clear()
```

#### `count() -> int`
获取已注册处理器的数量。

**返回：**
- int: 已注册的 URL 模式数量

**示例：**
```python
print(f"Total routes: {registry.count()}")
```

#### `sort() -> None`
对处理器进行排序，确保路由匹配优先级正确。

**算法复杂度：** O(n log n)

**示例：**
```python
registry.sort()
```

---

### HeaderRegistry 类

#### `__init__()`
创建一个新的头部注册中心实例。

```python
registry = HeaderRegistry()
```

#### `register(header: Any) -> None`
注册一个全局头部。

**参数：**
- `header` (Any): 头部对象或元组，通常是 `(header_name, header_value)` 元组

**示例：**
```python
registry.register(('Content-Type', 'application/json'))
registry.register(('X-Custom-Header', 'custom-value'))
```

#### `get_headers() -> List[Any]`
获取所有已注册的头部列表（副本）。

**返回：**
- List[Any]: 头部对象/元组列表

**示例：**
```python
headers = registry.get_headers()
for header in headers:
    print(f"Header: {header}")
```

#### `clear() -> None`
清空所有已注册的头部。

**用途：** 主要用于测试，在生产环境慎用。

**示例：**
```python
registry.clear()
```

#### `count() -> int`
获取已注册头部的数量。

**返回：**
- int: 已注册的头部数量

**示例：**
```python
print(f"Total headers: {registry.count()}")
```

#### `has_headers() -> bool`
检查是否有已注册的头部。

**返回：**
- bool: 如果有头部返回 True，否则返回 False

**示例：**
```python
if registry.has_headers():
    print("Headers are configured")
```

---

### 全局函数

#### `get_handler_registry() -> HandlerRegistry`
获取全局默认的处理器注册中心实例。

**返回：**
- HandlerRegistry: 全局处理器注册中心

**示例：**
```python
from cullinan.registry import get_handler_registry

registry = get_handler_registry()
```

#### `get_header_registry() -> HeaderRegistry`
获取全局默认的头部注册中心实例。

**返回：**
- HeaderRegistry: 全局头部注册中心

**示例：**
```python
from cullinan.registry import get_header_registry

registry = get_header_registry()
```

#### `reset_registries() -> None`
重置所有全局注册中心到空状态。

**用途：** 主要用于测试，确保测试之间的隔离。

**⚠️ 警告：** 不要在生产环境中使用。

**示例：**
```python
from cullinan.registry import reset_registries

# 在每个测试前重置
def setup():
    reset_registries()
```

---

## 最佳实践

### 1. 生产环境使用全局注册中心

在生产应用中，使用全局注册中心实例：

```python
from cullinan import configure, application
from cullinan.controller import controller, get_api
from cullinan.registry import get_handler_registry, get_header_registry

# 配置
configure(user_packages=['myapp'])

# 使用装饰器会自动注册到全局注册中心
@controller(url='/api')
class UserController:
    @get_api(url='/users')
    def list_users(self):
        return {'users': []}

# 运行应用
if __name__ == '__main__':
    application.run()
```

### 2. 测试时使用独立实例

在测试中创建独立的注册中心实例：

```python
import unittest
from cullinan.registry import HandlerRegistry, HeaderRegistry, reset_registries

class TestMyController(unittest.TestCase):
    def setUp(self):
        """每个测试前创建新的注册中心"""
        self.handler_registry = HandlerRegistry()
        self.header_registry = HeaderRegistry()
    
    def tearDown(self):
        """每个测试后清理"""
        self.handler_registry.clear()
        self.header_registry.clear()
    
    def test_registration(self):
        """测试处理器注册"""
        from myapp.controllers import UserController
        
        self.handler_registry.register('/api/users', UserController)
        self.assertEqual(self.handler_registry.count(), 1)
```

### 3. 初始化时注册全局头部

在应用启动时一次性注册所有全局头部：

```python
from cullinan import configure
from cullinan.registry import get_header_registry

def init_app():
    # 配置框架
    configure(user_packages=['myapp'])
    
    # 注册全局头部
    header_registry = get_header_registry()
    
    # CORS 头部
    header_registry.register(('Access-Control-Allow-Origin', '*'))
    header_registry.register(('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE'))
    
    # 安全头部
    header_registry.register(('X-Frame-Options', 'DENY'))
    header_registry.register(('X-Content-Type-Options', 'nosniff'))
    
    # 应用信息
    header_registry.register(('X-Powered-By', 'Cullinan'))

if __name__ == '__main__':
    init_app()
    from cullinan import application
    application.run()
```

### 4. 路由排序最佳实践

确保在所有处理器注册完成后进行排序：

```python
from cullinan.registry import get_handler_registry

def register_all_routes():
    registry = get_handler_registry()
    
    # 注册所有路由
    registry.register('/api/users', UserListController)
    registry.register('/api/users/([a-zA-Z0-9-]+)', UserDetailController)
    registry.register('/api/users/profile', UserProfileController)
    registry.register('/api/posts', PostListController)
    registry.register('/api/posts/([0-9]+)', PostDetailController)
    
    # 注册完成后排序（确保路由匹配优先级正确）
    registry.sort()
```

### 5. 避免重复注册

检查路由是否已注册以避免重复：

```python
from cullinan.registry import get_handler_registry

registry = get_handler_registry()

# registry.register() 内部已经处理了重复检查
# 重复注册同一个 URL 会被忽略并记录调试日志
registry.register('/api/users', UserController)
registry.register('/api/users', UserController)  # 第二次调用会被忽略
```

### 6. 日志和调试

启用调试日志来跟踪注册中心操作：

```python
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 注册中心操作会输出调试信息
# DEBUG:cullinan.registry:Registered handler for URL: /api/users
# DEBUG:cullinan.registry:Sorted 5 handlers
```

---

## 常见问题

### Q1: 注册中心和全局列表有什么区别？

**A:** 主要区别在于封装和可测试性：

| 特性 | 全局列表 | 注册中心 |
|------|---------|---------|
| 封装性 | 差（直接操作列表）| 好（通过类接口）|
| 测试性 | 差（难以隔离）| 好（可创建独立实例）|
| 扩展性 | 差（难以添加功能）| 好（易于扩展）|
| 维护性 | 差（职责不清晰）| 好（清晰的职责边界）|

### Q2: 我需要迁移现有代码吗？

**A:** 不是必须的。当前版本（0.65-0.7x）保持向后兼容性，全局列表仍然可用。但建议新代码使用注册中心模式，以获得更好的可测试性和维护性。

### Q3: 性能有影响吗？

**A:** 没有负面影响，反而有提升：

- 注册操作：性能相同（O(1)）
- 排序操作：新算法更快（O(n log n) vs O(n³)）
- 查询操作：性能相同（O(n)）
- 内存占用：略微增加（封装开销），但可忽略不计

### Q4: 如何在多线程环境中使用？

**A:** 注册中心设计为在启动阶段注册（单线程），运行时只读访问（多线程安全）：

```python
# 启动阶段（单线程）
def init_app():
    registry = get_handler_registry()
    registry.register('/api/users', UserController)
    registry.sort()

# 运行时（多线程）- 只读访问是安全的
def handle_request():
    handlers = registry.get_handlers()  # 返回副本，线程安全
    # ...
```

如果需要在运行时动态注册（不推荐），需要自己实现同步机制。

### Q5: 为什么排序很重要？

**A:** 排序确保路由匹配的优先级正确：

```python
# 未排序可能导致错误匹配
handlers = [
    ('/api/users/([a-zA-Z0-9-]+)', UserDetailController),  # 动态路由
    ('/api/users/profile', ProfileController),              # 静态路由
]
# 访问 /api/users/profile 会匹配到 UserDetailController（错误！）

# 排序后
handlers = [
    ('/api/users/profile', ProfileController),              # 静态路由优先
    ('/api/users/([a-zA-Z0-9-]+)', UserDetailController),  # 动态路由
]
# 访问 /api/users/profile 正确匹配到 ProfileController
```

### Q6: 可以动态添加和删除路由吗？

**A:** 理论上可以，但不推荐在运行时修改注册中心：

- ✅ **推荐**：在启动阶段一次性注册所有路由
- ⚠️ **不推荐**：运行时动态修改（需要考虑线程安全、重新排序等）

如果确实需要动态路由，考虑使用中间件或插件机制（计划在未来版本中提供）。

### Q7: 注册中心支持中间件吗？

**A:** 当前版本（0.65-0.7x）的注册中心专注于核心功能（注册和排序）。中间件支持计划在未来版本中添加。

设计预览（计划中）：

```python
# 未来版本可能的 API
registry.register(
    '/api/users',
    UserController,
    middleware=[AuthMiddleware, LoggingMiddleware],
    metadata={'auth_required': True, 'rate_limit': 100}
)
```

### Q8: 测试时如何避免全局状态污染？

**A:** 使用独立的注册中心实例或在测试间重置：

```python
# 方法 1：使用独立实例（推荐）
class TestMyController(unittest.TestCase):
    def setUp(self):
        self.registry = HandlerRegistry()
    
    def tearDown(self):
        self.registry.clear()

# 方法 2：重置全局注册中心
class TestMyController(unittest.TestCase):
    def setUp(self):
        from cullinan.registry import reset_registries
        reset_registries()
```

---

## 相关资源

### 文档链接

- [完整指南](00-complete-guide.md) - 框架完整指南
- [配置指南](01-configuration.md) - 配置系统
- [快速参考](04-quick-reference.md) - 快速命令参考

### 源代码

- [registry.py](../../cullinan/registry.py) - 注册中心实现
- [test_registry.py](../../tests/test_registry.py) - 单元测试

### 设计文档

- [REGISTRY_PATTERN_DESIGN.md](../../REGISTRY_PATTERN_DESIGN.md) - 注册中心设计文档
- [opt_and_refactor_cullinan.md](../../opt_and_refactor_cullinan.md) - 优化和重构记录

---

## 变更历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.65 | 2024 | 注册中心模块引入 |
| 0.7x | 计划中 | 完全集成注册中心模式 |
| 1.0+ | 未来 | 可能弃用全局列表 |

---

**反馈和问题？**

- **GitHub Issues**: [报告问题](https://github.com/plumeink/Cullinan/issues)
- **Discussions**: [讨论交流](https://github.com/plumeink/Cullinan/discussions)

---

[返回文档索引](README_zh.md)
