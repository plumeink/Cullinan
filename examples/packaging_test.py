# -*- coding: utf-8 -*-
"""
Cullinan 打包测试示例

这个示例演示如何创建一个可以被 Nuitka 和 PyInstaller 打包的 Cullinan 应用。
"""

import logging
import sys
from pathlib import Path

# 配置日志以查看打包环境下的模块扫描过程
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s: %(message)s'
)

# 如果需要更详细的调试信息，取消下面的注释
# logging.getLogger('cullinan.application').setLevel(logging.DEBUG)

from cullinan import Application

# 显式导入 controller 模块（重要！确保被打包工具包含）
try:
    from examples import test_controller
    print("✓ Controller module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import controller: {e}")
    # 尝试相对导入
    try:
        import test_controller
        print("✓ Controller module imported successfully (relative)")
    except ImportError as e2:
        print(f"✗ Failed to import controller (relative): {e2}")


def main():
    """应用程序入口点"""
    print("=" * 60)
    print("Cullinan 打包测试应用")
    print("=" * 60)

    # 检测运行环境
    is_frozen = getattr(sys, 'frozen', False)

    if is_frozen:
        if '__compiled__' in globals() or hasattr(sys, '__compiled__'):
            print("检测到 Nuitka 编译环境")
        elif hasattr(sys, '_MEIPASS'):
            print("检测到 PyInstaller 打包环境")
            print(f"临时目录: {sys._MEIPASS}")
        else:
            print("检测到未知的打包环境")
    else:
        print("运行在开发环境")

    print(f"Python 版本: {sys.version}")
    print(f"可执行文件: {sys.executable}")
    print("=" * 60)
    print()

    # 创建并启动应用
    app = Application()

    print("\n应用已启动，访问以下端点测试：")
    print("  - http://localhost:8888/api/hello")
    print("  - http://localhost:8888/api/info")
    print("\n按 Ctrl+C 停止服务器\n")

    try:
        app.run()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")


if __name__ == '__main__':
    main()

