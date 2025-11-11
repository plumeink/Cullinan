# -*- coding: utf-8 -*-
"""
通用诊断工具：检查你的应用包在 Nuitka 编译后的模块加载情况

使用方法：
    python diagnose_app.py your_app

其中 your_app 是你的应用包名，例如：myapp, your_project 等
"""

import sys
import os
import importlib

# 获取要诊断的包名
if len(sys.argv) > 1:
    APP_PACKAGE = sys.argv[1]
else:
    APP_PACKAGE = 'your_app'  # 默认值，请替换为你的包名

print("=" * 80)
print(f"{APP_PACKAGE} Nuitka 打包诊断")
print("=" * 80)
print()

# 1. 环境信息
print("1. 环境信息:")
print(f"   Python: {sys.version}")
print(f"   可执行文件: {sys.executable}")
print(f"   当前目录: {os.getcwd()}")
print(f"   sys.frozen: {getattr(sys, 'frozen', False)}")
print(f"   Nuitka: {'__compiled__' in globals() or hasattr(sys, '__compiled__')}")
print()

# 2. sys.modules 中的应用模块
print(f"2. sys.modules 中的 {APP_PACKAGE} 相关模块:")
app_modules = [name for name in sys.modules.keys() if APP_PACKAGE in name]
if app_modules:
    for mod_name in sorted(app_modules):
        mod = sys.modules[mod_name]
        mod_file = getattr(mod, '__file__', 'N/A')
        print(f"   ✓ {mod_name}")
        print(f"     文件: {mod_file}")
else:
    print(f"   ✗ 未找到任何 {APP_PACKAGE} 模块!")
print()

# 3. 尝试导入关键模块
print("3. 尝试导入关键模块:")
test_modules = [
    APP_PACKAGE,
    f'{APP_PACKAGE}.controllers',
    f'{APP_PACKAGE}.services',
]

for mod_name in test_modules:
    try:
        mod = importlib.import_module(mod_name)
        print(f"   ✓ {mod_name}")
        print(f"     文件: {getattr(mod, '__file__', 'N/A')}")
    except Exception as e:
        print(f"   ✗ {mod_name}: {e}")
print()

# 4. 扫描可执行文件目录
print("4. 扫描可执行文件目录:")
exe_dir = os.path.dirname(sys.executable)
print(f"   目录: {exe_dir}")

found_files = []
for root, dirs, files in os.walk(exe_dir):
    # 只看前3层
    depth = root[len(exe_dir):].count(os.sep)
    if depth > 3:
        continue

    dirs[:] = [d for d in dirs if not d.startswith('_')]

    for f in files:
        if APP_PACKAGE in f.lower() or f.endswith('.py'):
            rel_path = os.path.relpath(os.path.join(root, f), exe_dir)
            found_files.append(rel_path)

if found_files:
    print(f"   找到 {len(found_files)} 个相关文件:")
    for f in sorted(found_files)[:20]:
        print(f"     - {f}")
    if len(found_files) > 20:
        print(f"     ... 还有 {len(found_files) - 20} 个文件")
else:
    print("   ✗ 未找到相关文件")
print()

# 5. Controller 检查
print("5. Controller 注册情况:")
try:
    from cullinan.handler import get_handler_registry
    handler_registry = get_handler_registry()
    handlers = handler_registry.get_handlers()
    print(f"   已注册的 Handler: {len(handlers)}")
    if handlers:
        for url, servlet in handlers[:5]:
            servlet_name = servlet.__name__ if hasattr(servlet, '__name__') else str(servlet)
            print(f"     - {url} -> {servlet_name}")
        if len(handlers) > 5:
            print(f"     ... 还有 {len(handlers) - 5} 个")
    else:
        print("   ⚠ 警告: 没有已注册的 Handler!")
except Exception as e:
    print(f"   错误: {e}")
print()

# 6. __main__ 模块检查
print("6. __main__ 模块:")
if '__main__' in sys.modules:
    main_mod = sys.modules['__main__']
    print(f"   ✓ __main__ 存在")
    print(f"   文件: {getattr(main_mod, '__file__', 'N/A')}")
    print(f"   包: {getattr(main_mod, '__package__', 'N/A')}")

    attrs = [name for name in dir(main_mod) if not name.startswith('_')]
    print(f"   公开属性: {attrs[:10]}")
else:
    print("   ✗ __main__ 不存在")
print()

print("=" * 80)
print("诊断完成!")
print("=" * 80)
print()
print("建议:")
if not app_modules:
    print(f"⚠ 未找到 {APP_PACKAGE} 模块!")
    print("  可能原因:")
    print("  1. 模块没有被 Nuitka 包含（检查 --include-module 参数）")
    print("  2. 模块被包含但没有被导入到 sys.modules")
    print("  3. 模块名称在编译后发生了变化")
    print()
    print("  解决方案:")
    print(f"  1. 在 application.py 开头显式导入:")
    print(f"     from cullinan import configure")
    print(f"     configure(user_packages=['{APP_PACKAGE}'])")
    print(f"  2. 确保打包命令包含: --include-package={APP_PACKAGE}")
    print("  3. 尝试 --follow-imports")

