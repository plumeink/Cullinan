# Cullinan v0.7x 文档

**[English](../README.md)** | [中文](README.md)

**版本**: 0.7x

---

## 📚 完整架构指南

要获取全面的架构信息、设计决策和实现细节，请参阅：

## **[ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)** 📖

本指南涵盖：

1. **执行摘要** - 概述和关键设计决策
2. **服务层** - 具有依赖注入的增强服务层
3. **注册表模式** - 统一的组件注册
4. **核心模块** - 架构和组件
5. **实现细节** - 各部分如何协同工作
6. **测试策略** - 测试方法和工具
7. **迁移指南** - 从 v0.6x 升级

---

## 🚀 功能概览

v0.7x 架构包括：

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
| - v0.7x 演示 | ✅ | `examples/v070_demo.py` |

---

## 快速开始

### 对于用户

想要使用 v0.7x？查看这些资源：

1. **[主 README](../../README.MD)** - 概述和快速入门
2. **[v0.7x 演示](../../examples/v070_demo.py)** - 综合示例
3. **[迁移指南](MIGRATION_GUIDE.md)** - 从 v0.6x 升级
4. **[API迁移指南](API_MIGRATION_GUIDE.md)** - 完整的API迁移指南 ⚠️ **新增**
5. **[旧代码清理参考](LEGACY_CLEANUP_REFERENCE.md)** - 快速清理参考
6. **[更新日志](../../docs_archive/reports/CHANGELOG.md)** - 版本历史和更改

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

## 从 v0.6x 迁移

详细说明请参见 [迁移指南](MIGRATION_GUIDE.md)。

**快速摘要**：

```python
# 旧版本 (v0.6x)
from cullinan.service import service, Service

# 新版本 (v0.7x)
from cullinan import service, Service

# 可用的新功能：
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        # 生命周期钩子
        pass
```

---

## 资源

- **架构指南**: [ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)
- **迁移指南**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **文档索引**: [README.md](README.md)
- **示例**: [../../examples/](../../examples/)
- **源代码**: [../../cullinan/](../../cullinan/)
- **更新日志**: [../../CHANGELOG.md](../../docs_archive/reports/CHANGELOG.md)

---
**最后更新**: 2025年11月11日  
**最后更新**: 2025年11月10日  
**状态**: 实现完成  
**维护者**: Cullinan 开发团队
