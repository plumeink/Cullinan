# IoC/DI 2.0 架构

> **版本**：v0.90  
> **作者**：Plumeink

> 本文档描述 Cullinan 0.90 引入的全新 IoC/DI 架构。
> 从之前版本迁移请参阅 [导入迁移指南](../import_migration_090.md)。

## 概述

Cullinan 0.90 引入了完全重新设计的 IoC/DI 系统，主要改进包括：

- **单一入口**：`ApplicationContext` 作为唯一容器入口
- **定义/工厂分离**：清晰分离定义与实例创建
- **启动后冻结**：refresh 后注册表冻结，禁止运行期修改
- **作用域合约**：严格的作用域强制（singleton/prototype/request）
- **结构化诊断**：稳定、可复现的错误信息与依赖链路

## 核心组件

### ApplicationContext

所有容器操作的单一入口：

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

# 创建上下文
ctx = ApplicationContext()

# 注册定义
ctx.register(Definition(
    name='UserService',
    factory=lambda c: UserService(c.get('UserRepository')),
    scope=ScopeType.SINGLETON,
    source='service:UserService'
))

# 刷新（冻结注册表，初始化 eager bean）
ctx.refresh()

# 解析依赖
user_service = ctx.get('UserService')

# 关闭
ctx.shutdown()
```

### Definition

不可变的依赖定义（创建后冻结）：

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `name` | `str` | 是 | 全局唯一标识 |
| `factory` | `Callable[[ApplicationContext], Any]` | 是 | 实例创建函数 |
| `scope` | `ScopeType` | 是 | 作用域类型（SINGLETON/PROTOTYPE/REQUEST） |
| `source` | `str` | 是 | 来源描述，用于诊断 |
| `type_` | `type` | 否 | 用于类型推断 |
| `eager` | `bool` | 否 | refresh 时预创建（默认：False） |
| `conditions` | `list[Callable]` | 否 | 条件注册 |
| `dependencies` | `list[str]` | 否 | 显式依赖（用于排序） |
| `optional` | `bool` | 否 | 允许缺失（仅用于 try_get） |

### ScopeType

```python
from cullinan.core.container import ScopeType

ScopeType.SINGLETON   # 应用级单例（线程安全）
ScopeType.PROTOTYPE   # 每次解析创建新实例
ScopeType.REQUEST     # 请求作用域（需要 RequestContext）
```

## 生命周期

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   创建      │────▶│    注册     │────▶│    刷新     │────▶│    使用     │
│   上下文    │     │    定义     │     │  （冻结）   │     │  （解析）   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │    关闭     │
                                        └─────────────┘
```

### 冻结机制

`refresh()` 后：
- 所有定义被冻结
- 禁止新的注册
- 任何修改尝试都会抛出 `RegistryFrozenError`

```python
ctx.refresh()

# 这将抛出 RegistryFrozenError
ctx.register(Definition(...))  # 错误！
```

## Request 作用域

请求作用域依赖需要活动的 `RequestContext`：

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

ctx = ApplicationContext()
ctx.register(Definition(
    name='RequestData',
    factory=lambda c: RequestData(),
    scope=ScopeType.REQUEST,
    source='request:RequestData'
))
ctx.refresh()

# 没有上下文 - 抛出 ScopeNotActiveError
ctx.get('RequestData')  # 错误！

# 有上下文 - 正常工作
ctx.enter_request_context()
try:
    data = ctx.get('RequestData')
finally:
    ctx.exit_request_context()
```

## 错误处理

所有异常都带有结构化诊断字段：

| 异常 | 触发时机 |
|------|----------|
| `RegistryFrozenError` | 冻结后修改 |
| `DependencyNotFoundError` | 依赖缺失 |
| `CircularDependencyError` | 检测到循环引用 |
| `ScopeNotActiveError` | 请求作用域无上下文 |
| `ConditionNotMetError` | 条件检查失败 |
| `CreationError` | 工厂执行失败 |

### 依赖链路

循环依赖错误包含稳定、有序的链路：

```
CircularDependencyError: 检测到循环依赖: ServiceA -> ServiceB -> ServiceC -> ServiceA
```

## 最佳实践

1. **解析前始终调用 `refresh()`**
2. **可选依赖使用 `try_get()`**
3. **使用请求作用域 bean 前进入请求上下文**
4. **注册 shutdown 处理器用于清理**
5. **关键服务使用 `eager=True`**

## 测试

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

def test_my_service():
    ctx = ApplicationContext()
    ctx.register(Definition(
        name='MockRepository',
        factory=lambda c: MockRepository(),
        scope=ScopeType.SINGLETON,
        source='test:MockRepository'
    ))
    ctx.register(Definition(
        name='MyService',
        factory=lambda c: MyService(c.get('MockRepository')),
        scope=ScopeType.SINGLETON,
        source='test:MyService'
    ))
    ctx.refresh()
    
    service = ctx.get('MyService')
    assert service is not None
```

## 相关文档

- [装饰器](decorators.md) - 基于装饰器的组件注册
- [导入迁移指南](../import_migration_090.md)
- [API 参考](../api_reference.md)
- [架构概述](architecture.md)

