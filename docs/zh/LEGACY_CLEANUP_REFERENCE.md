# 旧代码清理 - 快速参考

## 变更内容

### 🗑️ 已删除：`cullinan/hooks.py`

旧的 `hooks.py` 文件已被**删除**。它只包含 `MissingHeaderHandlerHook` 类，这是v0.6x的遗留代码。

### ✅ 与 `cullinan/monitoring/hooks.py` 无混淆

这是**两个完全不同的文件**，用途不同：

| 文件 | 用途 | 状态 |
|------|------|------|
| ❌ `cullinan/hooks.py` | 简单的缺失头钩子（v0.6x遗留） | **已删除** |
| ✅ `cullinan/monitoring/hooks.py` | 监控系统（`MonitoringHook` 和 `MonitoringManager`，v0.7x） | **活跃** |

## 迁移路径

### 如果您使用了 `MissingHeaderHandlerHook`：

**之前：**
```python
from cullinan.hooks import MissingHeaderHandlerHook

def my_handler(request, header_name):
    print(f"缺失头: {header_name}")

MissingHeaderHandlerHook.set_hook(my_handler)
```

**现在：**
```python
from cullinan import set_missing_header_handler

def my_handler(request, header_name):
    print(f"缺失头: {header_name}")

set_missing_header_handler(my_handler)
```

### 新的API函数

```python
from cullinan import (
    set_missing_header_handler,  # 设置自定义处理器
    get_missing_header_handler,  # 获取当前处理器
)

# 设置自定义处理器
def custom_handler(request, header_name):
    # 您的自定义逻辑
    pass

set_missing_header_handler(custom_handler)

# 获取当前处理器（测试时有用）
handler = get_missing_header_handler()
```

## 已彻底删除的模块

在最新版本中，以下两个弃用模块已被**彻底删除**：

### 1. `cullinan/registry.py` - ❌ 已删除

**不再可用：**
```python
from cullinan.registry import HandlerRegistry  # ❌ ImportError
```

**使用新导入：**
```python
from cullinan.handler import HandlerRegistry  # ✅ 正确
# 或
from cullinan import HandlerRegistry  # ✅ 推荐
```

### 2. `cullinan/websocket.py` - ❌ 已删除

**不再可用：**
```python
from cullinan.websocket import websocket  # ❌ ImportError

@websocket(url='/ws/chat')
class ChatHandler:
    pass
```

**使用新导入：**
```python
from cullinan import websocket_handler  # ✅ 推荐

@websocket_handler(url='/ws/chat')
class ChatHandler:
    pass
```

## 为什么做这些变更？

1. **更清晰的架构**：功能移至适当的模块
2. **减少混淆**：清楚区分旧的和新的监控系统
3. **更好的组织**：相关代码组织在一起
4. **简化维护**：移除了冗余的转发层

## 时间线

- **v0.7x初期**：旧代码已删除，弃用模块显示警告
- **v0.7x当前**：弃用模块已彻底删除
- **v0.8x (未来)**：继续完善架构

## 需要帮助？

- 查看完整细节：[完整技术报告](../彻底删除弃用文件完成报告.md)
- 迁移指南：[API迁移指南](API_MIGRATION_GUIDE.md)
- 架构概览：[架构主文档](ARCHITECTURE_MASTER.md)
- 英文版本：[English Version](../LEGACY_CLEANUP_REFERENCE.md)

