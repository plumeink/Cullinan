#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_nuitka.py - Nuitka build script for Cullinan applications

Advanced Nuitka build script with support for:
- Cross-platform builds (Windows/Linux/macOS)
- Standalone and Onefile modes
- GCC/MSVC/Clang compiler selection
- Optimization levels
- Icon and version info
- Custom C compiler flags

Usage:
    python build_nuitka.py                        # Default standalone
    python build_nuitka.py --onefile             # Single file
    python build_nuitka.py --compiler gcc        # Use GCC
    python build_nuitka.py --optimize            # Full optimization
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


# =============================================================================
# Platform Detection and Configuration
# =============================================================================

class PlatformConfig:
    """平台特定配置"""

    def __init__(self):
        self.system = platform.system()  # Windows, Linux, Darwin
        self.machine = platform.machine()  # x86_64, arm64, etc.
        self.is_windows = self.system == 'Windows'
        self.is_linux = self.system == 'Linux'
        self.is_macos = self.system == 'Darwin'

    def get_compiler_paths(self):
        """获取编译器路径配置"""
        if self.is_windows:
            return {
                'mingw64': self._find_mingw64_windows(),
                'msvc': self._find_msvc_windows(),
                'gcc': self._find_gcc_windows(),
                'clang': self._find_clang_windows(),
            }
        elif self.is_linux:
            return {
                'gcc': self._find_gcc_linux(),
                'clang': self._find_clang_linux(),
            }
        elif self.is_macos:
            return {
                'clang': self._find_clang_macos(),
                'gcc': self._find_gcc_macos(),
            }
        return {}

    def _find_mingw64_windows(self):
        """查找 Windows 上的 MinGW64"""
        search_paths = [
            Path(r'C:\msys64\mingw64\bin'),
            Path(r'C:\msys64\ucrt64\bin'),
            Path(r'C:\mingw64\bin'),
            Path(r'C:\MinGW\bin'),
            Path(os.environ.get('MINGW_HOME', '')) / 'bin',
        ]

        for path in search_paths:
            if path.exists() and (path / 'gcc.exe').exists():
                return path
        return None

    def _find_msvc_windows(self):
        """查找 Windows 上的 MSVC"""
        # MSVC 通常由 Nuitka 自动检测
        return 'auto'

    def _find_gcc_windows(self):
        """查找 Windows 上的 GCC"""
        return self._find_mingw64_windows()

    def _find_clang_windows(self):
        """查找 Windows 上的 Clang"""
        search_paths = [
            Path(r'C:\Program Files\LLVM\bin'),
            Path(r'C:\msys64\clang64\bin'),
        ]

        for path in search_paths:
            if path.exists() and (path / 'clang.exe').exists():
                return path
        return None

    def _find_gcc_linux(self):
        """查找 Linux 上的 GCC"""
        return 'gcc'  # 通常在 PATH 中

    def _find_clang_linux(self):
        """查找 Linux 上的 Clang"""
        return 'clang'  # 通常在 PATH 中

    def _find_clang_macos(self):
        """查找 macOS 上的 Clang"""
        return 'clang'  # Xcode Command Line Tools

    def _find_gcc_macos(self):
        """查找 macOS 上的 GCC"""
        # macOS 上的 gcc 通常是 clang 的别名
        # 真正的 GCC 需要通过 Homebrew 安装
        gcc_versions = ['gcc-13', 'gcc-12', 'gcc-11', 'gcc']
        for gcc in gcc_versions:
            try:
                result = subprocess.run(
                    ['which', gcc],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return gcc
            except:
                pass
        return None

    def get_default_compiler(self):
        """获取平台默认编译器"""
        if self.is_windows:
            return 'mingw64'
        elif self.is_linux:
            return 'gcc'
        elif self.is_macos:
            return 'clang'
        return None

    def get_available_compilers(self):
        """获取可用的编译器列表"""
        compilers = self.get_compiler_paths()
        return [name for name, path in compilers.items() if path]


# =============================================================================
# Build Functions
# =============================================================================

def build_nuitka(args, platform_config):
    """Build with Nuitka"""

    # Find entry point
    entry = Path(args.entry).resolve()
    if not entry.exists():
        print(f"Error: Entry point not found: {args.entry}")
        return 1

    print(f"Platform: {platform_config.system} ({platform_config.machine})")
    print(f"Entry point: {entry}")
    print(f"Mode: {'Onefile' if args.onefile else 'Standalone'}")
    print(f"Output: {args.output}")
    print()

    # Build command
    cmd = [sys.executable, '-m', 'nuitka', str(entry)]

    # Mode
    if args.onefile:
        cmd.append('--onefile')
    else:
        cmd.append('--standalone')

    # Output directory
    cmd.extend([
        f'--output-dir={args.output}',
        '--remove-output',
        '--follow-imports',
    ])

    # Compiler selection
    compiler = args.compiler or platform_config.get_default_compiler()
    if compiler:
        compiler_paths = platform_config.get_compiler_paths()

        if compiler == 'mingw64' and platform_config.is_windows:
            mingw_path = compiler_paths.get('mingw64')
            if mingw_path:
                print(f"Using MinGW64 from: {mingw_path}")
                cmd.append('--mingw64')
                # 设置 PATH
                os.environ['PATH'] = str(mingw_path) + os.pathsep + os.environ['PATH']
            else:
                print("Warning: MinGW64 not found, using default compiler")
        elif compiler == 'msvc' and platform_config.is_windows:
            cmd.append('--msvc=latest')
        elif compiler == 'gcc':
            if platform_config.is_windows:
                gcc_path = compiler_paths.get('gcc')
                if gcc_path:
                    os.environ['PATH'] = str(gcc_path) + os.pathsep + os.environ['PATH']
            cmd.append('--gcc')
        elif compiler == 'clang':
            if platform_config.is_windows:
                clang_path = compiler_paths.get('clang')
                if clang_path:
                    os.environ['PATH'] = str(clang_path) + os.pathsep + os.environ['PATH']
            cmd.append('--clang')

    # Optimization
    if args.optimize:
        cmd.extend([
            '--lto=yes',  # Link Time Optimization
        ])
        if not platform_config.is_macos:  # macOS 可能不支持某些插件
            cmd.append('--enable-plugin=anti-bloat')

    # Jobs
    if args.jobs:
        cmd.append(f'--jobs={args.jobs}')
    else:
        try:
            import multiprocessing
            jobs = max(1, multiprocessing.cpu_count() // 2)
            cmd.append(f'--jobs={jobs}')
        except:
            pass

    # Icon (platform-specific)
    if args.icon:
        icon_path = Path(args.icon)
        if platform_config.is_windows:
            if icon_path.suffix.lower() in ['.ico', '.exe']:
                cmd.append(f'--windows-icon-from-ico={icon_path}')
        elif platform_config.is_macos:
            if icon_path.suffix.lower() == '.icns':
                cmd.append(f'--macos-app-icon={icon_path}')
        elif platform_config.is_linux:
            if icon_path.suffix.lower() in ['.png', '.svg']:
                cmd.append(f'--linux-onefile-icon={icon_path}')

    # Console mode (platform-specific)
    if args.no_console:
        if platform_config.is_windows:
            cmd.append('--windows-disable-console')
        elif platform_config.is_macos:
            cmd.append('--macos-create-app-bundle')

    # Include Cullinan
    cmd.append('--include-package=cullinan')

    # Include user package
    if args.package:
        cmd.append(f'--include-package={args.package}')
    else:
        # Auto-detect from entry point
        entry_dir = entry.parent
        if (entry_dir / '__init__.py').exists():
            package = entry_dir.name
            cmd.append(f'--include-package={package}')
            print(f"Auto-detected package: {package}")

    # Extra arguments
    if args.extra:
        cmd.extend(args.extra)

    # Print command
    print("="*60)
    print("Nuitka Command:")
    print("="*60)
    print(' '.join(cmd))
    print()

    # Execute
    print("="*60)
    print("Building...")
    print("="*60)
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print()
        print("="*60)
        print("Build completed successfully!")
        print(f"Output directory: {args.output}")
        print("="*60)
    else:
        print()
        print("="*60)
        print("Build failed!")
        print("="*60)

    return result.returncode


def main():
    # 创建平台配置
    platform_config = PlatformConfig()

    # 获取可用编译器
    available_compilers = platform_config.get_available_compilers()
    default_compiler = platform_config.get_default_compiler()

    parser = argparse.ArgumentParser(
        description='Build Cullinan applications with Nuitka',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Platform: {platform_config.system} ({platform_config.machine})
Available compilers: {', '.join(available_compilers) if available_compilers else 'None detected'}
Default compiler: {default_compiler or 'None'}

Examples:
  # Basic builds
  python build_nuitka.py                           # Default standalone
  python build_nuitka.py --onefile                # Single executable
  
  # With optimization
  python build_nuitka.py --optimize               # Full optimization
  python build_nuitka.py --onefile --optimize     # Optimized onefile
  
  # Compiler selection (platform-specific)
  python build_nuitka.py --compiler gcc           # Use GCC
  python build_nuitka.py --compiler mingw64       # Use MinGW64 (Windows)
  python build_nuitka.py --compiler msvc          # Use MSVC (Windows)
  python build_nuitka.py --compiler clang         # Use Clang
  
  # With icon (platform-specific formats)
  python build_nuitka.py --icon app.ico           # Windows (.ico)
  python build_nuitka.py --icon app.icns          # macOS (.icns)
  python build_nuitka.py --icon app.png           # Linux (.png)
        """
    )

    parser.add_argument(
        '--entry', '-e',
        default='main.py',
        help='Entry point Python file (default: main.py)'
    )

    parser.add_argument(
        '--onefile',
        action='store_true',
        help='Build as single file (default: standalone folder)'
    )

    parser.add_argument(
        '--output', '-o',
        default='dist',
        help='Output directory (default: dist)'
    )

    # 动态生成编译器选项
    compiler_choices = available_compilers if available_compilers else None
    parser.add_argument(
        '--compiler', '-c',
        choices=compiler_choices,
        help=f'C compiler to use (available: {", ".join(available_compilers) if available_compilers else "auto-detect"})'
    )

    parser.add_argument(
        '--optimize',
        action='store_true',
        help='Enable full optimization (LTO, anti-bloat)'
    )

    parser.add_argument(
        '--jobs', '-j',
        type=int,
        help='Number of parallel jobs'
    )

    parser.add_argument(
        '--package', '-p',
        help='Main package to include (auto-detected if not specified)'
    )

    parser.add_argument(
        '--icon',
        help='Path to icon file (.ico for Windows, .icns for macOS, .png for Linux)'
    )

    parser.add_argument(
        '--no-console',
        action='store_true',
        help='Disable console window (GUI mode)'
    )

    parser.add_argument(
        '--extra',
        nargs='*',
        help='Extra arguments to pass to Nuitka'
    )

    args = parser.parse_args()

    try:
        return build_nuitka(args, platform_config)
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        return 1


if __name__ == '__main__':
    sys.exit(main())

