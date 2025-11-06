# -*- coding: utf-8 -*-
"""
your_app.application with Nuitka packaging fix

在你的 your_app/application.py 文件开头添加这些代码
"""

import sys
import os

# ============================================================================
# Nuitka 打包修复：显式导入所有模块
# ============================================================================
print("=" * 80)
print("Nuitka Packaging Fix: Loading your_app modules explicitly...")
print("=" * 80)

# 检测运行环境
IS_NUITKA = '__compiled__' in globals() or hasattr(sys, '__compiled__')
IS_FROZEN = getattr(sys, 'frozen', False)

print(f"Environment: Nuitka={IS_NUITKA}, Frozen={IS_FROZEN}")
print(f"Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print()

# 显式导入所有关键模块
# 这确保它们被加载到 sys.modules，框架才能扫描到
modules_to_import = [
    ('your_app.controllers.user_controller', 'User controller'),
    ('your_app.controllers.product_controller', 'Product controller'),
    ('your_app.services.user_service', 'User service'),
    ('your_app.services.product_service', 'Product service'),
    # 根据你的项目添加更多模块
]

successfully_imported = []
failed_imports = []

for module_name, description in modules_to_import:
    try:
        # 使用 __import__ 确保导入
        __import__(module_name)
        successfully_imported.append(module_name)
        print(f"✓ {description}: {module_name}")
    except Exception as e:
        failed_imports.append((module_name, str(e)))
        print(f"✗ Failed to import {module_name}: {e}")

print()
print(f"Successfully imported: {len(successfully_imported)} modules")
if failed_imports:
    print(f"Failed imports: {len(failed_imports)} modules")
    for mod, err in failed_imports:
        print(f"  - {mod}: {err}")

# 验证模块是否在 sys.modules 中
print()
print("Verifying sys.modules...")
app_modules = [name for name in sys.modules.keys() if 'your_app' in name]
print(f"your_app modules in sys.modules: {len(app_modules)}")
for mod in sorted(app_modules)[:15]:
    print(f"  - {mod}")
if len(app_modules) > 15:
    print(f"  ... and {len(app_modules) - 15} more")

print("=" * 80)
print()

# ============================================================================
# 然后是你原来的代码
# ============================================================================

from cullinan import Application

def main():
    """Application entry point"""

    # 额外的验证（可选）
    if IS_NUITKA or IS_FROZEN:
        print("Running in packaged mode, verifying Controller registration...")
        try:
            from cullinan.controller import handler_list
            print(f"Registered handlers: {len(handler_list)}")
            if len(handler_list) > 0:
                print("✓ Controllers successfully registered!")
                for handler in handler_list[:5]:
                    print(f"  - {handler[0]}")  # URL pattern
                if len(handler_list) > 5:
                    print(f"  ... and {len(handler_list) - 5} more")
            else:
                print("⚠ WARNING: No handlers registered!")
                print("  This means Controllers were not loaded properly.")
                print("  Check the import statements above.")
        except Exception as e:
            print(f"✗ Error checking handlers: {e}")
        print()

    # 启动应用
    app = Application()
    app.run()

if __name__ == '__main__':
    main()

