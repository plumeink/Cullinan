# Cullinan 框架架构文档（更新版）

> **版本**：v0.92  
> **最后更新**：2026-02-19  
> **作者**：Plumeink  
> **状态**：已更新

---

## 目录

1. [架构概览](#overview)
2. [核心组件](#core-components)
3. [IoC/DI 2.0 系统](#iocdi-20)
4. [扩展机制](#extensions)
5. [启动流程](#startup-flow)
6. [请求处理流程](#request-flow)
7. [模块扫描机制](#module-scanning)
8. [性能优化](#performance)
9. [从 0.83 迁移](#migration)

---

## 架构概览 {#overview}

Cullinan 是一个基于 Tornado 的 Web 框架，采用 **IoC/DI**（控制反转/依赖注入）设计模式，提供装饰器驱动的开发体验。

### 核心设计理念

- **非侵入式**：通过装饰器和注解实现功能，无需继承复杂基类
- **依赖注入**：自动管理组件依赖关系
- **扩展友好**：统一的扩展点注册和发现机制
- **高性能**：优化的启动和运行时性能

### 架构分层

```
┌─────────────────────────────────────────────────────┐
│              应用层 (Application Layer)               │
│  - 业务逻辑 (Controllers)                             │
│  - 服务层 (Services)                                  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┼───────────────────────────────────┐
│              框架层 (Framework Layer)                 │
│  ┌──────────────┴──────────────┐                     │
│  │    扩展机制                  │                     │
│  │  - Middleware               │                     │
│  │  - Extension Points         │                     │
│  └──────────────┬──────────────┘                     │
│  ┌──────────────┴──────────────┐                     │
│  │    IoC/DI 2.0 容器           │                     │
│  │  - ApplicationContext       │                     │
│  │  - Definition + Factory     │                     │
│  │  - ScopeManager             │                     │
│  │  - 结构化诊断               │                     │
│  └──────────────┬──────────────┘                     │
│  ┌──────────────┴──────────────┐                     │
│  │    核心基础                  │                     │
│  │  - Lifecycle Management     │                     │
│  │  - Request Context          │                     │
│  │  - Module Scanner           │                     │
│  └─────────────────────────────┘                     │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│            Web 服务器层 (Tornado)                     │
│  - IOLoop                                            │
│  - HTTP Server                                       │
│  - Request Handler                                   │
└─────────────────────────────────────────────────────┘
```

---

## 核心组件 {#core-components}

### 1. Core 模块 (`cullinan/core/`)

提供框架的基础设施。

**主要组件**：

#### 1.1 IoC/DI 2.0 容器

```
ApplicationContext (单一入口)
    ├── Definition Registry (不可变定义)
    ├── Factory (实例创建)
    └── ScopeManager (作用域管理)
        ├── SingletonScope
        ├── PrototypeScope
        └── RequestScope
```

**核心组件 (v0.90)**：
- **ApplicationContext**：所有容器操作的单一入口
  - `register(Definition)` - 注册依赖定义
  - `get(name)` / `try_get(name)` - 解析依赖
  - `refresh()` - 冻结注册表，初始化 eager bean
  - `shutdown()` - 清理资源

- **Definition**：不可变的依赖定义
  - `name` - 全局唯一标识
  - `factory` - 实例创建函数
  - `scope` - ScopeType（SINGLETON/PROTOTYPE/REQUEST）
  - `source` - 来源描述（用于诊断）

- **Factory**：统一实例创建
  - 通过 Definition.factory 创建实例
  - 委托 ScopeManager 进行缓存

- **ScopeManager**：统一作用域管理
  - `SINGLETON` - 应用级单例（线程安全）
  - `PROTOTYPE` - 每次解析创建新实例
  - `REQUEST` - 请求作用域实例

**新目录结构 (v0.90)**：
```
cullinan/core/
├── container/      # IoC/DI 2.0 API
│   ├── context.py
│   ├── definitions.py
│   ├── factory.py
│   └── scope.py
├── diagnostics/    # 异常 + 渲染
├── lifecycle/      # 生命周期管理
├── request/        # 请求上下文
└── legacy/         # 已弃用的 1.x 组件
```
  - 循环依赖检测

- **ProviderRegistry**：Provider 管理
  - 管理不同类型的 Provider（Instance、Class、Factory、Scoped）
  - 支持单例和瞬时模式

- **ServiceRegistry**：Service 生命周期管理
  - 注册和初始化 `@service` 装饰的类
  - 管理 Service 生命周期钩子
  - 依赖顺序初始化

#### 1.2 生命周期管理

```python
class LifecycleManager:
    - refresh()       # 初始化/启动阶段
    - shutdown()      # 关闭阶段
```

**统一生命周期钩子（v0.92+）**：
- `on_post_construct()` - 依赖注入完成后执行
- `on_startup()` - 应用启动时执行
- `on_shutdown()` - 应用关闭时执行
- `on_pre_destroy()` - 销毁前执行

所有钩子支持异步版本（添加 `_async` 后缀）。

#### 1.3 请求上下文

```python
class RequestContext:
    - request_id: str
    - start_time: float
    - _metadata: Dict (延迟初始化)
    - _cleanup_callbacks: List (延迟初始化)
```

**优化**（v0.81+）：
- 延迟初始化：节省 20-55% 内存
- 性能：初始化从 500ns → 350ns

#### 1.4 Scope 系统

- **SingletonScope**：单例作用域
- **TransientScope**：瞬时作用域（每次新建）
- **RequestScope**：请求作用域
- **自定义 Scope**：支持用户扩展（如 SessionScope）

---

### 2. Service 层 (`cullinan/service/`)

管理应用的业务服务。

**使用方式**：
```python
from cullinan.service import service, Service
from cullinan.core import Inject

@service
class UserService(Service):
    email_service: 'EmailService' = Inject()
    
    def on_startup(self):
        # 初始化资源
        self.db = connect_database()
    
    def on_shutdown(self):
        # 清理资源
        self.db.close()
```

**特性**：
- 单例模式（应用级）
- 自动依赖注入
- 生命周期管理
- 启动错误策略（strict/warn/ignore）

---

### 3. Controller 层 (`cullinan/controller/`)

处理 HTTP 请求。

**使用方式**：
```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject
from cullinan.params import Path

@controller(url='/api/users')
class UserController:
    user_service: 'UserService' = Inject()
    
    @get_api(url='/{user_id}')
    async def get_user(self, user_id: int = Path()):
        return self.user_service.get_user(user_id)
```

**特性**：
- RESTful 路由映射
- 自动依赖注入
- 请求级实例（每个请求新建）
- 参数自动解析和验证

---

### 4. 参数系统 (`cullinan/params/`, `cullinan/codec/`) - v0.90 新增

类型安全的参数处理，支持自动转换和校验。

**模块结构**：
```
cullinan/
├── codec/           # 编解码层
│   ├── base.py     # BodyCodec / ResponseCodec 抽象
│   ├── errors.py   # DecodeError / EncodeError
│   ├── json_codec.py
│   ├── form_codec.py
│   └── registry.py # CodecRegistry
├── params/          # 参数处理层
│   ├── base.py     # Param 基类 + UNSET
│   ├── types.py    # Path/Query/Body/Header/File
│   ├── converter.py # TypeConverter
│   ├── auto.py     # Auto 类型推断
│   ├── dynamic.py  # DynamicBody
│   ├── validator.py # ParamValidator
│   ├── model.py    # ModelResolver (dataclass)
│   └── resolver.py # ParamResolver
└── middleware/
    └── body_decoder.py # BodyDecoderMiddleware
```

**使用方式**：
```python
from cullinan.params import Path, Query, Body, DynamicBody

@controller(url='/api/users')
class UserController:
    @get_api(url='/{id}')
    async def get_user(
        self,
        id: int = Path(),
        include_posts: bool = Query(default=False),
    ):
        return {"id": id}
    
    @post_api(url='/')
    async def create_user(
        self,
        name: str = Body(required=True),
        age: int = Body(default=0, ge=0, le=150),
    ):
        return {"name": name, "age": age}
```

**特性**：
- 类型安全的参数声明
- 自动类型转换
- 内置校验器 (ge, le, regex 等)
- dataclass 和 DynamicBody 支持
- 自定义 Codec 注册

详见 [参数系统指南](parameter_system_guide.md)。

---

### 5. 扩展机制

#### 5.1 中间件系统

```python
from cullinan.middleware import middleware, Middleware

@middleware(priority=100)
class LoggingMiddleware(Middleware):
    def process_request(self, handler):
        logger.info(f"Request: {handler.request.uri}")
        return handler
    
    def process_response(self, handler, response):
        logger.info(f"Response: {response}")
        return response
```

**特性**：
- 装饰器驱动注册
- 优先级控制（数字越小越先执行）
- 请求/响应双向拦截
- 支持短路（返回 None 停止后续处理）

#### 5.2 扩展点发现

```python
from cullinan.extensions import list_extension_points

# 查询可用扩展点
points = list_extension_points(category='middleware')
for point in points:
    print(f"{point['name']}: {point['description']}")
```

**6 大类扩展点**：
1. **Middleware** - 请求/响应拦截
2. **Lifecycle** - 生命周期钩子
3. **Injection** - 依赖注入扩展
4. **Routing** - 路由处理
5. **Configuration** - 配置管理
6. **Handler** - 请求处理器

---

## IoC/DI 2.0 系统 {#iocdi-20}

### 新架构 (v0.90)

```
┌─────────────────────────────────────┐
│   ApplicationContext (单一入口)      │
│  - register(Definition)             │
│  - get(name) / try_get(name)        │
│  - refresh() / shutdown()           │
└───────────────┬─────────────────────┘
                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼
┌──────────┐ ┌─────────┐ ┌────────────┐
│Definition│ │ Factory │ │ScopeManager│
│ Registry │ │         │ │            │
└──────────┘ └─────────┘ └────────────┘
```

### 关键改进

| 特性 | 0.83 (Legacy) | 0.90 (0.93) |
|------|---------------|------------|
| 入口点 | 多个 (IoCFacade, Registries) | 单一 (ApplicationContext) |
| 定义 | 可变 | 不可变（冻结） |
| 注册表 | 运行时可修改 | refresh() 后冻结 |
| 作用域 | 隐式 | 显式 ScopeType 枚举 |
| 诊断 | 字符串错误 | 结构化异常 |

### 使用方式

#### 方式 1：基于装饰器的自动注入（推荐）

```python
from cullinan.service import service, Service
from cullinan.core import Inject

@service
class UserService(Service):
    email_service: EmailService = Inject()  # 自动注入
    
    def on_post_construct(self):
        # 依赖注入完成后执行
        pass
    
    def on_startup(self):
        # 应用启动时执行
        pass
```

**特性**：
- 装饰器内部使用新版 IoC/DI 2.0 注册逻辑
- 自动管理依赖解析和生命周期
- 支持 `Inject()` 属性注入

#### 方式 2：基于 Definition 的注册（高级用法）

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

ctx = ApplicationContext()

# 使用显式定义注册（适用于复杂场景或第三方库集成）
ctx.register(Definition(
    name='UserService',
    factory=lambda c: UserService(c.get('UserRepository')),
    scope=ScopeType.SINGLETON,
    source='service:UserService'
))

ctx.refresh()  # 冻结注册表
user_service = ctx.get('UserService')
```

**适用场景**：
- 需要自定义实例创建逻辑
- 集成第三方库组件
- 需要动态注册依赖

---

## 扩展机制 {#extensions}

### 中间件执行流程

```
客户端请求
  ↓
CorsMiddleware (priority=10)      → process_request
  ↓
AuthMiddleware (priority=50)      → process_request
  ↓
LoggingMiddleware (priority=100)  → process_request
  ↓
Handler 处理
  ↓
LoggingMiddleware (priority=100)  → process_response
  ↓
AuthMiddleware (priority=50)      → process_response
  ↓
CorsMiddleware (priority=10)      → process_response
  ↓
客户端响应
```

**优先级规范**：
- `0-50`：关键中间件（CORS、安全）
- `51-100`：标准中间件（日志、指标）
- `101-200`：应用特定中间件

---

## 启动流程 {#startup-flow}

### 启动序列图

```
1. configure(...)
   └── 加载配置

2. 模块扫描
   ├── 自动扫描模式
   │   ├── 检测打包环境（development/nuitka/pyinstaller）
   │   ├── 扫描用户包（user_packages）
   │   └── 收集统计信息（新增 v0.81+）
   │
   └── 显式注册模式（新增 v0.81+）
       └── 跳过扫描，直接使用配置的类

3. IoC 容器初始化
   ├── 初始化 IoCFacade
   ├── 注册 Provider
   └── 配置 InjectionRegistry

4. Service 初始化
   ├── 按依赖顺序初始化
   ├── 调用 on_post_construct() 钩子
   ├── 调用 on_startup() 钩子
   └── 错误处理（根据 startup_error_policy）

5. Controller 注册
   ├── 注册路由
   └── 配置 Handler

6. 中间件链构建
   ├── 按优先级排序
   ├── 初始化中间件（on_startup）
   └── 构建处理链

7. 启动 Web 服务器
   ├── 创建 Tornado Application
   ├── 注册信号处理器（SIGINT/SIGTERM）
   └── 启动 IOLoop
```

### 启动性能（v0.81+ 优化后）

| 场景 | 优化前 | 优化后 | 提升 |
|-----|-------|-------|------|
| 显式注册模式 | 69.56 ms | 0.08 ms | **902x** |
| 小型项目（10模块） | 50-100 ms | 50-100 ms | - |
| 中型项目（50模块） | 300-800 ms | 150-300 ms | **2x** |

---

## 请求处理流程 {#request-flow}

```
1. 请求到达 Tornado
   └── IOLoop 分发到 Handler

2. 创建请求上下文
   ├── RequestContext.create()
   ├── 设置 request_id
   └── 初始化请求级 Scope

3. 中间件处理（请求阶段）
   ├── 按优先级执行 process_request()
   ├── 可能短路返回（如认证失败）
   └── 传递到下一个中间件

4. Controller 实例化
   ├── 创建 Controller 实例
   ├── 注入依赖（通过 InjectionRegistry）
   └── 解析请求参数

5. 执行业务逻辑
   ├── 调用 Controller 方法
   ├── Service 层处理
   └── 返回响应

6. 中间件处理（响应阶段）
   ├── 逆序执行 process_response()
   ├── 可以修改响应
   └── 添加响应头

7. 清理请求上下文
   ├── 执行 cleanup callbacks
   ├── 清除请求级依赖
   └── 销毁 RequestContext

8. 返回响应给客户端
```

---

## 模块扫描机制 {#module-scanning}

### 扫描策略（多环境支持）

```
┌─────────────────────────────────────┐
│      检测打包环境                     │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┬─────────┬─────────┐
     ▼           ▼         ▼         ▼
Development  Nuitka   PyInstaller  其他
     │           │         │         │
     ▼           ▼         ▼         ▼
  标准扫描   sys.modules  _MEIPASS  Fallback
```

### 扫描统计（新增 v0.81+）

```python
from cullinan.scan_stats import get_scan_stats_collector

collector = get_scan_stats_collector()
stats = collector.get_aggregate_stats()

# 输出：
# {
#   'total_scans': 1,
#   'avg_duration_ms': 66.06,
#   'total_modules': 35,
#   'fastest_scan_ms': 66.06,
#   'slowest_scan_ms': 66.06
# }
```

**收集的指标**：
- 总耗时（分阶段）
- 模块数量（发现/过滤/缓存）
- 扫描模式（auto/explicit/cached）
- 打包环境（development/nuitka/pyinstaller）
- 错误记录

---

## 性能优化 {#performance}

### 已实施的优化（v0.81+）

| 优化项 | 优化前 | 优化后 | 提升 |
|-------|-------|-------|------|
| **模块扫描（显式）** | 69.56 ms | 0.08 ms | **902x** |
| **RequestContext 初始化** | 500 ns | 350 ns | **30%** |
| **RequestContext 内存** | 536 B | 240 B | **55%** |
| **依赖解析（缓存）** | - | 0.26 μs | **极快** |
| **日志开销（生产）** | 150 ns | 100 ns | **33%** |

### 优化策略

#### 1. 显式注册模式

```python
from cullinan import configure

configure(
    explicit_services=[DatabaseService, CacheService],
    explicit_controllers=[UserController, AdminController],
    auto_scan=False  # 跳过扫描
)
```

**收益**：启动速度提升 902 倍（测试场景）

#### 2. 延迟初始化

- RequestContext 字段按需创建
- 降低内存占用 55%

#### 3. 智能缓存

- 模块扫描结果缓存
- IoC 依赖解析缓存（0.26 μs）
- Provider 实例缓存

#### 4. 结构化日志

- 生产环境日志优化
- 惰性求值减少开销

---

## 配置选项

### 核心配置

```python
from cullinan import configure

configure(
    # 基础配置
    port=8080,
    debug=True,
    
    # 性能优化
    explicit_services=[...],      # 显式服务注册
    explicit_controllers=[...],   # 显式控制器注册
    auto_scan=False,              # 禁用自动扫描
    user_packages=['myapp'],      # 限制扫描范围
    
    # 启动行为
    startup_error_policy='strict', # 'strict'/'warn'/'ignore'
    
    # 扩展配置
    middlewares=[...],            # 自定义中间件
    handlers=[...],               # 自定义 Handler
)
```

---

## 最佳实践

### 1. 依赖注入

✅ **推荐**：使用类型注入
```python
@service
class UserService(Service):
    email_service: EmailService = Inject()
```

❌ **避免**：手动获取依赖
```python
# 不推荐
registry = get_service_registry()
email_service = registry.get_instance('EmailService')
```

### 2. 性能优化

✅ **推荐**：使用显式注册（大型项目）
```python
configure(
    explicit_services=[...],
    explicit_controllers=[...],
    auto_scan=False
)
```

✅ **推荐**：限制扫描范围
```python
configure(
    user_packages=['myapp', 'myapp.extensions'],
    exclude_packages=['tests', '__pycache__']
)
```

### 3. 中间件设计

✅ **推荐**：单一职责
```python
@middleware(priority=50)
class AuthMiddleware(Middleware):  # 只处理认证
    pass

@middleware(priority=60)
class RoleMiddleware(Middleware):  # 只处理权限
    pass
```

❌ **避免**：职责混杂
```python
@middleware(priority=50)
class AuthAndLoggingMiddleware(Middleware):  # 混杂
    pass
```

---

## 参考资料

- [扩展开发指南](./extension_development_guide.md)
- [API 参考文档](./api_reference.md)
- [快速开始](./getting_started.md)
- [迁移指南](./migration_guide.md)

---

## 从 0.83 迁移 {#migration}

关于从 0.83 版本迁移到 0.90 的详细信息，请参阅 [导入迁移指南](./import_migration_090.md)。

主要变更：
- `cullinan.core.application_context` → `cullinan.core.container`
- `cullinan.core.definitions` → `cullinan.core.container`
- `cullinan.core.exceptions` → `cullinan.core.diagnostics`
- `cullinan.core.context` → `cullinan.core.request`
- 遗留组件移至 `cullinan.core.legacy/`

---

**版本**：v0.90  
**作者**：Plumeink  
**最后更新**：2025-12-25

