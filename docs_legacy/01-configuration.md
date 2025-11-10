# Cullinan Configuration System Guide

## Overview

Cullinan now supports precise specification of user packages through a configuration file, completely solving the module scanning problem in a packaged environment. This is a more professional and elegant solution!

## Why is Configuration Needed?

### Problems with the Traditional Approach

1.  **Difficult to Maintain `EXCLUDE_PREFIXES`**: Requires constantly adding packages to exclude.
2.  **Inaccurate Scanning**: May scan unnecessary modules.
3.  **Fails After Packaging**: Nuitka/PyInstaller changes the file structure.

### Advantages of the Configuration Approach

1.  **Precise Control**: Scans only the specified packages.
2.  **Packaging-Friendly**: Works with all packaging tools.
3.  **Easy to Maintain**: Clear and concise configuration.
4.  **Zero Intrusion**: No need to modify business logic code.

## Quick Start

### Method 1: Code-based Configuration (Recommended)

```python
# your_app/application.py

from cullinan import configure, Application

# Configure before creating the Application instance
configure(
    user_packages=['your_app'],  # Your package name
    verbose=True                 # Optional: Enable verbose logging
)

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
```

**It's that simple!** The framework will automatically scan all modules under the `your_app` package.

### Method 2: JSON Configuration File

Create a `cullinan.json` file:

```json
{
  "user_packages": [
    "your_app"
  ],
  "verbose": true,
  "auto_scan": false
}
```

Load it in your code:

```python
import json
from cullinan import get_config, application

# Load configuration
with open('cullinan.json', 'r') as f:
    config_data = json.load(f)
    get_config().from_dict(config_data)

app = application
app.run()
```

### Method 3: Environment Variables

```bash
# Set environment variables (Linux / macOS)
export CULLINAN_USER_PACKAGES=your_app,myapp.controllers

# Windows
set CULLINAN_USER_PACKAGES=your_app,myapp.controllers
```

```python
import os
from cullinan import configure, Application

# Load from environment variables
if os.getenv('CULLINAN_USER_PACKAGES'):
    packages = os.getenv('CULLINAN_USER_PACKAGES').split(',')
    configure(user_packages=packages)

app = Application()
app.run()
```

## Configuration Options Explained

### `user_packages` (List[str])

Specifies the list of user packages to scan:

```python
configure(
    user_packages=[
        'your_app',              # Scan the entire package
        'myapp.controllers',     # Scan only controllers
        'myapp.services'         # Scan only services
    ]
)
```

**How it works:**
1.  Imports the specified packages.
2.  Uses `pkgutil.walk_packages` to recursively scan all sub-modules.
3.  Automatically imports all modules, triggering decorators.

### `verbose` (bool)

Enables detailed logging to see the scanning process:

```python
configure(verbose=True)
```

### `auto_scan` (bool)

Enables or disables automatic scanning (fallback strategy):

```python
configure(
    user_packages=['your_app'],
    auto_scan=False  # Disable auto-scan, use only configured packages
)
```

-   `True` (default): If configured packages fail to import, attempts to auto-scan.
-   `False`: Strict mode, uses only the configured packages.

### `project_root` (str)

The project root directory (usually auto-detected):

```python
configure(project_root='/path/to/project')
```

### `exclude_packages` (List[str])

A list of package names to exclude (used for `auto_scan`):

```python
configure(
    exclude_packages=['test', 'tests', '__pycache__']
)
```

## Best Practices for Packaging

### Nuitka Packaging

#### Standalone Mode

```python
# your_app/application.py

from cullinan import configure, Application

# Configure (before Application)
configure(
    user_packages=['your_app'],
    auto_scan=False  # Strict mode
)

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
```

**Packaging Command:**

```bash
nuitka --standalone \
       --include-package=your_app \
       --include-package=cullinan \
       your_app/application.py
```

**No longer need** to specify modules one by one with `--include-module`.

#### Onefile Mode

Configuration is the same. Packaging command:

```bash
nuitka --onefile \
       --include-package=your_app \
       --include-package=cullinan \
       your_app/application.py
```

### PyInstaller Packaging

#### Onedir Mode

```python
from cullinan import configure, Application

configure(user_packages=['your_app'])

app = Application()
app.run()
```

**Packaging Command:**

```bash
pyinstaller --onedir \
            --hidden-import=your_app \
            --collect-all=your_app \
            --collect-all=cullinan \
            application.py
```

#### Onefile Mode

Configuration is the same. Packaging command:

```bash
pyinstaller --onefile \
            --hidden-import=your_app \
            --collect-all=your_app \
            --collect-all=cullinan \
            application.py
```

## How It Works

### Development Environment

1.  Reads the `user_packages` configuration.
2.  Tries to import each package.
3.  Uses `pkgutil.walk_packages` to scan sub-modules.
4.  Imports all sub-modules, triggering decorators.

### Nuitka Packaging

1.  Reads the `user_packages` configuration.
2.  **Imports packages** (Nuitka has already compiled the modules).
3.  Scans sub-modules (via `pkg.__path__`).
4.  Fallback: If a package cannot be imported, searches `sys.modules`.

### PyInstaller Packaging

1.  Reads the `user_packages` configuration.
2.  **Imports packages** (PyInstaller has already included them).
3.  Scans sub-modules.
4.  Fallback: Directory scanning (if `auto_scan` is enabled).

## Complete Example

### `your_app` Project Configuration

```python
# your_app/application.py

import logging
from cullinan import configure, Application

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure Cullinan
configure(
    user_packages=['your_app'],  # Specify the package
    verbose=True,                # See the scanning process
    auto_scan=False              # Strict mode
)

def main():
    # Verify configuration
    from cullinan import get_config
    config = get_config()
    print(f"Configured packages: {config.user_packages}")
    
    # Create the application
    app = Application()
    
    # Verify Controllers
    from cullinan.controller import handler_list
    print(f"Registered handlers: {len(handler_list)}")
    
    # Start
    app.run()

if __name__ == '__main__':
    main()
```

### Log Output

With the correct configuration, you will see:

```
Configured packages: ['your_app']

INFO:cullinan.application: Starting module discovery...
INFO:cullinan.application: === Using Nuitka scanning strategy ===
INFO:cullinan.application: Using configured user packages: ['your_app']
INFO:cullinan.application: Found 11 modules from configured packages
INFO:cullinan.application: Successfully imported: your_app.controller
INFO:cullinan.application: Successfully imported: your_app.hooks
...

Registered handlers: 5
```

## Comparison: Before vs. After Configuration

### Before (The Problem)

```
INFO: Found 0 user modules in sys.modules  # The issue
INFO: Only __main__ found
```

**Reason**: The framework doesn't know which packages to scan.

### After (The Solution)

```
INFO: Using configured user packages: ['your_app']
INFO: Found 11 modules from configured packages  # Success
INFO: your_app.controller
INFO: your_app.hooks
...
```

**Reason**: The packages to be scanned are precisely specified.

## Migration Guide

### Migrating from the Old Way

**Before**: Required explicit imports.

```python
# Needed to manually import all modules
from your_app import controller
from your_app import hooks
from your_app.service import user_service

from cullinan import Application
app = Application()
```

**Now**: Use configuration.

```python
# Just configure once
from cullinan import configure, Application

configure(user_packages=['your_app'])

# No need for manual imports! The framework handles it automatically.
app = Application()
```

## Advanced Usage

### Multi-Package Configuration

```python
configure(
    user_packages=[
        'your_app',        # Main application
        'plugins.auth',    # Authentication plugin
        'plugins.payment'  # Payment plugin
    ]
)
```

### Conditional Configuration

```python
import os
from cullinan import configure

packages = ['myapp']

# Add test package in development environment
if os.getenv('ENV') == 'development':
    packages.append('myapp.tests')

configure(user_packages=packages)
```

### Dynamic Configuration

```python
from cullinan import get_config

config = get_config()
config.add_user_package('myapp.controllers')
config.add_user_package('myapp.services')
config.set_verbose(True)
```

## Troubleshooting

### Problem: Still 404

Check:

```python
from cullinan import get_config

config = get_config()
print(f"Configured packages: {config.user_packages}")

# Should output your configured packages, not an empty list
```

**Solution**: Make sure `configure()` is called before `Application()`.

### Problem: Import Failed

Enable verbose logging:

```python
configure(
    user_packages=['your_app'],
    verbose=True  # See the detailed import process
)
```

Check the error messages in the logs.

### Problem: Some Modules Are Not Scanned

**Check your package structure:**

```
your_project/
└── app/
    ├── __init__.py
    ├── controller.py
    └── service/
        ├── __init__.py
        └── user_service.py
```

**Ensure every directory has an `__init__.py` file.**

## Summary

### Core Points

1.  Specify your packages in `configure(user_packages=[...])`.
2.  Configure **before** creating the `Application` instance.
3.  No need to manually import modules.
4.  Works with all packaging tools.

### Recommended Configuration

```python
from cullinan import configure, Application

configure(
    user_packages=['your_app'],  # Your package
    auto_scan=False               # Strict mode (optional)
)

app = Application()
app.run()
```

**This is the most professional and elegant solution!** 🎉

