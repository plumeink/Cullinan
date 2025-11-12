# -*- coding: utf-8 -*-
"""
Cullinan Framework - Nuitka/PyInstaller Packaging Guide

推荐方法：使用 cullinan.configure() 配置用户包
这是最简单、最可靠的方法

版本 v0.7.1+ 已内置打包支持，无需额外配置！
"""

# ============================================================================
# 方法 1：推荐 - 使用 cullinan.configure() 配置（最简单）
# ============================================================================

from cullinan import configure
from cullinan import Application

# 在导入应用模块之前配置框架
configure(
    user_packages=['your_app'],  # 替换为你的应用包名
    verbose=True,                  # 启用详细日志（可选）
    auto_scan=True                 # 启用自动扫描（默认）
)


def main():
    """Application entry point"""

    # 可选：打印路径诊断信息（用于调试打包问题）
    if __debug__:
        from cullinan import log_path_info
        log_path_info()

    # 启动应用
    app = Application()
    app.run()


if __name__ == '__main__':
    main()


# ============================================================================
# 方法 2：使用 path_utils 处理资源文件（新功能 v0.7.1+）
# ============================================================================
"""
如果你的应用需要访问配置文件、模板等资源，使用 path_utils 确保跨平台兼容：

from cullinan import get_resource_path, get_user_data_dir
import yaml

def load_config():
    # 获取配置文件路径（支持所有打包模式）
    config_path = get_resource_path('config.yaml')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config

def get_log_directory():
    # 获取用户数据目录（用于日志、缓存等）
    data_dir = get_user_data_dir()
    log_dir = data_dir / 'logs'
    log_dir.mkdir(exist_ok=True)
    return log_dir
"""


# ============================================================================
# 方法 3：显式导入模块（如果 configure 不能工作）
# ============================================================================
"""
如果自动扫描无法工作，可以在应用启动前显式导入所有控制器和服务：

import sys
import os

# 显式导入所有控制器和服务模块
# 这确保它们被加载到 sys.modules，框架才能扫描到
try:
    import your_app.controllers.user_controller
    import your_app.controllers.product_controller
    import your_app.services.user_service
    import your_app.services.product_service
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Failed to import modules: {e}")
    sys.exit(1)

from cullinan import Application

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
"""


# ============================================================================
# Nuitka 打包命令示例（推荐使用增强脚本）
# ============================================================================
"""
# 使用 Cullinan 提供的增强打包脚本（推荐）:

python scripts/build_nuitka_enhanced.py --entry application.py --app myapp --onefile \\
    --include-package your_app

# 或手动使用 Nuitka 命令:

# Windows 单文件模式:
python -m nuitka --standalone --onefile ^
    --enable-plugin=anti-bloat ^
    --windows-console-mode=attach ^
    --output-dir=dist ^
    --output-filename=your_app.exe ^
    --include-package=your_app ^
    --include-package=cullinan ^
    application.py

# Linux/Mac 单文件模式:
python -m nuitka --standalone --onefile \\
    --enable-plugin=anti-bloat \\
    --output-dir=dist \\
    --output-filename=your_app \\
    --include-package=your_app \\
    --include-package=cullinan \\
    application.py

# 如果需要包含其他依赖:
    --include-package=dotenv \\
    --include-package=tornado

# 如果需要包含静态文件:
    --include-data-dir=templates=templates \\
    --include-data-dir=static=static \\
    --include-data-file=.env=.env
"""


# ============================================================================
# PyInstaller 打包命令示例
# ============================================================================
"""
# 使用 Cullinan 提供的增强打包脚本（推荐）:

python scripts/build_pyinstaller_enhanced.py --entry application.py --app myapp --onefile \\
    --collect-all your_app

# 或手动使用 PyInstaller 命令:

# Windows/Linux/Mac 单文件模式:
pyinstaller --onefile \\
    --name=your_app \\
    --collect-all=your_app \\
    --collect-all=cullinan \\
    --hidden-import=your_app.controllers \\
    --hidden-import=your_app.services \\
    application.py

# 包含数据文件:
    --add-data="config.yaml{os.pathsep}." \\
    --add-data="templates{os.pathsep}templates"
"""


# ============================================================================
# 打包故障排查
# ============================================================================
"""
如果打包后运行出现问题，启用路径诊断：

from cullinan import log_path_info, get_path_info
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 打印路径信息
log_path_info()

# 或获取路径信息字典
path_info = get_path_info()
print(path_info)

常见问题：
1. "controller.py not found" - 已在 v0.7.1+ 修复，使用 path_utils
2. "Module not found" - 使用 --include-package 或 --collect-all
3. "Config file not found" - 使用 get_resource_path() 获取资源路径
4. "Cannot write logs" - 使用 get_user_data_dir() 获取数据目录
"""


# ============================================================================
# PyInstaller 打包命令示例
# ============================================================================
"""
# Windows 单文件模式:
pyinstaller --onefile ^
    --name=your_app ^
    --hidden-import=your_app ^
    --hidden-import=cullinan ^
    --collect-all=your_app ^
    --collect-all=cullinan ^
    your_app\application.py

# Linux/Mac 单文件模式:
pyinstaller --onefile \
    --name=your_app \
    --hidden-import=your_app \
    --hidden-import=cullinan \
    --collect-all=your_app \
    --collect-all=cullinan \
    your_app/application.py

# 如果需要包含静态文件:
    --add-data "templates;templates" \
    --add-data "static;static" \
    --add-data ".env;."
"""


# ============================================================================
# 故障排除
# ============================================================================
"""
如果打包后应用启动但没有路由：

1. 检查日志输出:
   ⚠ No modules found for service scanning!
   ⚠ No modules found for controller scanning!
   
   → 说明模块扫描失败

2. 解决方案 A - 使用 configure:
   from cullinan import configure
   configure(user_packages=['your_app'])

3. 解决方案 B - 显式导入:
   import your_app.controllers.user_controller
   import your_app.services.user_service

4. 解决方案 C - 检查打包配置:
   确保使用 --include-package=your_app 或 --hidden-import=your_app

5. 验证模块是否被打包:
   打包后运行应用，检查日志中的 "Discovered X modules" 信息
   
6. 如果仍然失败，启用详细日志:
   configure(user_packages=['your_app'], verbose=True)
   或设置环境变量:
   set CULLINAN_AUTO_CONSOLE_LEVEL=DEBUG
"""
    app = Application()
    app.run()

if __name__ == '__main__':
    main()

