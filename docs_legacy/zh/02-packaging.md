# Cullinan 打包指南

本指南介绍如何使用 Nuitka 和 PyInstaller 打包 Cullinan Web 应用程序。

## 概述

Cullinan 框架现已完全支持 Nuitka 和 PyInstaller 打包，包括 onefile 和 onedir/standalone 模式。框架会自动检测运行环境并使用相应的模块扫描策略。

## 打包环境检测

框架内置了智能环境检测机制：

- **Nuitka 检测**：检测 `__compiled__` 属性和 `sys.frozen`
- **PyInstaller 检测**：检测 `sys.frozen` 和 `sys._MEIPASS`
- **模式识别**：自动识别 onefile 和 standalone/onedir 模式

## Nuitka 打包

### Standalone 模式（推荐）

```bash
nuitka --standalone \
       --enable-plugin=tornado \
       --include-package=your_app \
       --include-package-data=your_app \
       --output-dir=dist \
       your_app/main.py
```

### Onefile 模式

```bash
nuitka --onefile \
       --enable-plugin=tornado \
       --include-package=your_app \
       --include-package-data=your_app \
       --output-dir=dist \
       your_app/main.py
```

### 关键参数说明

- `--standalone` / `--onefile`：打包模式
- `--enable-plugin=tornado`：启用 Tornado 插件（如果使用）
- `--include-package=your_app`：包含你的应用程序包
- `--include-package-data=your_app`：包含包数据文件

### Nuitka 模块扫描策略

Cullinan 在 Nuitka 环境下使用以下扫描策略：

1. **sys.modules 扫描**：扫描已加载的模块（Nuitka 会预加载包含的模块）
2. **目录扫描**（Standalone 模式）：扫描可执行文件目录的 .pyd/.so 文件
3. **包推断**（Onefile 模式）：从调用栈推断包名并扫描
4. **__main__ 扫描**：从主模块路径扫描

## PyInstaller 打包

### Onedir 模式（推荐）

```bash
pyinstaller --onedir \
            --hidden-import=your_app \
            --collect-all=your_app \
            --name=your_app \
            your_app/main.py
```

### Onefile 模式

```bash
pyinstaller --onefile \
            --hidden-import=your_app \
            --collect-all=your_app \
            --name=your_app \
            your_app/main.py
```

### 关键参数说明

- `--onefile` / `--onedir`：打包模式
- `--hidden-import=your_app`：声明隐藏导入
- `--collect-all=your_app`：收集所有包数据

### PyInstaller 模块扫描策略

Cullinan 在 PyInstaller 环境下使用以下扫描策略：

1. **_MEIPASS 扫描**：扫描 PyInstaller 临时解压目录
2. **可执行文件目录扫描**（Onedir 模式）
3. **sys.modules 补充扫描**：扫描已导入的模块

## 最佳实践

### 1. 显式导入关键模块

虽然框架会自动扫描，但建议在主文件中显式导入关键模块：

```python
# main.py
from cullinan import Application

# 显式导入 controller 和 service（可选，但推荐）
from your_app import controllers
from your_app import services

app = Application()
app.run()
```

### 2. 使用包结构

推荐的项目结构：

```
your_app/
├── __init__.py
├── main.py
├── controllers/
│   ├── __init__.py
│   ├── user_controller.py
│   └── product_controller.py
└── services/
    ├── __init__.py
    ├── user_service.py
    └── product_service.py
```

### 3. 在 __init__.py 中导入

在包的 `__init__.py` 中导入所有子模块：

```python
# controllers/__init__.py
from . import user_controller
from . import product_controller

# services/__init__.py
from . import user_service
from . import product_service
```

### 4. Nuitka 特殊注意事项

对于 Nuitka，确保所有需要的模块都被包含：

```bash
# 使用 --include-module 明确包含特定模块
nuitka --standalone \
       --include-package=your_app \
       --include-module=your_app.controllers.user_controller \
       --include-module=your_app.services.user_service \
       your_app/main.py
```

### 5. PyInstaller Spec 文件

创建 `.spec` 文件以获得更精细的控制：

```python
# your_app.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['your_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'your_app.controllers.user_controller',
        'your_app.services.user_service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='your_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='your_app',
)
```

## 调试打包问题

### 启用详细日志

框架使用 Python logging 模块。启用 DEBUG 级别查看详细的扫描信息：

```python
import logging

logging.basicConfig(level=logging.DEBUG)

from cullinan import Application
app = Application()
app.run()
```

### 日志输出示例

```
INFO:cullinan.application: ||| Starting module discovery...
INFO:cullinan.application: ||| === Using Nuitka scanning strategy ===
INFO:cullinan.application: ||| Detected Nuitka compiled environment
INFO:cullinan.application: ||| Nuitka mode: standalone
INFO:cullinan.application: ||| Scanning Nuitka standalone directory: C:\app\dist
INFO:cullinan.application: ||| Found 15 modules via Nuitka scanning
INFO:cullinan.application: ||| Discovered 15 modules
```

### 常见问题排查

#### 问题：Controller 或 Service 未被扫描到

**解决方案**：
1. 确认模块已被打包（检查打包输出）
2. 在主文件中显式导入模块
3. 使用 `--include-module` 或 `--hidden-import` 明确包含

#### 问题：导入错误

**解决方案**：
1. 检查模块路径是否正确
2. 确认 `__init__.py` 文件存在
3. 检查是否有循环导入

#### 问题：Onefile 模式下模块丢失

**解决方案**：
1. 优先使用 standalone/onedir 模式
2. 使用显式导入
3. 检查打包工具的数据收集选项

## 测试打包结果

### 开发环境测试

```bash
python your_app/main.py
```

### Nuitka 打包测试

```bash
# Standalone
cd dist/your_app.dist
./your_app

# Onefile
cd dist
./your_app
```

### PyInstaller 打包测试

```bash
# Onedir
cd dist/your_app
./your_app

# Onefile
cd dist
./your_app
```

## 性能优化

### Nuitka 优化

```bash
nuitka --standalone \
       --lto=yes \
       --enable-plugin=anti-bloat \
       --remove-output \
       your_app/main.py
```

### PyInstaller 优化

```bash
pyinstaller --onefile \
            --optimize=2 \
            --strip \
            --upx-dir=/path/to/upx \
            your_app/main.py
```

## 总结

Cullinan 框架现已完全支持主流打包工具，能够自动适应不同的打包环境。遵循本指南的最佳实践，可以确保应用程序在打包后正常运行。

如有问题，请查看详细日志或提交 Issue。

