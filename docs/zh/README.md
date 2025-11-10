# Cullinan v0.71a1 架构文档

**[English](../README.md)** | [中文](README.md)

**状态**: ✅ 已实现  
**版本**: 0.71a1  
**日期**: 2025年11月10日

---

## 📌 文档状态

所有规划和分析文档已经**整合**到一个主文档中：

## **[ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)** 📖

这个综合文档包含：

1. **执行摘要** - 构建内容和关键决策
2. **服务层分析** - 为什么保留和增强服务层
3. **注册表模式评估** - 统一注册表设计
4. **核心模块设计** - 架构概览和组件
5. **实现细节** - 一切如何工作
6. **测试策略** - 单元和集成测试
7. **迁移指南** - 从 v0.6.x 升级到 v0.71a1
8. **未来路线图** - 未来版本和 v1.0.0 的计划

---

## 实现完成 ✅

v0.71a1 架构已经**完全实现**：

| 组件 | 状态 | 位置 |
|-----------|--------|----------|
| **核心模块** | ✅ 完成 | `cullinan/core/` |
| - 注册表模式 | ✅ | `core/registry.py` |
| - 依赖注入 | ✅ | `core/injection.py` |
| - 生命周期管理 | ✅ | `core/lifecycle.py` |
| - 请求上下文 | ✅ | `core/context.py` |
| **服务层** | ✅ 完成 | `cullinan/service/` |
| - 增强服务 | ✅ | `service/base.py` |
| - 服务注册表 | ✅ | `service/registry.py` |
| - @service 装饰器 | ✅ | `service/decorators.py` |
| **WebSocket** | ✅ 完成 | `cullinan/websocket_registry.py` |
| - WebSocket注册表 | ✅ | `websocket_registry.py` |
| - @websocket_handler | ✅ | `websocket_registry.py` |
| **测试** | ✅ 完成 | `cullinan/testing/` |
| - 测试注册表 | ✅ | `testing/registry.py` |
| - 模拟服务 | ✅ | `testing/mocks.py` |
| **文档** | ✅ 完成 | 多个位置 |
| - 主 README | ✅ | `README.MD` |
| - CHANGELOG | ✅ | `CHANGELOG.md` |
| - 文档索引 | ✅ | `docs/zh/README.md` |
| **示例** | ✅ 完成 | `examples/` |
| - v0.71a1 演示 | ✅ | `examples/v070_demo.py` |

---

## 快速开始

### 对于用户

想要使用 v0.71a1？查看这些资源：

1. **[主 README](../../README.MD)** - 概览和快速入门
2. **[v0.71a1 演示](../../examples/v070_demo.py)** - 综合示例
3. **[CHANGELOG](../../CHANGELOG.md)** - 从 v0.6.x 的迁移指南
4. **[文档索引](README.md)** - 完整文档

### 对于开发者

想要了解架构？

1. **[ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)** - 完整设计文档
2. **源代码**:
   - `cullinan/core/` - 核心组件
   - `cullinan/service/` - 服务层
   - `cullinan/websocket_registry.py` - WebSocket 集成
3. **[测试指南](ARCHITECTURE_MASTER.md#测试策略)** - 如何测试

---

## 主要特性

### 带依赖注入的服务层

```python
from cullinan import service, Service

@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name, email):
        user = {'name': name, 'email': email}
        self.email.send_welcome(email)
        return user
```

### 带注册表集成的 WebSocket

```python
from cullinan import websocket_handler

@websocket_handler(url='/ws/chat')
class ChatHandler:
    def on_init(self):
        self.connections = set()
    
    def on_open(self):
        self.connections.add(self)
    
    def on_message(self, message):
        for conn in self.connections:
            conn.write_message(message)
```

### 请求上下文管理

```python
from cullinan import create_context, get_current_context

with create_context():
    ctx = get_current_context()
    ctx.set('user_id', 123)
    ctx.set('request_id', 'abc-123')
    # 上下文自动清理
```

---

## 历史文档（已归档）

以下规划文档已整合到 ARCHITECTURE_MASTER.md：

- `01-service-layer-analysis.md` - 服务层价值分析
- `02-registry-pattern-evaluation.md` - 注册表模式评估
- `03-architecture-comparison.md` - 框架比较
- `04-core-module-design.md` - 核心模块规范
- `05-implementation-plan.md` - 实现路线图
- `06-migration-guide.md` - 迁移说明
- `07-api-specifications.md` - API 参考
- `08-testing-strategy.md` - 测试方法
- `09-code-examples.md` - 代码示例
- `10-backward-compatibility.md` - 兼容性分析

这些文件保留作为历史参考，但不再积极维护。

---

## 规划发生了什么变化？

实现紧密遵循原始计划，并进行了以下改进：

| 方面 | 计划 | 实现 | 备注 |
|--------|---------|-------------|-------|
| 核心模块 | ✅ | ✅ | 按设计实现 |
| 服务 DI | ✅ | ✅ | 按设计实现 |
| 生命周期钩子 | ✅ | ✅ | 按设计实现 |
| 请求上下文 | ✅ | ✅ | 按设计实现 |
| WebSocket | ✅ | ✅ | 增强了生命周期 |
| 测试 | ✅ | ✅ | 按设计实现 |
| 版本 | 0.8.0 | 0.71a1 | 为清晰起见而更改 |

---

## 从 v0.6.x 迁移

详细说明请参见 [CHANGELOG 迁移指南](../../CHANGELOG.md#迁移指南)。

**快速摘要**：

```python
# 旧版本 (v0.6.x)
from cullinan.service import service, Service

# 新版本 (v0.71a1)
from cullinan import service, Service

# 可用的新功能：
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        # 生命周期钩子
        pass
```

---

## 未来路线图

详情请参见 [ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md#未来路线图)。

**短期 (v0.7.x)**：
- 额外的生命周期钩子
- 性能优化
- 更多中间件

**中期 (v0.8.0)**：
- 移除已弃用的模块
- 高级作用域
- 服务网格集成

**长期 (v1.0.0)**：
- 稳定的 API 保证
- 完全 async/await
- 云原生功能

---

## 资源

- **架构**: [ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)
- **摘要**: [SUMMARY.md](SUMMARY.md)
- **主文档**: [README.md](README.md)
- **示例**: [../../examples/](../../examples/)
- **源代码**: [../../cullinan/](../../cullinan/)

---

**最后更新**: 2025年11月10日  
**状态**: 实现完成  
**维护者**: Cullinan 开发团队
