#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_app.py - Universal build script for Cullinan-based applications
               Cullinan 应用的通用构建脚本

This script helps package Cullinan-based web applications using Nuitka or PyInstaller.
本脚本帮助使用 Nuitka 或 PyInstaller 打包基于 Cullinan 的 Web 应用程序。

Language / 语言:
    Set CULLINAN_LANG=zh for Chinese output
    设置 CULLINAN_LANG=zh 使用中文输出

Usage / 使用方法:
    python build_app.py                          # Interactive mode / 交互模式
    python build_app.py --tool nuitka            # Use Nuitka / 使用 Nuitka
    python build_app.py --tool pyinstaller       # Use PyInstaller / 使用 PyInstaller
    python build_app.py --mode onefile           # Single file mode / 单文件模式
    python build_app.py --entry your_app/main.py # Custom entry point / 自定义入口
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

# Language selection / 语言选择
LANG = os.getenv('CULLINAN_LANG', 'en')  # Default: en, Options: en, zh

MESSAGES = {
    'en': {
        'banner': 'Cullinan Application Builder',
        'platform': 'Platform',
        'python': 'Python',
        'root_dir': 'Root directory',
        'detecting_entry': 'Detecting entry point...',
        'found_entry': 'Found entry point',
        'select_tool': 'Select packaging tool',
        'select_mode': 'Select build mode',
        'building': 'Building application...',
        'build_complete': 'Build completed successfully!',
        'build_failed': 'Build failed!',
        'error': 'Error',
    },
    'zh': {
        'banner': 'Cullinan 应用构建器',
        'platform': '平台',
        'python': 'Python 版本',
        'root_dir': '根目录',
        'detecting_entry': '正在检测入口文件...',
        'found_entry': '找到入口文件',
        'select_tool': '选择打包工具',
        'select_mode': '选择构建模式',
        'building': '正在构建应用...',
        'build_complete': '构建成功完成！',
        'build_failed': '构建失败！',
        'error': '错误',
    }
}

def _(key, *args):
    """Get localized message / 获取本地化消息"""
    msg = MESSAGES.get(LANG, MESSAGES['en']).get(key, key)
    return msg.format(*args) if args else msg


class AppBuilder:
    """Application builder for Cullinan-based apps"""

    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir or os.getcwd()).resolve()
        self.python_exe = sys.executable
        self.system = platform.system()
        self.is_windows = self.system == 'Windows'
        self.is_linux = self.system == 'Linux'
        self.is_macos = self.system == 'Darwin'

    def find_entry_point(self):
        """Auto-detect application entry point"""
        # Common entry point patterns
        patterns = [
            'main.py',
            'app.py',
            'application.py',
            'run.py',
            '*/main.py',
            '*/app.py',
            '*/application.py',
        ]

        for pattern in patterns:
            matches = list(self.root_dir.glob(pattern))
            if matches:
                return matches[0]

        return None

    def find_packages(self, entry_point):
        """Find Python packages to include"""
        packages = set()

        # Get the package containing the entry point
        entry_dir = entry_point.parent

        # Find all packages from entry point directory
        for path in entry_dir.rglob('__init__.py'):
            package_dir = path.parent
            rel_path = package_dir.relative_to(self.root_dir)
            package_name = str(rel_path).replace(os.sep, '.')
            packages.add(package_name)

        return list(packages)

    def check_tool(self, tool):
        """Check if build tool is available"""
        try:
            cmd = [self.python_exe, '-m', tool, '--version']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def install_tool(self, tool):
        """Install build tool"""
        print(f"Installing {tool}...")
        cmd = [self.python_exe, '-m', 'pip', 'install', tool]
        result = subprocess.run(cmd)
        return result.returncode == 0

    def build_nuitka(self, entry_point, packages, mode='standalone', output_dir='dist', extra_args=None):
        """Build with Nuitka"""
        print(f"\n{'='*60}")
        print(f"Building with Nuitka ({mode} mode)")
        print(f"{'='*60}\n")

        cmd = [
            self.python_exe, '-m', 'nuitka',
            str(entry_point),
        ]

        # Mode
        if mode == 'onefile':
            cmd.append('--onefile')
        else:
            cmd.append('--standalone')

        # Output
        cmd.extend([
            f'--output-dir={output_dir}',
            '--remove-output',
            '--follow-imports',
        ])

        # Include Cullinan
        cmd.append('--include-package=cullinan')

        # Include user packages
        for pkg in packages:
            cmd.append(f'--include-package={pkg}')

        # Performance
        try:
            import multiprocessing
            jobs = max(1, multiprocessing.cpu_count() // 2)
            cmd.append(f'--jobs={jobs}')
        except:
            pass

        # Extra arguments
        if extra_args:
            cmd.extend(extra_args)

        # Print command
        print("Command:")
        print(' '.join(cmd))
        print()

        # Execute
        return subprocess.run(cmd).returncode

    def build_pyinstaller(self, entry_point, packages, mode='onedir', output_dir='dist', extra_args=None):
        """Build with PyInstaller"""
        print(f"\n{'='*60}")
        print(f"Building with PyInstaller ({mode} mode)")
        print(f"{'='*60}\n")

        cmd = [
            self.python_exe, '-m', 'PyInstaller',
            str(entry_point),
        ]

        # Mode
        if mode == 'onefile':
            cmd.append('--onefile')
        else:
            cmd.append('--onedir')

        # Output
        cmd.extend([
            f'--distpath={output_dir}',
            '--clean',
        ])

        # Include Cullinan
        cmd.extend([
            '--hidden-import=cullinan',
            '--collect-all=cullinan',
        ])

        # Include user packages
        for pkg in packages:
            cmd.extend([
                f'--hidden-import={pkg}',
                f'--collect-all={pkg}',
            ])

        # Extra arguments
        if extra_args:
            cmd.extend(extra_args)

        # Print command
        print("Command:")
        print(' '.join(cmd))
        print()

        # Execute
        return subprocess.run(cmd).returncode


def main():
    parser = argparse.ArgumentParser(
        description='Build Cullinan-based applications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_app.py                              # Interactive mode
  python build_app.py --tool nuitka                # Build with Nuitka
  python build_app.py --tool pyinstaller           # Build with PyInstaller
  python build_app.py --mode onefile               # Single file mode
  python build_app.py --entry your_app/main.py     # Custom entry point
  python build_app.py --tool nuitka --mode onefile # Nuitka onefile
        """
    )

    parser.add_argument(
        '--entry', '-e',
        help='Application entry point (auto-detected if not specified)'
    )

    parser.add_argument(
        '--tool', '-t',
        choices=['nuitka', 'pyinstaller'],
        help='Build tool to use'
    )

    parser.add_argument(
        '--mode', '-m',
        choices=['standalone', 'onedir', 'onefile'],
        help='Build mode'
    )

    parser.add_argument(
        '--output', '-o',
        default='dist',
        help='Output directory (default: dist)'
    )

    parser.add_argument(
        '--extra-args',
        nargs='*',
        help='Extra arguments to pass to build tool'
    )

    args = parser.parse_args()

    # Create builder
    builder = AppBuilder()

    # Find or validate entry point
    if args.entry:
        entry_point = Path(args.entry).resolve()
        if not entry_point.exists():
            print(f"Error: Entry point not found: {args.entry}")
            return 1
    else:
        print("Auto-detecting entry point...")
        entry_point = builder.find_entry_point()
        if not entry_point:
            print("Error: Could not find entry point. Please specify with --entry")
            return 1

    print(f"Entry point: {entry_point}")

    # Find packages
    print("Scanning packages...")
    packages = builder.find_packages(entry_point)
    print(f"Found packages: {', '.join(packages) if packages else 'none'}")

    # Select tool
    tool = args.tool
    if not tool:
        # Interactive selection
        print("\nAvailable build tools:")
        print("  1. Nuitka (recommended for production)")
        print("  2. PyInstaller (faster build)")

        choice = input("\nSelect tool (1/2): ").strip()
        tool = 'nuitka' if choice == '1' else 'pyinstaller'

    # Check and install tool
    if not builder.check_tool(tool):
        print(f"\n{tool} not found.")
        install = input(f"Install {tool}? (y/n): ").strip().lower()
        if install == 'y':
            if not builder.install_tool(tool):
                print(f"Failed to install {tool}")
                return 1
        else:
            return 1

    # Select mode
    mode = args.mode
    if not mode:
        print("\nBuild modes:")
        print("  1. Standalone/Onedir (folder with exe)")
        print("  2. Onefile (single exe file)")

        choice = input("\nSelect mode (1/2): ").strip()
        if tool == 'nuitka':
            mode = 'standalone' if choice == '1' else 'onefile'
        else:
            mode = 'onedir' if choice == '1' else 'onefile'

    # Normalize mode
    if mode == 'standalone' and tool == 'pyinstaller':
        mode = 'onedir'
    elif mode == 'onedir' and tool == 'nuitka':
        mode = 'standalone'

    # Build
    if tool == 'nuitka':
        result = builder.build_nuitka(
            entry_point, packages, mode, args.output, args.extra_args
        )
    else:
        result = builder.build_pyinstaller(
            entry_point, packages, mode, args.output, args.extra_args
        )

    if result == 0:
        print(f"\n{'='*60}")
        print("Build completed successfully!")
        print(f"Output: {args.output}/")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("Build failed!")
        print(f"{'='*60}")

    return result


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        sys.exit(1)
