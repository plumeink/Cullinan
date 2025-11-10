# Cullinan v0.7x - API迁移完全指南

**版本**: v0.7x (弃用模块已删除)  
**日期**: 2025年11月11日  
**重要性**: ⚠️ **破坏性变更** - 必须更新代码

---

## 🚨 重要通知

Cullinan v0.7x已**彻底删除**以下弃用模块：
- ❌ `cullinan/registry.py` - 已删除
- ❌ `cullinan/websocket.py` - 已删除

**这是一个破坏性变更**，使用旧导入路径的代码将无法运行。

---

## 📋 快速迁移检查清单

### 步骤1：检查导入
在您的代码中搜索以下导入：
```python
❌ from cullinan.registry import
❌ from cullinan.websocket import
```

### 步骤2：更新导入
按照本指南更新所有导入语句

### 步骤3：运行测试
确保所有功能正常工作

---

## 🔄 详细迁移指南

### 1. HandlerRegistry迁移

#### 旧代码（不再工作）
```python
from cullinan.registry import HandlerRegistry
from cullinan.registry import get_handler_registry
from cullinan.registry import reset_registries
```

#### 新代码（推荐）
```python
# 方式1：从主包导入（推荐）
from cullinan import HandlerRegistry, get_handler_registry

# 方式2：从handler模块导入
from cullinan.handler import HandlerRegistry, get_handler_registry, reset_handler_registry
```

#### 示例
```python
# 旧代码
from cullinan.registry import get_handler_registry

def setup_handlers():
    registry = get_handler_registry()
    registry.register('/api/users', UserHandler)

# 新代码
from cullinan import get_handler_registry

def setup_handlers():
    registry = get_handler_registry()
    registry.register('/api/users', UserHandler)
```

---

### 2. HeaderRegistry迁移

#### 旧代码（不再工作）
```python
from cullinan.registry import HeaderRegistry
from cullinan.registry import get_header_registry
```

#### 新代码（推荐）
```python
# 方式1：从主包导入（推荐）
from cullinan import HeaderRegistry, get_header_registry

# 方式2：从controller模块导入
from cullinan.controller import HeaderRegistry, get_header_registry
```

#### 示例
```python
# 旧代码
from cullinan.registry import get_header_registry

def setup_headers():
    registry = get_header_registry()
    registry.register(('X-Custom-Header', 'value'))

# 新代码
from cullinan import get_header_registry

def setup_headers():
    registry = get_header_registry()
    registry.register(('X-Custom-Header', 'value'))
```

---

### 3. reset_registries()迁移

#### 旧代码（不再工作）
```python
from cullinan.registry import reset_registries

reset_registries()  # 重置所有注册表
```

#### 新代码
```python
from cullinan.handler import reset_handler_registry
from cullinan import get_header_registry

# 分别重置
reset_handler_registry()          # 重置处理器注册表
get_header_registry().clear()     # 清除头注册表
```

#### 测试代码示例
```python
# 旧代码
class TestMyFeature(unittest.TestCase):
    def setUp(self):
        from cullinan.registry import reset_registries
        reset_registries()

# 新代码
class TestMyFeature(unittest.TestCase):
    def setUp(self):
        from cullinan.handler import reset_handler_registry
        from cullinan import get_header_registry
        
        reset_handler_registry()
        get_header_registry().clear()
```

---

### 4. WebSocket装饰器迁移

#### 旧代码（不再工作）
```python
from cullinan.websocket import websocket

@websocket(url='/ws/chat')
class ChatWebSocketHandler:
    def on_open(self):
        print("WebSocket opened")
    
    def on_message(self, message):
        self.write_message(f"Echo: {message}")
    
    def on_close(self):
        print("WebSocket closed")
```

#### 新代码
```python
from cullinan import websocket_handler

@websocket_handler(url='/ws/chat')
class ChatWebSocketHandler:
    def on_open(self):
        print("WebSocket opened")
    
    def on_message(self, message):
        self.write_message(f"Echo: {message}")
    
    def on_close(self):
        print("WebSocket closed")
```

---

## 📦 完整导入映射表

| 旧导入（已删除） | 新导入（推荐） | 备选导入 |
|-----------------|--------------|----------|
| `from cullinan.registry import HandlerRegistry` | `from cullinan import HandlerRegistry` | `from cullinan.handler import HandlerRegistry` |
| `from cullinan.registry import get_handler_registry` | `from cullinan import get_handler_registry` | `from cullinan.handler import get_handler_registry` |
| `from cullinan.registry import reset_registries` | 见上面reset_registries()迁移 | - |
| `from cullinan.registry import HeaderRegistry` | `from cullinan import HeaderRegistry` | `from cullinan.controller import HeaderRegistry` |
| `from cullinan.registry import get_header_registry` | `from cullinan import get_header_registry` | `from cullinan.controller import get_header_registry` |
| `from cullinan.websocket import websocket` | `from cullinan import websocket_handler` | `from cullinan.websocket_registry import websocket_handler` |

---

## 🛠️ 实用工具：批量替换脚本

### 使用sed（Linux/Mac）
```bash
# 替换HandlerRegistry导入
find . -name "*.py" -type f -exec sed -i 's/from cullinan.registry import HandlerRegistry/from cullinan import HandlerRegistry/g' {} \;

# 替换get_handler_registry导入
find . -name "*.py" -type f -exec sed -i 's/from cullinan.registry import get_handler_registry/from cullinan import get_handler_registry/g' {} \;

# 替换websocket导入
find . -name "*.py" -type f -exec sed -i 's/from cullinan.websocket import websocket/from cullinan import websocket_handler/g' {} \;
find . -name "*.py" -type f -exec sed -i 's/@websocket(/@websocket_handler(/g' {} \;
```

### 使用PowerShell（Windows）
```powershell
# 替换HandlerRegistry导入
Get-ChildItem -Path . -Recurse -Filter *.py | ForEach-Object {
    (Get-Content $_.FullName) -replace 'from cullinan.registry import HandlerRegistry', 'from cullinan import HandlerRegistry' | Set-Content $_.FullName
}

# 替换websocket装饰器
Get-ChildItem -Path . -Recurse -Filter *.py | ForEach-Object {
    (Get-Content $_.FullName) -replace 'from cullinan.websocket import websocket', 'from cullinan import websocket_handler' | Set-Content $_.FullName
    (Get-Content $_.FullName) -replace '@websocket\(', '@websocket_handler(' | Set-Content $_.FullName
}
```

---

## 🧪 验证迁移

### 1. 静态检查
```python
# 在Python中检查导入
python -c "from cullinan import HandlerRegistry, get_handler_registry, HeaderRegistry, get_header_registry, websocket_handler; print('✓ 所有导入成功')"
```

### 2. 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 或使用unittest
python -m unittest discover tests/
```

### 3. 检查是否有遗漏
```bash
# 搜索可能的旧导入
grep -r "from cullinan.registry import" .
grep -r "from cullinan.websocket import" .
```

---

## ❓ 常见问题

### Q1: 为什么要删除这些文件？
**A**: 为了保持代码库清晰，减少维护负担。这些文件只是简单的转发层，现在功能已经完全整合到正确的模块中。

### Q2: 有没有办法继续使用旧导入？
**A**: 没有。这是一个破坏性变更，旧导入已经完全移除。必须更新代码。

### Q3: 我的应用会立即崩溃吗？
**A**: 如果您使用了旧的导入路径，更新框架后应用将无法启动（ImportError）。

### Q4: 迁移需要多长时间？
**A**: 通常只需要5-15分钟。主要是查找和替换导入语句。

### Q5: 功能有变化吗？
**A**: 没有。API完全相同，只是导入路径改变了。

### Q6: 我可以同时使用旧版和新版吗？
**A**: 不可以。建议在更新框架前先完成代码迁移，或者在独立环境中测试。

---

## 📚 相关文档

- [彻底删除弃用文件完成报告.md](../彻底删除弃用文件完成报告.md) - 完整的技术报告
- [ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md) - 架构指南
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 原始迁移指南

---

## 🎯 迁移支持

如果在迁移过程中遇到问题：

1. **检查错误信息** - ImportError会明确指出哪个模块不存在
2. **参考本指南** - 所有常见情况都有解决方案
3. **运行测试** - 确保功能正常
4. **查看示例** - 参考`examples/`目录中的代码

---

**最后更新**: 2025-11-11  
**适用版本**: Cullinan v0.7x+  
**状态**: ✅ 官方指南

