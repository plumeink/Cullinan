# -*- coding: utf-8 -*-
"""
Cullinan Framework - Enhanced PyInstaller Build Script

This script provides optimized PyInstaller building for Cullinan applications
with proper handling of all packaging modes and edge cases.

Usage:
    python scripts/build_pyinstaller_enhanced.py
    python scripts/build_pyinstaller_enhanced.py --onefile
    python scripts/build_pyinstaller_enhanced.py --onedir
    python scripts/build_pyinstaller_enhanced.py --help
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def build_pyinstaller(
    entry_point: str,
    app_name: str,
    mode: str = "onefile",
    include_packages: list = None,
    hidden_imports: list = None,
    include_data_files: list = None,
    include_data_dirs: list = None,
    output_dir: str = "dist",
    enable_console: bool = True,
    optimize: bool = True,
    debug: bool = False,
):
    """Build application using PyInstaller with optimized settings.

    Args:
        entry_point: Main Python file (e.g., 'application.py', 'main.py')
        app_name: Output executable name (without extension)
        mode: 'onefile' or 'onedir'
        include_packages: List of packages to collect all submodules
        hidden_imports: List of hidden imports to include
        include_data_files: List of (source, dest) tuples for data files
        include_data_dirs: List of (source_dir, dest_dir) tuples for directories
        output_dir: Output directory
        enable_console: Show console window
        optimize: Enable optimizations
        debug: Enable debug mode (verbose output)
    """

    if include_packages is None:
        include_packages = []
    if hidden_imports is None:
        hidden_imports = []
    if include_data_files is None:
        include_data_files = []
    if include_data_dirs is None:
        include_data_dirs = []

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
    ]

    # Mode selection
    if mode == "onefile":
        cmd.append("--onefile")
        print(f"📦 Building in ONEFILE mode")
    else:
        cmd.append("--onedir")
        print(f"📦 Building in ONEDIR mode")

    # Output configuration
    cmd.extend([
        f"--distpath={output_dir}",
        f"--name={app_name}",
    ])

    # Console mode
    if not enable_console:
        cmd.append("--noconsole")
    else:
        cmd.append("--console")

    # Clean build
    cmd.append("--clean")

    # Optimization
    if optimize:
        cmd.extend([
            "--strip",  # Strip debug symbols
            "--optimize=2",  # Python optimization level
        ])

    # Debug mode
    if debug:
        cmd.append("--debug=all")

    # Always include cullinan package
    if "cullinan" not in include_packages:
        include_packages.insert(0, "cullinan")

    # Collect all submodules from packages
    for package in include_packages:
        cmd.append(f"--collect-all={package}")
        print(f"  📚 Collecting package: {package}")

    # Hidden imports
    for hidden_import in hidden_imports:
        cmd.append(f"--hidden-import={hidden_import}")
        print(f"  🔍 Hidden import: {hidden_import}")

    # Include data files
    for source, dest in include_data_files:
        cmd.append(f"--add-data={source}{os.pathsep}{dest}")
        print(f"  📄 Including file: {source} -> {dest}")

    # Include data directories
    for source_dir, dest_dir in include_data_dirs:
        cmd.append(f"--add-data={source_dir}{os.pathsep}{dest_dir}")
        print(f"  📁 Including directory: {source_dir} -> {dest_dir}")

    # Entry point (last argument)
    cmd.append(entry_point)

    # Print command
    print("\n" + "="*70)
    print("🔨 PyInstaller Build Command:")
    print("="*70)
    if sys.platform == "win32":
        print(" ^\n    ".join(cmd))
    else:
        print(" \\\n    ".join(cmd))
    print("="*70 + "\n")

    # Execute build
    try:
        print("🚀 Starting build process...\n")
        result = subprocess.run(cmd, check=True)

        print("\n" + "="*70)
        print("✅ Build completed successfully!")
        print("="*70)
        print(f"📦 Output: {output_dir}/{app_name}")

        return True

    except subprocess.CalledProcessError as e:
        print("\n" + "="*70)
        print("❌ Build failed!")
        print("="*70)
        print(f"Error code: {e.returncode}")
        return False
    except FileNotFoundError:
        print("\n" + "="*70)
        print("❌ PyInstaller not found!")
        print("="*70)
        print("Please install PyInstaller: pip install pyinstaller")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Build Cullinan application with PyInstaller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build onefile executable
  python build_pyinstaller_enhanced.py --entry application.py --app myapp --onefile
  
  # Build onedir with packages
  python build_pyinstaller_enhanced.py --entry main.py --app myapp --onedir \\
      --collect-all myapp
  
  # Build with data files
  python build_pyinstaller_enhanced.py --entry app.py --app myapp \\
      --add-data config.yaml=config.yaml \\
      --add-data templates=templates
        """
    )

    parser.add_argument(
        "--entry",
        default="application.py",
        help="Entry point Python file (default: application.py)"
    )

    parser.add_argument(
        "--app",
        default="app",
        help="Output executable name (default: app)"
    )

    parser.add_argument(
        "--mode",
        choices=["onefile", "onedir"],
        default="onefile",
        help="Build mode (default: onefile)"
    )

    parser.add_argument(
        "--onefile",
        action="store_const",
        const="onefile",
        dest="mode",
        help="Build as single file (shortcut for --mode onefile)"
    )

    parser.add_argument(
        "--onedir",
        action="store_const",
        const="onedir",
        dest="mode",
        help="Build as directory (shortcut for --mode onedir)"
    )

    parser.add_argument(
        "--collect-all",
        action="append",
        dest="packages",
        default=[],
        help="Collect all submodules from package (can be used multiple times)"
    )

    parser.add_argument(
        "--hidden-import",
        action="append",
        dest="hidden_imports",
        default=[],
        help="Hidden import to include (can be used multiple times)"
    )

    parser.add_argument(
        "--add-data",
        action="append",
        dest="data_items",
        default=[],
        help="Add data file/dir as 'source=dest' (can be used multiple times)"
    )

    parser.add_argument(
        "--output-dir",
        default="dist",
        help="Output directory (default: dist)"
    )

    parser.add_argument(
        "--no-console",
        action="store_true",
        help="Hide console window"
    )

    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Disable optimizations"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug/verbose output"
    )

    args = parser.parse_args()

    # Validate entry point
    if not os.path.exists(args.entry):
        print(f"❌ Error: Entry point '{args.entry}' not found")
        sys.exit(1)

    # Parse data items (files and directories)
    data_files = []
    data_dirs = []
    for item in args.data_items:
        if "=" not in item:
            print(f"❌ Error: Invalid data format '{item}' (expected: source=dest)")
            sys.exit(1)
        source, dest = item.split("=", 1)

        # Determine if source is file or directory
        if os.path.isdir(source):
            data_dirs.append((source, dest))
        else:
            data_files.append((source, dest))

    # Print configuration
    print("\n" + "="*70)
    print("🔧 Build Configuration")
    print("="*70)
    print(f"  Entry Point:    {args.entry}")
    print(f"  App Name:       {args.app}")
    print(f"  Mode:           {args.mode}")
    print(f"  Output Dir:     {args.output_dir}")
    print(f"  Console:        {'Enabled' if not args.no_console else 'Disabled'}")
    print(f"  Optimization:   {'Enabled' if not args.no_optimize else 'Disabled'}")
    print(f"  Debug:          {'Enabled' if args.debug else 'Disabled'}")
    print("="*70 + "\n")

    # Build
    success = build_pyinstaller(
        entry_point=args.entry,
        app_name=args.app,
        mode=args.mode,
        include_packages=args.packages,
        hidden_imports=args.hidden_imports,
        include_data_files=data_files,
        include_data_dirs=data_dirs,
        output_dir=args.output_dir,
        enable_console=not args.no_console,
        optimize=not args.no_optimize,
        debug=args.debug,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

