#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_pyinstaller.py - PyInstaller build script for Cullinan applications

PyInstaller build script with support for:
- Onedir and Onefile modes
- Icon and version info
- Hidden imports detection
- UPX compression

Usage:
    python build_pyinstaller.py                   # Default onedir
    python build_pyinstaller.py --onefile        # Single file
    python build_pyinstaller.py --upx            # Enable UPX compression
    python build_pyinstaller.py --icon app.ico   # Add icon
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def build_pyinstaller(args):
    """Build with PyInstaller"""

    # Find entry point
    entry = Path(args.entry).resolve()
    if not entry.exists():
        print(f"Error: Entry point not found: {args.entry}")
        return 1

    print(f"Entry point: {entry}")
    print(f"Mode: {'Onefile' if args.onefile else 'Onedir'}")
    print(f"Output: {args.distpath}")
    print()

    # Build command
    cmd = [sys.executable, '-m', 'PyInstaller', str(entry)]

    # Mode
    if args.onefile:
        cmd.append('--onefile')
    else:
        cmd.append('--onedir')

    # Output paths
    cmd.extend([
        f'--distpath={args.distpath}',
        f'--workpath={args.workpath}',
        f'--specpath={args.specpath}',
    ])

    # Clean
    if args.clean:
        cmd.append('--clean')

    # Console mode
    if args.no_console:
        cmd.append('--noconsole')
    elif args.console:
        cmd.append('--console')

    # Icon
    if args.icon:
        cmd.append(f'--icon={args.icon}')

    # Name
    if args.name:
        cmd.append(f'--name={args.name}')
    else:
        cmd.append(f'--name={entry.stem}')

    # UPX
    if args.upx:
        if args.upx_dir:
            cmd.append(f'--upx-dir={args.upx_dir}')
        else:
            cmd.append('--upx-dir=.')
    else:
        cmd.append('--noupx')

    # Hidden imports - Cullinan
    cmd.extend([
        '--hidden-import=cullinan',
        '--hidden-import=cullinan.config',
        '--hidden-import=cullinan.application',
        '--hidden-import=cullinan.controller',
        '--hidden-import=cullinan.service',
        '--collect-all=cullinan',
    ])

    # Hidden imports - User package
    if args.package:
        cmd.extend([
            f'--hidden-import={args.package}',
            f'--collect-all={args.package}',
        ])
    else:
        # Auto-detect from entry point
        entry_dir = entry.parent
        if (entry_dir / '__init__.py').exists():
            package = entry_dir.name
            cmd.extend([
                f'--hidden-import={package}',
                f'--collect-all={package}',
            ])
            print(f"Auto-detected package: {package}")

    # Data files
    if args.add_data:
        for data in args.add_data:
            cmd.append(f'--add-data={data}')

    # Extra arguments
    if args.extra:
        cmd.extend(args.extra)

    # Print command
    print("="*60)
    print("PyInstaller Command:")
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
        print(f"Output directory: {args.distpath}")
        print("="*60)
    else:
        print()
        print("="*60)
        print("Build failed!")
        print("="*60)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description='Build Cullinan applications with PyInstaller',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic builds
  python build_pyinstaller.py                      # Default onedir
  python build_pyinstaller.py --onefile           # Single executable
  
  # With compression
  python build_pyinstaller.py --upx               # Enable UPX
  python build_pyinstaller.py --onefile --upx     # Compressed onefile
  
  # Custom package
  python build_pyinstaller.py --package your_app  # Specify package
  
  # With icon and no console
  python build_pyinstaller.py --icon app.ico --no-console
  
  # With data files
  python build_pyinstaller.py --add-data "data;data" --add-data "config.json;."
  
  # Clean build
  python build_pyinstaller.py --clean --onefile
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
        help='Build as single file (default: onedir)'
    )

    parser.add_argument(
        '--distpath',
        default='dist',
        help='Output directory (default: dist)'
    )

    parser.add_argument(
        '--workpath',
        default='build',
        help='Work directory (default: build)'
    )

    parser.add_argument(
        '--specpath',
        default='.',
        help='Spec file directory (default: .)'
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean PyInstaller cache before building'
    )

    parser.add_argument(
        '--package', '-p',
        help='Main package to include (auto-detected if not specified)'
    )

    parser.add_argument(
        '--icon',
        help='Path to .ico file for Windows'
    )

    parser.add_argument(
        '--name', '-n',
        help='Name for the bundled app (default: entry filename)'
    )

    parser.add_argument(
        '--console',
        action='store_true',
        help='Show console window (default)'
    )

    parser.add_argument(
        '--no-console',
        action='store_true',
        help='Hide console window (GUI mode)'
    )

    parser.add_argument(
        '--upx',
        action='store_true',
        help='Enable UPX compression'
    )

    parser.add_argument(
        '--upx-dir',
        help='Path to UPX directory'
    )

    parser.add_argument(
        '--add-data',
        action='append',
        help='Add data files (format: src;dest)'
    )

    parser.add_argument(
        '--extra',
        nargs='*',
        help='Extra arguments to pass to PyInstaller'
    )

    args = parser.parse_args()

    try:
        return build_pyinstaller(args)
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        return 1


if __name__ == '__main__':
    sys.exit(main())

