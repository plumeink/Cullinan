# Cullinan Packaging Guide

This guide explains how to package a Cullinan web application using Nuitka and PyInstaller.

## Overview

The Cullinan framework now fully supports packaging with Nuitka and PyInstaller, including `onefile` and `onedir`/`standalone` modes. The framework automatically detects the runtime environment and uses the appropriate module scanning strategy.

## Packaging Environment Detection

The framework has a built-in intelligent environment detection mechanism:

-   **Nuitka Detection**: Detects the `__compiled__` attribute and `sys.frozen`.
-   **PyInstaller Detection**: Detects `sys.frozen` and `sys._MEIPASS`.
-   **Mode Recognition**: Automatically identifies `onefile` and `standalone`/`onedir` modes.

## Nuitka Packaging

### Standalone Mode (Recommended)

```bash
nuitka --standalone \
       --enable-plugin=tornado \
       --include-package=your_app \
       --include-package-data=your_app \
       --output-dir=dist \
       your_app/main.py
```

### Onefile Mode

```bash
nuitka --onefile \
       --enable-plugin=tornado \
       --include-package=your_app \
       --include-package-data=your_app \
       --output-dir=dist \
       your_app/main.py
```

### Key Parameter Explanations

-   `--standalone` / `--onefile`: Packaging mode.
-   `--enable-plugin=tornado`: Enables the Tornado plugin (if used).
-   `--include-package=your_app`: Includes your application package.
-   `--include-package-data=your_app`: Includes package data files.

### Nuitka Module Scanning Strategy

Cullinan uses the following scanning strategies in a Nuitka environment:

1.  **`sys.modules` Scanning**: Scans already loaded modules (Nuitka preloads included modules).
2.  **Directory Scanning** (Standalone mode): Scans `.pyd`/`.so` files in the executable's directory.
3.  **Package Inference** (Onefile mode): Infers the package name from the call stack and scans it.
4.  **`__main__` Scanning**: Scans from the main module's path.

## PyInstaller Packaging

### Onedir Mode (Recommended)

```bash
pyinstaller --onedir \
            --hidden-import=your_app \
            --collect-all=your_app \
            --name=your_app \
            your_app/main.py
```

### Onefile Mode

```bash
pyinstaller --onefile \
            --hidden-import=your_app \
            --collect-all=your_app \
            --name=your_app \
            your_app/main.py
```

### Key Parameter Explanations

-   `--onefile` / `--onedir`: Packaging mode.
-   `--hidden-import=your_app`: Declares hidden imports.
-   `--collect-all=your_app`: Collects all package data.

### PyInstaller Module Scanning Strategy

Cullinan uses the following scanning strategies in a PyInstaller environment:

1.  **`_MEIPASS` Scanning**: Scans the temporary directory where PyInstaller extracts files.
2.  **Executable Directory Scanning** (Onedir mode).
3.  **`sys.modules` Supplemental Scanning**: Scans already imported modules.

## Best Practices

### 1. Explicitly Import Key Modules

Although the framework scans automatically, it is recommended to explicitly import key modules in your main file:

```python
# main.py
from cullinan import Application

# Explicitly import controllers and services (optional, but recommended)
from your_app import controllers
from your_app import services

app = Application()
app.run()
```

### 2. Use a Package Structure

Recommended project structure:

```
your_app/
├── __init__.py
├── main.py
├── controllers/
│   ├── __init__.py
│   ├── user_controller.py
│   └── product_controller.py
└── services/
    ├── __init__.py
    ├── user_service.py
    └── product_service.py
```

### 3. Import in `__init__.py`

Import all sub-modules in the package's `__init__.py`:

```python
# controllers/__init__.py
from . import user_controller
from . import product_controller

# services/__init__.py
from . import user_service
from . import product_service
```

### 4. Nuitka-Specific Considerations

For Nuitka, ensure all required modules are included:

```bash
# Use --include-module to explicitly include specific modules
nuitka --standalone \
       --include-package=your_app \
       --include-module=your_app.controllers.user_controller \
       --include-module=your_app.services.user_service \
       your_app/main.py
```

### 5. PyInstaller Spec File

Create a `.spec` file for finer control:

```python
# your_app.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['your_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'your_app.controllers.user_controller',
        'your_app.services.user_service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='your_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='your_app',
)
```

## Debugging Packaging Issues

### Enable Verbose Logging

The framework uses Python's `logging` module. Enable `DEBUG` level to see detailed scanning information:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

from cullinan import Application
app = Application()
app.run()
```

### Example Log Output

```
INFO:cullinan.application: ||| Starting module discovery...
INFO:cullinan.application: ||| === Using Nuitka scanning strategy ===
INFO:cullinan.application: ||| Detected Nuitka compiled environment
INFO:cullinan.application: ||| Nuitka mode: standalone
INFO:cullinan.application: ||| Scanning Nuitka standalone directory: C:\app\dist
INFO:cullinan.application: ||| Found 15 modules via Nuitka scanning
INFO:cullinan.application: ||| Discovered 15 modules
```

### Common Troubleshooting

#### Problem: Controller or Service Not Scanned

**Solution**:
1.  Confirm the module is packaged (check the packaging output).
2.  Explicitly import the module in the main file.
3.  Use `--include-module` or `--hidden-import` to explicitly include it.

#### Problem: Import Error

**Solution**:
1.  Check if the module path is correct.
2.  Ensure `__init__.py` files exist.
3.  Check for circular imports.

#### Problem: Modules Missing in Onefile Mode

**Solution**:
1.  Prefer `standalone`/`onedir` mode.
2.  Use explicit imports.
3.  Check the data collection options of your packaging tool.

## Testing the Packaged Result

### Development Environment Testing

```bash
python your_app/main.py
```

### Nuitka Packaging Test

```bash
# Standalone
cd dist/your_app.dist
./your_app

# Onefile
cd dist
./your_app
```

### PyInstaller Packaging Test

```bash
# Onedir
cd dist/your_app
./your_app

# Onefile
cd dist
./your_app
```

## Performance Optimization

### Nuitka Optimization

```bash
nuitka --standalone \
       --lto=yes \
       --enable-plugin=anti-bloat \
       --remove-output \
       your_app/main.py
```

### PyInstaller Optimization

```bash
pyinstaller --onefile \
            --optimize=2 \
            --strip \
            --upx-dir=/path/to/upx \
            your_app/main.py
```

## Summary

The Cullinan framework now fully supports major packaging tools and can automatically adapt to different packaging environments. Following the best practices in this guide will ensure your application runs correctly after being packaged.

If you encounter any issues, please check the detailed logs or submit an Issue.

