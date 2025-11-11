# -*- coding: utf-8 -*-
"""
Cullinan 打包诊断工具

用于调试打包后的模块扫描问题
"""

import sys
import os
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s: %(message)s'
)

print("=" * 80)
print("Cullinan 打包诊断工具")
print("=" * 80)
print()

# 1. 环境信息
print("1. 环境信息:")
print(f"   Python 版本: {sys.version}")
print(f"   可执行文件: {sys.executable}")
print(f"   当前目录: {os.getcwd()}")
print(f"   sys.frozen: {getattr(sys, 'frozen', False)}")
print(f"   sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
print(f"   __compiled__: {'__compiled__' in globals() or hasattr(sys, '__compiled__')}")
print()

# 2. 检测打包环境
print("2. 打包环境检测:")
try:
    from cullinan.application import is_nuitka_compiled, is_pyinstaller_frozen
    from cullinan.application import get_nuitka_standalone_mode, get_pyinstaller_mode

    is_nuitka = is_nuitka_compiled()
    is_pyinstaller = is_pyinstaller_frozen()

    print(f"   Nuitka 编译: {is_nuitka}")
    if is_nuitka:
        print(f"   Nuitka 模式: {get_nuitka_standalone_mode()}")

    print(f"   PyInstaller 打包: {is_pyinstaller}")
    if is_pyinstaller:
        print(f"   PyInstaller 模式: {get_pyinstaller_mode()}")
except Exception as e:
    print(f"   错误: {e}")
print()

# 3. sys.modules 分析
print("3. sys.modules 分析:")
print(f"   总模块数: {len(sys.modules)}")

# 按类别统计
stdlib_count = 0
thirdparty_count = 0
user_count = 0
cullinan_count = 0

for mod_name in sys.modules.keys():
    if mod_name.startswith('cullinan'):
        cullinan_count += 1
    elif mod_name.startswith('_') or '.' not in mod_name:
        stdlib_count += 1
    else:
        mod = sys.modules.get(mod_name)
        if mod:
            mod_file = getattr(mod, '__file__', None)
            if mod_file and 'site-packages' in mod_file:
                thirdparty_count += 1
            else:
                user_count += 1

print(f"   标准库模块: {stdlib_count}")
print(f"   第三方库模块: {thirdparty_count}")
print(f"   Cullinan 模块: {cullinan_count}")
print(f"   用户模块: {user_count}")
print()

# 4. 用户模块详情
print("4. 潜在的用户模块:")
EXCLUDE_PREFIXES = (
    '_', 'abc', 'asyncio', 'collections', 'concurrent', 'ctypes', 'datetime',
    'email', 'encodings', 'html', 'http', 'importlib', 'json', 'logging',
    'multiprocessing', 'os', 'pickle', 'pkg_resources', 'queue', 're',
    'setuptools', 'socket', 'ssl', 'threading', 'typing', 'urllib', 'weakref',
    'xml', 'tornado', 'dotenv', 'sqlalchemy', 'certifi', 'idna', 'charset_normalizer'
)

user_modules = []
for mod_name in sorted(sys.modules.keys()):
    if mod_name.startswith('cullinan'):
        continue
    if mod_name.startswith('_'):
        continue

    skip = False
    for prefix in EXCLUDE_PREFIXES:
        if mod_name == prefix or mod_name.startswith(prefix + '.'):
            skip = True
            break
    if skip:
        continue

    mod = sys.modules.get(mod_name)
    if mod:
        mod_file = getattr(mod, '__file__', None)
        if mod_file:
            if 'site-packages' not in mod_file and 'lib' + os.sep + 'python' not in mod_file:
                if 'nuitka' not in mod_file.lower():
                    user_modules.append((mod_name, mod_file))
                    print(f"   ✓ {mod_name}")
                    print(f"     文件: {mod_file}")

if not user_modules:
    print("   (未找到用户模块)")
print()

# 5. Controller 检查
print("5. Controller 检查:")
try:
    from cullinan.handler import get_handler_registry
    handler_registry = get_handler_registry()
    handlers = handler_registry.get_handlers()
    print(f"   已注册的 Handler 数量: {len(handlers)}")
    if handlers:
        print("   已注册的路由:")
        for url, servlet in handlers:
            print(f"     - {url} -> {servlet.__name__ if hasattr(servlet, '__name__') else servlet}")
    else:
        print("   ⚠ 警告: 未找到任何已注册的 Handler!")
except Exception as e:
    print(f"   错误: {e}")
print()

# 6. 模块扫描测试
print("6. 模块扫描测试:")
try:
    from cullinan.application import file_list_func
    print("   执行 file_list_func()...")
    modules = file_list_func()
    print(f"   扫描到的模块数: {len(modules)}")
    if modules:
        print("   前 10 个模块:")
        for mod in modules[:10]:
            print(f"     - {mod}")
        if len(modules) > 10:
            print(f"     ... 还有 {len(modules) - 10} 个模块")
except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()
print()

# 7. 建议
print("=" * 80)
print("诊断建议:")
print("=" * 80)

if user_count == 0:
    print("⚠ 警告: 未检测到用户模块")
    print("  建议:")
    print("  1. 确保使用了 --include-package 或 --collect-all 参数")
    print("  2. 在主文件中显式导入 controller 模块")
    print("  3. 检查打包命令是否正确")
    print()

try:
    from cullinan.handler import get_handler_registry
    handler_registry = get_handler_registry()
    handlers = handler_registry.get_handlers()
    if len(handlers) == 0:
        print("⚠ 警告: Controller 未被注册")
        print("  可能原因:")
        print("  1. Controller 模块未被正确导入")
        print("  2. Controller 装饰器未执行")
        print("  3. 模块扫描逻辑有问题")
        print()
        print("  解决方案:")
        print("  1. 在主文件中使用: from your_package import your_controller")
        print("  2. 确保 controller 文件在独立的模块中")
        print("  3. 启用 DEBUG 日志查看详细信息")
        print()
except:
    pass

print("=" * 80)
print("诊断完成!")
print("=" * 80)

