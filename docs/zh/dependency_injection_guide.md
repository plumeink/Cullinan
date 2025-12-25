# Cullinan 依赖注入系统指南

> **版本**: v0.9  
> **作者**: Plumeink  
> **最后更新**: 2025-12-24

---

## 概述

Cullinan 提供了一个强大的依赖注入（DI）系统，支持多种注入方式，并在 v0.9 中引入了统一的注入模型。本指南将帮助您理解和使用这些功能。

## 目录

1. [基础概念](#basics)
2. [三种注入方式](#three-injection-methods)
3. [统一注入模型](#unified-model)
4. [高级特性](#advanced-features)
5. [最佳实践](#best-practices)
6. [迁移指南](#migration-guide)

---

## 基础概念 {#basics}

### 什么是依赖注入？

依赖注入是一种设计模式，用于实现控制反转（IoC）。简单来说，就是让框架自动为您的类注入所需的依赖，而不是在类内部手动创建。

### 为什么使用依赖注入？

✅ **松耦合**：类之间的依赖关系更清晰  
✅ **易测试**：可以轻松替换依赖进行单元测试  
✅ **易维护**：依赖关系集中管理  
✅ **可扩展**：轻松添加新的服务和组件

---

## 三种注入方式 {#three-injection-methods}

Cullinan 支持三种依赖注入方式，它们都已统一到新的注入模型中。

### 1. Inject() - 类型注解注入

**推荐指数**: ⭐⭐⭐⭐⭐

使用类型注解的方式，提供最佳的 IDE 支持和类型安全。

```python
from cullinan.core import Inject
from cullinan.service import service

@service
class DatabaseService:
    def query(self, sql: str):
        return f"Result: {sql}"

@service
class UserService:
    # 使用类型注解 + Inject()
    database: DatabaseService = Inject()
    
    def get_user(self, user_id: int):
        return self.database.query(f"SELECT * FROM users WHERE id={user_id}")
```

**特点**：
- ✅ IDE 自动补全
- ✅ 类型检查
- ✅ 自动推断依赖名称
- ✅ 支持可选依赖

**可选依赖**：
```python
class UserService:
    database: DatabaseService = Inject()
    cache: CacheService = Inject(required=False)  # 可选依赖
    
    def get_user(self, user_id: int):
        # cache 可能为 None
        if self.cache:
            return self.cache.get(f"user_{user_id}")
        return self.database.query(...)
```

### 2. InjectByName() - 字符串名称注入

**推荐指数**: ⭐⭐⭐⭐

使用字符串名称的方式，完全无需 import 依赖类。

```python
from cullinan.core import InjectByName

class UserController:
    # 显式指定名称
    user_service = InjectByName('UserService')
    
    # 自动推断名称（email_service → EmailService）
    email_service = InjectByName()
    
    def get_user(self, user_id: int):
        return self.user_service.get_user(user_id)
```

**特点**：
- ✅ 无需 import 依赖类
- ✅ 避免循环导入
- ✅ 自动名称推断（snake_case → PascalCase）
- ✅ 支持可选依赖

**自动名称推断规则**：
```python
user_service = InjectByName()  # → UserService
email_service = InjectByName()  # → EmailService
cache_manager = InjectByName()  # → CacheManager
```

### 3. @injectable - 装饰器批量注入

**推荐指数**: ⭐⭐⭐⭐⭐

使用装饰器的方式，在类实例化时自动注入所有依赖。

```python
from cullinan.core import injectable, Inject, InjectByName

@injectable
class UserController:
    database: DatabaseService = Inject()
    cache = InjectByName('CacheService')
    logger = InjectByName('LogService', required=False)
    
    def __init__(self):
        # __init__ 执行后，所有依赖自动注入
        pass
    
    def get_user(self, user_id: int):
        # 此时 database、cache 已经可用
        result = self.database.query(...)
        if self.cache:
            self.cache.set(f"user_{user_id}", result)
        return result
```

**特点**：
- ✅ 自动批量注入
- ✅ 支持混合使用 Inject 和 InjectByName
- ✅ 在 __init__ 后立即注入
- ✅ 与 @service、@controller 装饰器兼容

---

## 统一注入模型 {#unified-model}

### 新架构概览

从 v0.9 开始，Cullinan 引入了统一的注入模型，所有注入方式都基于相同的底层架构：

```
┌─────────────────────────────────────────┐
│  应用层 (Inject / InjectByName / @injectable) │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  InjectionPoint (统一元信息模型)        │
│  - attr_name: 属性名                    │
│  - dependency_name: 依赖名称            │
│  - required: 是否必需                   │
│  - attr_type: 类型注解                  │
│  - resolve_strategy: 解析策略           │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  InjectionExecutor (统一执行器)         │
│  - resolve_injection_point()            │
│  - inject_instance()                    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  ServiceRegistry / ProviderRegistry     │
│  (服务提供者)                           │
└─────────────────────────────────────────┘
```

### 解析策略

新模型支持三种解析策略：

#### AUTO（自动推断）
```python
# 使用 Inject() 时的默认策略
user_service: UserService = Inject()
# 策略：优先按类型（UserService），回退到名称（'UserService'）
```

#### BY_TYPE（按类型）
```python
# 强制按类型解析
user_service: UserService = Inject()
# 只会查找类型为 UserService 的服务
```

#### BY_NAME（按名称）
```python
# 使用 InjectByName 时的策略
user_service = InjectByName('UserService')
# 只会查找名称为 'UserService' 的服务
```

### 性能特性

新的统一模型提供了出色的性能：

- **缓存机制**：注入后的依赖会缓存到实例，避免重复解析
- **延迟注入**：只在首次访问时才解析依赖
- **批量注入**：@injectable 一次性注入所有依赖，减少开销

---

## 高级特性 {#advanced-features}

### 1. 嵌套依赖

服务可以依赖其他服务，形成依赖链：

```python
@service
class DatabaseService:
    pass

@service
class CacheService:
    pass

@service
@injectable
class DataAccessLayer:
    database: DatabaseService = Inject()
    cache: CacheService = Inject()
    
    def fetch(self, key):
        # 先查缓存
        if self.cache:
            return self.cache.get(key)
        # 再查数据库
        return self.database.query(...)

@injectable
class BusinessLogic:
    dal: DataAccessLayer = Inject()
    
    def process(self, key):
        return self.dal.fetch(key)
```

### 2. 循环依赖检测

框架会自动检测并阻止循环依赖：

```python
@service
@injectable
class ServiceA:
    b: ServiceB = Inject()

@service
@injectable
class ServiceB:
    a: ServiceA = Inject()  # ❌ 会抛出 CircularDependencyError
```

**解决方案**：
1. 重新设计依赖关系
2. 使用延迟注入
3. 引入中间层打破循环

### 3. 字符串注解支持

支持使用字符串类型注解（避免循环导入）：

```python
from __future__ import annotations

@injectable
class UserController:
    # 使用字符串注解（Python 3.7+）
    user_service: 'UserService' = Inject()
```

### 4. 测试 Mock

所有注入方式都支持手动设置（便于测试）：

```python
def test_user_controller():
    controller = UserController()
    
    # 手动注入 Mock 对象
    controller.user_service = MockUserService()
    
    # 测试业务逻辑
    result = controller.get_user(123)
    assert result == expected_value
```

---

## 最佳实践 {#best-practices}

### ✅ 推荐做法

#### 1. 优先使用 Inject() + 类型注解
```python
@injectable
class UserService:
    database: DatabaseService = Inject()  # ✅ 推荐
    cache: CacheService = Inject()
```

#### 2. 明确标记可选依赖
```python
class UserService:
    database: DatabaseService = Inject()  # 必需
    cache: CacheService = Inject(required=False)  # 可选
```

#### 3. 使用 @injectable 简化注入
```python
@injectable
class UserController:
    user_service: UserService = Inject()
    # 自动注入，无需手动调用
```

#### 4. 服务类使用 @service 装饰器
```python
@service  # 自动注册到 ServiceRegistry
@injectable  # 支持依赖注入
class UserService:
    database: DatabaseService = Inject()
```

### ❌ 避免做法

#### 1. 避免在构造函数中访问依赖
```python
@injectable
class UserService:
    database: DatabaseService = Inject()
    
    def __init__(self):
        # ❌ 此时 database 还未注入
        # self.database.query(...)  
        pass
    
    def get_user(self, user_id):
        # ✅ 此时可以安全访问
        return self.database.query(...)
```

#### 2. 避免循环依赖
```python
# ❌ 错误：循环依赖
@service
class ServiceA:
    b: ServiceB = Inject()

@service
class ServiceB:
    a: ServiceA = Inject()
```

#### 3. 避免过度使用 InjectByName
```python
# ❌ 不推荐：失去类型安全
user_service = InjectByName('UserService')

# ✅ 推荐：有类型检��
user_service: UserService = Inject()
```

---

## 迁移指南 {#migration-guide}

### 从旧代码迁移

如果您的代码使用了旧的注入方式，**无需修改**！新的统一模型完全向后兼容。

#### 旧代码继续工作
```python
# 旧代码 - 仍然工作
@injectable
class UserService:
    database: DatabaseService = Inject()

# 新代码 - 完全相同的语法
@injectable
class UserService:
    database: DatabaseService = Inject()
```

#### 向后兼容机制

框架内部使用了向后兼容机制：
1. **优先尝试新模型**（InjectionExecutor）
2. **失败时自动回退**到旧逻辑（registry.inject()）
3. **完全透明**，用户无感知

这些向后兼容代码在源码中标记为：
```python
# BACKWARD_COMPAT: v0.8 - 保留旧的注入逻辑
# 计划移除版本：v1.0
```

### 升级建议

虽然旧代码继续工作，但建议：

1. **新项目**：直接使用新的推荐模式
2. **现有项目**：逐步迁移，无需急于一次性改完
3. **关注性能**：新模型在大多数场景下性能更优

---

## 常见问题

### Q: 三种注入方式应该用哪个？

**A**: 推荐顺序：
1. **Inject() + 类型注解**：最推荐，类型安全
2. **@injectable + 混合使用**：简化代码
3. **InjectByName**：避免循环导入时使用

### Q: 什么时候依赖会被注入？

**A**: 
- **Inject/InjectByName**：首次访问属性时（延迟注入）
- **@injectable**：__init__ 方法执行后（批量注入）

### Q: 如何处理可选依赖？

**A**: 
```python
cache: CacheService = Inject(required=False)

if self.cache:  # 检查是否为 None
    self.cache.set(key, value)
```

### Q: 如何避免循环依赖？

**A**:
1. 重新设计依赖关系
2. 使用事件系统解耦
3. 引入中间层/Facade

### Q: 性能如何？

**A**: 新模型性能优异：
- 缓存命中：< 1 μs
- 首次解析：10-50 μs
- 与旧模型相当或更优

---

## 完整示例

### 示例 1：简单的三层架构

```python
from cullinan.core import Inject, injectable
from cullinan.service import service

# 数据访问层
@service
class DatabaseService:
    def query(self, sql: str):
        return f"Query result: {sql}"

# 业务逻辑层
@service
@injectable
class UserService:
    database: DatabaseService = Inject()
    
    def get_user(self, user_id: int):
        return self.database.query(
            f"SELECT * FROM users WHERE id={user_id}"
        )
    
    def create_user(self, username: str):
        return self.database.query(
            f"INSERT INTO users (username) VALUES ('{username}')"
        )

# 控制器层
@injectable
class UserController:
    user_service: UserService = Inject()
    
    def get(self, user_id: int):
        return self.user_service.get_user(user_id)
    
    def post(self, username: str):
        return self.user_service.create_user(username)
```

### 示例 2：带缓存的复杂场景

```python
from cullinan.core import Inject, InjectByName, injectable
from cullinan.service import service

@service
class CacheService:
    def get(self, key): pass
    def set(self, key, value): pass

@service
class LogService:
    def log(self, message): pass

@service
@injectable
class UserService:
    database: DatabaseService = Inject()
    cache: CacheService = Inject(required=False)
    logger = InjectByName('LogService', required=False)
    
    def get_user(self, user_id: int):
        # 尝试从缓存获取
        if self.cache:
            cached = self.cache.get(f"user_{user_id}")
            if cached:
                if self.logger:
                    self.logger.log(f"Cache hit: user_{user_id}")
                return cached
        
        # 从数据库查询
        result = self.database.query(
            f"SELECT * FROM users WHERE id={user_id}"
        )
        
        # 写入缓存
        if self.cache:
            self.cache.set(f"user_{user_id}", result)
        
        return result
```

---

## 参考资料

- [架构文档](./architecture_updated.md)
- [扩展开发指南](./extension_development_guide.md)
- [API 参考](./api_reference.md)

---

**更新日志**:
- 2025-12-24: 创建文档，覆盖 v0.9 统一注入模型
- 未来：持续更新最佳实践和示例

