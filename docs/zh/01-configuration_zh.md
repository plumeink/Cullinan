# Cullinan 配置系统使用指南

## 概述

Cullinan 现在支持通过配置文件精确指定用户包，彻底解决打包环境下的模块扫描问题。这是一个更专业、更优雅的解决方案�?

## 为什么需要配置？

### 传统方式的问�?

1. **EXCLUDE_PREFIXES 维护困难**：需要不断添加要排除的包
2. **扫描不精�?*：可能扫描到不需要的模块
3. **打包后失�?*：Nuitka/PyInstaller 改变了文件结�?

### 配置方式的优�?

1. �?**精确控制**：只扫描指定的包
2. �?**打包友好**：适用于所有打包工�?
3. �?**易于维护**：配置清晰明�?
4. �?**零侵�?*：不需要修改业务代�?

## 快速开�?

### 方式 1: 代码配置（推荐）

```python
# your_app/application.py

from cullinan import configure, Application

# 在创�?Application 之前配置
configure(
    user_packages=['your_app'],  # 你的包名
    verbose=True                   # 可选：启用详细日志
)

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
```

**就这么简单！** 框架会自动扫�?`your_app` 包下的所有模块�?

### 方式 2: JSON 配置文件

创建 `cullinan.json`�?

```json
{
  "user_packages": [
    "your_app"
  ],
  "verbose": true,
  "auto_scan": false
}
```

在代码中加载�?

```python
import json
from cullinan import get_config, Application

# 加载配置
with open('cullinan.json', 'r') as f:
    config_data = json.load(f)
    get_config().from_dict(config_data)

app = Application()
app.run()
```

### 方式 3: 环境变量

```bash
# 设置环境变量
export CULLINAN_USER_PACKAGES=your_app,myapp.controllers

# �?Windows
set CULLINAN_USER_PACKAGES=your_app,myapp.controllers
```

```python
import os
from cullinan import configure, Application

# 从环境变量加�?
if os.getenv('CULLINAN_USER_PACKAGES'):
    packages = os.getenv('CULLINAN_USER_PACKAGES').split(',')
    configure(user_packages=packages)

app = Application()
app.run()
```

## 配置选项详解

### user_packages (List[str])

指定要扫描的用户包列表�?

```python
configure(
    user_packages=[
        'your_app',              # 扫描整个�?
        'myapp.controllers',      # 只扫�?controllers
        'myapp.services'          # 只扫�?services
    ]
)
```

**工作原理**�?
1. 导入指定的包
2. 使用 `pkgutil.walk_packages` 递归扫描所有子模块
3. 自动导入所有模块，触发装饰�?

### verbose (bool)

启用详细日志，查看扫描过程�?

```python
configure(verbose=True)
```

### auto_scan (bool)

是否启用自动扫描（回退策略）�?

```python
configure(
    user_packages=['your_app'],
    auto_scan=False  # 禁用自动扫描，只使用配置的包
)
```

- `True`（默认）：如果配置的包导入失败，尝试自动扫描
- `False`：严格模式，只使用配置的�?

### project_root (str)

项目根目录（通常自动检测）�?

```python
configure(project_root='/path/to/project')
```

### exclude_packages (List[str])

排除的包名列表（用于 auto_scan）�?

```python
configure(
    exclude_packages=['test', 'tests', '__pycache__']
)
```

## 打包场景最佳实�?

### Nuitka 打包

#### Standalone 模式

```python
# your_app/application.py

from cullinan import configure, Application

# 配置（在 Application 之前�?
configure(
    user_packages=['your_app'],
    auto_scan=False  # 严格模式
)

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
```

**打包命令**�?

```bash
nuitka --standalone \
       --include-package=your_app \
       --include-package=cullinan \
       your_app/application.py
```

**不再需�?* `--include-module` 逐个指定模块�?

#### Onefile 模式

配置相同，打包命令：

```bash
nuitka --onefile \
       --include-package=your_app \
       --include-package=cullinan \
       your_app/application.py
```

### PyInstaller 打包

#### Onedir 模式

```python
from cullinan import configure, Application

configure(user_packages=['your_app'])

app = Application()
app.run()
```

**打包命令**�?

```bash
pyinstaller --onedir \
            --hidden-import=your_app \
            --collect-all=your_app \
            --collect-all=cullinan \
            application.py
```

#### Onefile 模式

配置相同，打包命令：

```bash
pyinstaller --onefile \
            --hidden-import=your_app \
            --collect-all=your_app \
            --collect-all=cullinan \
            application.py
```

## 工作原理

### 开发环�?

1. 读取配置�?`user_packages`
2. 尝试导入每个�?
3. 使用 `pkgutil.walk_packages` 扫描子模�?
4. 导入所有子模块，触发装饰器

### Nuitka 打包

1. 读取配置�?`user_packages`
2. **导入�?*（Nuitka 已经将模块编译进去）
3. 扫描子模块（通过 `pkg.__path__`�?
4. 回退：如果包无法导入，从 sys.modules 查找

### PyInstaller 打包

1. 读取配置�?`user_packages`
2. **导入�?*（PyInstaller 已经打包�?
3. 扫描子模�?
4. 回退：目录扫描（如果启用 auto_scan�?

## 完整示例

### your_app 项目配置

```python
# your_app/application.py

import logging
from cullinan import configure, Application

# 配置日志
logging.basicConfig(level=logging.INFO)

# 配置 Cullinan
configure(
    user_packages=['your_app'],  # 指定�?
    verbose=True,                  # 查看扫描过程
    auto_scan=False                # 严格模式
)

def main():
    # 验证配置
    from cullinan import get_config
    config = get_config()
    print(f"Configured packages: {config.user_packages}")
    
    # 创建应用
    app = Application()
    
    # 验证 Controller
    from cullinan.controller import handler_list
    print(f"Registered handlers: {len(handler_list)}")
    
    # 启动
    app.run()

if __name__ == '__main__':
    main()
```

### 日志输出

配置正确后，你会看到�?

```
Configured packages: ['your_app']

INFO:cullinan.application: Starting module discovery...
INFO:cullinan.application: === Using Nuitka scanning strategy ===
INFO:cullinan.application: Using configured user packages: ['your_app']
INFO:cullinan.application: Found 11 modules from configured packages
INFO:cullinan.application: �?Successfully imported: your_app.controller
INFO:cullinan.application: �?Successfully imported: your_app.hooks
...

Registered handlers: 5
```

## 对比：配置前 vs 配置�?

### 配置前（问题�?

```
INFO: Found 0 user modules in sys.modules  �?问题�?
INFO: Only __main__ found
```

**原因**：框架不知道要扫描哪些包

### 配置后（解决�?

```
INFO: Using configured user packages: ['your_app']
INFO: Found 11 modules from configured packages  �?成功�?
INFO: �?your_app.controller
INFO: �?your_app.hooks
...
```

**原因**：精确指定了要扫描的�?

## 迁移指南

### 从旧方式迁移

**之前**：需要显式导�?

```python
# 需要手动导入所有模�?
from your_app import controller
from your_app import hooks
from your_app.service import user_service

from cullinan import Application
app = Application()
```

**现在**：使用配�?

```python
# 只需配置一�?
from cullinan import configure, Application

configure(user_packages=['your_app'])

# 不需要手动导入！框架会自动处�?
app = Application()
```

## 高级用法

### 多包配置

```python
configure(
    user_packages=[
        'your_app',        # 主应�?
        'plugins.auth',     # 认证插件
        'plugins.payment'   # 支付插件
    ]
)
```

### 条件配置

```python
import os
from cullinan import configure

packages = ['myapp']

# 开发环境添加测试包
if os.getenv('ENV') == 'development':
    packages.append('myapp.tests')

configure(user_packages=packages)
```

### 动态配�?

```python
from cullinan import get_config

config = get_config()
config.add_user_package('myapp.controllers')
config.add_user_package('myapp.services')
config.set_verbose(True)
```

## 故障排查

### 问题：Still 404

**检�?*�?

```python
from cullinan import get_config

config = get_config()
print(f"Configured packages: {config.user_packages}")

# 应该输出你配置的包，不应该是空列�?
```

**解决**：确保在 `Application()` 之前调用 `configure()`

### 问题：导入失�?

启用详细日志�?

```python
configure(
    user_packages=['your_app'],
    verbose=True  # 查看详细的导入过�?
)
```

查看日志中的错误信息�?

### 问题：某些模块没有被扫描

**检查包结构**�?

```
your_project/
└── app/
    ├── __init__.py          �?必须�?
    ├── controller.py
    └── service/
        ├── __init__.py      �?必须�?
        └── user_service.py
```

**确保每个目录都有 `__init__.py`**�?

## 总结

### 核心要点

1. �?使用 `configure(user_packages=[...])` 指定�?
2. �?在创�?`Application` **之前**配置
3. �?不需要手动导入模�?
4. �?适用于所有打包工�?

### 推荐配置

```python
from cullinan import configure, Application

configure(
    user_packages=['your_app'],  # 你的�?
    auto_scan=False               # 严格模式（可选）
)

app = Application()
app.run()
```

**这是最专业、最优雅的解决方案！** 🎉

