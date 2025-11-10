# 打包后 Controller 未注册问题排查指南

## 问题现象

打包后运行应用，访问 API 时返回 404 错误，虽然日志显示扫描到了模块，但 Controller 没有被注册。

## 根本原因

在 Nuitka 编译环境下，有以下几种可能：

1. **模块被扫描但未导入**：模块在 sys.modules 中被发现，但 `reflect_module` 没有真正导入它
2. **导入失败被忽略**：导入时出错，但错误被静默处理了
3. **装饰器未执行**：模块虽然存在，但装饰器代码没有运行
4. **Controller 定义位置**：Controller 定义在主文件 ` __main__` 中，而不是独立模块

## 诊断步骤

### 1. 运行诊断工具

```bash
cd dist_nuitka\packaging_test.dist  # Standalone 模式
packaging_test.exe  # 这会失败，但没关系

# 然后运行诊断
python ..\..\..\examples\diagnose.py
```

诊断工具会显示：
- 环境检测结果
- sys.modules 中的模块列表
- 已注册的 Handler 数量
- 扫描到的用户模块

### 2. 启用详细日志

修改 `packaging_test.py`，启用 DEBUG 日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

查看以下关键日志：
- `✓ Successfully imported: xxx` - 模块成功导入
- `✗ Import failed for xxx` - 模块导入失败
- `✓ Found in sys.modules: xxx` - 从 sys.modules 找到模块

### 3. 检查 Handler 列表

在应用代码中添加：

```python
from cullinan.controller import handler_list

print(f"Registered handlers: {len(handler_list)}")
for handler in handler_list:
    print(f"  - {handler}")
```

## 解决方案

### 方案 1: 将 Controller 放在独立模块中（推荐）

**不要** 在主文件中定义 Controller：

```python
# ❌ 错误：在 main.py 中定义
@Controller('/api')
class TestController:
    pass

def main():
    app = Application()
    app.run()
```

**应该** 创建独立的 controller 模块：

```python
# examples/test_controller.py
from cullinan.controller import Controller, request_mapping

@Controller('/api')
class TestController:
    @request_mapping('/hello', method=['GET'])
    def hello(self, request):
        return {'message': 'Hello'}
```

然后在主文件中**显式导入**：

```python
# examples/packaging_test.py
from cullinan import Application

# 显式导入 controller（重要！）
try:
    from examples import test_controller
except ImportError:
    import test_controller

def main():
    app = Application()
    app.run()
```

### 方案 2: 更新打包命令

确保使用 `--include-module` 参数：

```bash
nuitka --standalone \
       --include-package=cullinan \
       --include-package=examples \
       --include-module=examples.test_controller \
       examples/packaging_test.py
```

### 方案 3: 使用包结构

创建完整的包结构：

```
your_app/
├── __init__.py
├── main.py
├── controllers/
│   ├── __init__.py          # 重要：导入所有 controller
│   └── test_controller.py
└── services/
    ├── __init__.py          # 重要：导入所有 service
    └── test_service.py
```

在 `controllers/__init__.py` 中：

```python
# 导入所有 controller 模块
from . import test_controller
```

在 `main.py` 中：

```python
from cullinan import Application

# 显式导入
from your_app import controllers
from your_app import services

def main():
    app = Application()
    app.run()
```

### 方案 4: 强制导入

如果上述方法都不行，可以在应用启动前强制导入：

```python
# main.py
import sys
import importlib

# 强制导入 controller 模块
controller_modules = [
    'examples.test_controller',
    # 添加其他 controller 模块
]

for mod_name in controller_modules:
    try:
        importlib.import_module(mod_name)
        print(f"✓ Imported: {mod_name}")
    except Exception as e:
        print(f"✗ Failed to import {mod_name}: {e}")

from cullinan import Application
app = Application()
app.run()
```

## 验证修复

### 1. 检查日志

启动应用后，应该看到：

```
INFO:cullinan.application: ||| Starting module discovery...
INFO:cullinan.application: ||| === Using Nuitka scanning strategy ===
INFO:cullinan.application: ||| Found X user modules in sys.modules
INFO:cullinan.application: ✓ Found in sys.modules: examples.test_controller
```

### 2. 检查 Handler

应该看到：

```
Registered handlers: 3
  - ('/api/hello', <handler>, ['GET'])
  - ('/api/info', <handler>, ['GET'])
  - ('/api/test', <handler>, ['GET'])
```

### 3. 测试 API

```bash
curl http://localhost:8888/api/hello
# 应该返回: {"message": "Hello from Cullinan!", "status": "ok"}
```

## 当前实现的改进

我已经对代码做了以下改进：

1. **优先检查 sys.modules**：在 Nuitka 环境下，模块通常已经在 sys.modules 中
2. **详细日志**：使用 INFO/WARNING 级别记录导入状态
3. **__main__ 处理**：特别处理 __main__ 模块
4. **更好的过滤**：排除标准库和第三方库，只扫描用户代码

## 调试检查清单

- [ ] Controller 是否在独立模块中？
- [ ] 主文件是否显式导入了 controller 模块？
- [ ] `__init__.py` 是否存在并导入了子模块？
- [ ] 打包命令是否包含 `--include-module` 参数？
- [ ] 日志是否显示模块被成功导入？
- [ ] `handler_list` 是否包含注册的路由？
- [ ] 是否启用了 DEBUG 日志查看详细信息？

## 推荐的项目结构

```
your_project/
├── setup.py 或 pyproject.toml
├── your_app/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── controllers/
│   │   ├── __init__.py      # from . import user_controller
│   │   └── user_controller.py
│   └── services/
│       ├── __init__.py      # from . import user_service
│       └── user_service.py
└── build_scripts/
    ├── build_nuitka.bat
    └── build_pyinstaller.bat
```

## 联系支持

如果问题仍然存在，请提供：

1. 诊断工具的完整输出
2. 应用启动时的完整日志（使用 DEBUG 级别）
3. 项目结构截图
4. 打包命令
5. `handler_list` 的内容

这样我们可以更快地帮助你解决问题。

