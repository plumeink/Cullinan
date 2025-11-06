# 示例应用 - Cullinan 配置指南

## 快速配置

在你的项目中添加 Cullinan 配置，只需在 `application.py` 开头添加**两行代码**：

```python
from cullinan import configure
configure(user_packages=['your_app'])
```

## 完整示例

### your_app/application.py

```python
# your_app/application.py

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s: %(message)s'
)

# ============================================================
# Cullinan 配置（必须在 Application 之前）
# ============================================================

from cullinan import configure

configure(
    user_packages=['your_app'],  # 指定你的包
    verbose=True,                 # 启用详细日志（可选）
    auto_scan=False               # 严格模式（推荐）
)

print("✓ Cullinan configured")

# ============================================================
# 原来的代码
# ============================================================

from cullinan import Application

def main():
    """应用入口"""
    
    # 可选：验证配置
    from cullinan import get_config
    from cullinan.controller import handler_list
    
    config = get_config()
    print(f"Configured packages: {config.user_packages}")
    print(f"Registered handlers: {len(handler_list)}")
    
    # 创建并启动应用
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
```

## 打包命令

### Nuitka

**简化后的打包命令**：
```bash
nuitka --standalone \
       --include-package=your_app \
       --include-package=cullinan \
       --output-dir=build/nuitka \
       your_app/application.py
```

### PyInstaller

```bash
pyinstaller --onedir \
            --hidden-import=your_app \
            --collect-all=your_app \
            --collect-all=cullinan \
            your_app/application.py
```

## 预期输出

配置后，启动应用应该看到：

```
✓ Cullinan configured

INFO:cullinan.application: Starting module discovery...
INFO:cullinan.application: === Using development/Nuitka/PyInstaller scanning strategy ===
INFO:cullinan.application: Using configured user packages: ['your_app']
INFO:cullinan.application: Found X modules from configured packages
INFO:cullinan.application: ✓ Successfully imported: your_app.controllers
INFO:cullinan.application: ✓ Successfully imported: your_app.services
...

Registered handlers: 5
```

## 对比：配置前 vs 配置后

### 配置前（有问题）

```
INFO: Found 0 user modules in sys.modules
API 404 - Controller not found
```

### 配置后（正常）

```
INFO: Using configured user packages: ['your_app']
INFO: Found X modules from configured packages
API 200 OK
```

## 故障排查

如果还有问题，检查：

1. **配置是否在 Application 之前**
2. **包名是否正确**（应该是 `your_app`，不是 `your_app/`）
3. **启用详细日志**查看扫描详情

详细文档请参考：
- `docs/CONFIGURATION_GUIDE.md` - 完整配置指南
- `docs/packaging_guide.md` - 打包详细说明

