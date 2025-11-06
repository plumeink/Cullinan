# 启动方式改进和 sys.path 自动处理

## 问题背景

之前使用 Cullinan 时，当代码放在包内（如 `club/fnep/application.py`）时，需要手动添加：

```python
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')
```

这样做的原因是 Python 需要知道包的根目录在哪里才能正确导入模块和读取环境变量文件。

## 解决方案

现在 `configure()` 函数会**自动检测并添加项目根目录到 sys.path**，无需手动添加！

---

## 新的启动方式（推荐）

### 简化的启动代码

```python
# -*- coding: utf-8 -*-
# club/fnep/application.py

from cullinan import application, configure
from cullinan.hooks import MissingHeaderHandlerHook
from club.fnep.hooks import missing_header_handler

def main():
    # configure 会自动处理 sys.path
    configure(user_packages=['club.fnep'])
    
    # 设置钩子
    MissingHeaderHandlerHook.set_hook(missing_header_handler)
    
    # 启动应用
    application.run()

if __name__ == '__main__':
    main()
```

**不再需要** `sys.path.append(...)` 这一行！

---

## 工作原理

### 自动检测逻辑

`configure()` 函数会根据配置的包名自动检测项目根目录：

1. **获取调用者文件路径**：通过 Python 的 `inspect` 模块获取调用 `configure()` 的文件位置

2. **向上查找包根目录**：
   - 例如配置了 `user_packages=['club.fnep']`
   - 从当前文件位置向上查找包含 `club/` 目录的父目录
   - 最多向上查找 5 级目录

3. **自动添加到 sys.path**：
   - 找到项目根目录后，自动添加到 `sys.path` 的最前面
   - 确保后续的导入操作可以正确找到模块

### 示例

假设项目结构：
```
/home/user/projects/my_discord_bot/
├── club/
│   └── fnep/
│       ├── application.py      # ← 这是启动文件
│       ├── controllers/
│       ├── services/
│       └── hooks.py
├── .env
└── requirements.txt
```

当在 `club/fnep/application.py` 中调用：
```python
configure(user_packages=['club.fnep'])
```

Cullinan 会：
1. 检测到当前文件在 `/home/user/projects/my_discord_bot/club/fnep/`
2. 根据包名 `club.fnep` 知道需要找到包含 `club/` 的父目录
3. 向上查找，找到 `/home/user/projects/my_discord_bot/`
4. 自动将其添加到 `sys.path`

---

## 手动指定项目根目录（可选）

如果自动检测不准确，可以手动指定：

```python
configure(
    user_packages=['club.fnep'],
    project_root='/path/to/project/root'
)
```

---

## 详细输出（调试用）

启用 verbose 模式可以看到 sys.path 的变化：

```python
configure(
    user_packages=['club.fnep'],
    verbose=True
)

# 输出：
# Auto-added project root to sys.path: /home/user/projects/my_discord_bot
```

---

## 对比：旧 vs 新

### 旧方式（繁琐）

```python
import sys
import os

# 需要手动计算路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')

from cullinan import application, configure
from club.fnep.hooks import missing_header_handler

def main():
    configure(user_packages=['club.fnep'])
    application.run()
```

### 新方式（简洁）

```python
from cullinan import application, configure
from club.fnep.hooks import missing_header_handler

def main():
    # configure 自动处理 sys.path
    configure(user_packages=['club.fnep'])
    application.run()
```

---

## 优势

✅ **更简洁**：不需要手动操作 sys.path  
✅ **更安全**：自动计算避免路径错误  
✅ **更智能**：自动适配不同的项目结构  
✅ **向后兼容**：仍然支持手动指定 `project_root`

---

## 注意事项

1. **包名必须准确**：`user_packages` 中的包名要与实际文件结构一致

2. **最多查找 5 级**：如果项目结构嵌套超过 5 级，建议手动指定 `project_root`

3. **开发模式安装**：如果项目以 `pip install -e .` 方式安装，通常不需要担心 sys.path 问题

---

## 示例：完整的启动文件

```python
# -*- coding: utf-8 -*-
"""
Discord Bot Application Entry Point
"""

from cullinan import application, configure
from cullinan.hooks import MissingHeaderHandlerHook
from club.fnep.hooks import missing_header_handler

def main():
    """应用启动入口"""
    # 配置 Cullinan（自动处理 sys.path）
    configure(
        user_packages=['club.fnep'],
        verbose=False,  # 生产环境设为 False
        auto_scan=False  # 只扫描指定的包
    )
    
    # 注册全局钩子
    MissingHeaderHandlerHook.set_hook(missing_header_handler)
    
    # 启动应用
    print("Starting Discord Bot API...")
    application.run(port=8080)

if __name__ == '__main__':
    main()
```

---

## 测试

新功能已通过单元测试验证：

```bash
$ python run_tests.py

Ran 29 tests in 0.081s
OK

✓ 所有测试通过！(29/29)
```

---

## 更新时间

2025-11-06

## 相关文件

- `cullinan/config.py` - 实现自动 sys.path 处理
- `tests/test_core.py` - 包含相关测试用例

