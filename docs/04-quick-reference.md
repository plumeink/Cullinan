# Cullinan 配置快速参考

## 一行解决打包问题

```python
from cullinan import configure, Application

configure(user_packages=['your_app'])  # 你的包名
app = Application()
app.run()
```

## 配置选项

```python
configure(
    user_packages=['your_app'],   # 必需：要扫描的包
    verbose=True,                   # 可选：详细日志
    auto_scan=False,                # 可选：禁用自动扫描
    project_root='/path/to/app',    # 可选：项目根目录
    exclude_packages=['test']       # 可选：排除的包
)
```

## 适用场景

✅ Nuitka Standalone  
✅ Nuitka Onefile  
✅ PyInstaller Onedir  
✅ PyInstaller Onefile  
✅ 开发环境  

## 打包命令简化

### 之前

```bash
nuitka --standalone \
       --include-module=your_app.application \
       --include-module=your_app.controllers \
       --include-module=your_app.services \
       # ... 还有很多
```

### 现在

```bash
nuitka --standalone \
       --include-package=your_app \
       application.py
```

## 验证配置

```python
from cullinan import get_config
from cullinan.controller import handler_list

config = get_config()
print(f"Packages: {config.user_packages}")
print(f"Handlers: {len(handler_list)}")
```

## 完整示例

```python
# your_app/application.py

from cullinan import configure, Application

# 配置（必须在 Application 之前）
configure(user_packages=['your_app'])

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
```

## JSON 配置（可选）

```json
{
  "user_packages": ["your_app"],
  "verbose": true,
  "auto_scan": false
}
```

```python
import json
from cullinan import get_config

with open('cullinan.json') as f:
    get_config().from_dict(json.load(f))
```

## 环境变量（可选）

```bash
export CULLINAN_USER_PACKAGES=your_app
```

```python
import os
from cullinan import configure

if pkg := os.getenv('CULLINAN_USER_PACKAGES'):
    configure(user_packages=pkg.split(','))
```

## 对比效果

### 配置前

```
INFO: Found 0 user modules  ← 问题
API 404
```

### 配置后

```
INFO: Using configured user packages: ['your_app']
INFO: Found 11 modules  ← 解决
API 200 OK
```

## 详细文档

- 完整指南：`docs/CONFIGURATION_GUIDE.md`
- 示例代码：`examples/config_example.py`
- JSON 示例：`examples/cullinan.json`

