# -*- coding: utf-8 -*-
"""
Cullinan Framework - Enhanced Nuitka Build Script

This script provides optimized Nuitka building for Cullinan applications
with proper handling of all packaging modes and edge cases.

Usage:
    python scripts/build_nuitka_enhanced.py
    python scripts/build_nuitka_enhanced.py --onefile
    python scripts/build_nuitka_enhanced.py --standalone
    python scripts/build_nuitka_enhanced.py --help
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def build_nuitka(
    entry_point: str,
    app_name: str,
    mode: str = "onefile",
    include_packages: list = None,
    include_data_files: list = None,
    include_data_dirs: list = None,
    output_dir: str = "dist",
    enable_console: bool = True,
    optimize: bool = True,
    debug: bool = False,
):
    """Build application using Nuitka with optimized settings.

    Args:
        entry_point: Main Python file (e.g., 'application.py', 'main.py')
        app_name: Output executable name (without extension)
        mode: 'onefile' or 'standalone'
        include_packages: List of packages to include explicitly
        include_data_files: List of (source, dest) tuples for data files
        include_data_dirs: List of (source_dir, dest_dir) tuples for directories
        output_dir: Output directory
        enable_console: Show console window (Windows)
        optimize: Enable optimizations
        debug: Enable debug mode (verbose output)
    """

    if include_packages is None:
        include_packages = []
    if include_data_files is None:
        include_data_files = []
    if include_data_dirs is None:
        include_data_dirs = []

    # Build command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
    ]

    # Mode selection
    if mode == "onefile":
        cmd.append("--onefile")
        print(f"📦 Building in ONEFILE mode")
    else:
        print(f"📦 Building in STANDALONE mode")

    # Output configuration
    cmd.extend([
        f"--output-dir={output_dir}",
        f"--output-filename={app_name}",
    ])

    # Console mode (Windows)
    if sys.platform == "win32":
        if enable_console:
            cmd.append("--windows-console-mode=attach")
        else:
            cmd.append("--windows-console-mode=disable")

    # Optimization plugins
    if optimize:
        cmd.extend([
            "--enable-plugin=anti-bloat",
            "--prefer-source-code",
        ])

    # Debug mode
    if debug:
        cmd.extend([
            "--verbose",
            "--show-progress",
            "--show-modules",
        ])

    # Always include cullinan package
    if "cullinan" not in include_packages:
        include_packages.insert(0, "cullinan")

    # Include packages
    for package in include_packages:
        cmd.append(f"--include-package={package}")
        print(f"  📚 Including package: {package}")

    # Include data files
    for source, dest in include_data_files:
        cmd.append(f"--include-data-file={source}={dest}")
        print(f"  📄 Including file: {source} -> {dest}")

    # Include data directories
    for source_dir, dest_dir in include_data_dirs:
        cmd.append(f"--include-data-dir={source_dir}={dest_dir}")
        print(f"  📁 Including directory: {source_dir} -> {dest_dir}")

    # Entry point (last argument)
    cmd.append(entry_point)

    # Print command
    print("\n" + "="*70)
    print("🔨 Nuitka Build Command:")
    print("="*70)
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
        print("❌ Nuitka not found!")
        print("="*70)
        print("Please install Nuitka: pip install nuitka")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Build Cullinan application with Nuitka",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build onefile executable
  python build_nuitka_enhanced.py --entry application.py --app myapp --onefile
  
  # Build standalone with packages
  python build_nuitka_enhanced.py --entry main.py --app myapp --standalone \\
      --include-package myapp --include-package myapp.controllers
  
  # Build with data files
  python build_nuitka_enhanced.py --entry app.py --app myapp \\
      --include-data-file config.yaml=config.yaml \\
      --include-data-dir templates=templates
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
        choices=["onefile", "standalone"],
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
        "--standalone",
        action="store_const",
        const="standalone",
        dest="mode",
        help="Build as standalone directory (shortcut for --mode standalone)"
    )

    parser.add_argument(
        "--include-package",
        action="append",
        dest="packages",
        default=[],
        help="Include package (can be used multiple times)"
    )

    parser.add_argument(
        "--include-data-file",
        action="append",
        dest="data_files",
        default=[],
        help="Include data file as 'source=dest' (can be used multiple times)"
    )

    parser.add_argument(
        "--include-data-dir",
        action="append",
        dest="data_dirs",
        default=[],
        help="Include data directory as 'source=dest' (can be used multiple times)"
    )

    parser.add_argument(
        "--output-dir",
        default="dist",
        help="Output directory (default: dist)"
    )

    parser.add_argument(
        "--no-console",
        action="store_true",
        help="Hide console window (Windows only)"
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

    # Parse data files
    data_files = []
    for item in args.data_files:
        if "=" not in item:
            print(f"❌ Error: Invalid data file format '{item}' (expected: source=dest)")
            sys.exit(1)
        source, dest = item.split("=", 1)
        data_files.append((source, dest))

    # Parse data directories
    data_dirs = []
    for item in args.data_dirs:
        if "=" not in item:
            print(f"❌ Error: Invalid data directory format '{item}' (expected: source=dest)")
            sys.exit(1)
        source, dest = item.split("=", 1)
        data_dirs.append((source, dest))

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
    success = build_nuitka(
        entry_point=args.entry,
        app_name=args.app,
        mode=args.mode,
        include_packages=args.packages,
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

