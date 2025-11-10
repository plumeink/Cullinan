# Troubleshooting Guide for Unregistered Controllers After Packaging

## Problem Description

After packaging and running the application, accessing an API returns a 404 error. Although the logs show that modules were scanned, the Controller is not registered.

## Root Cause

In a Nuitka-compiled environment, there are several possibilities:

1.  **Module Scanned but Not Imported**: The module is found in `sys.modules`, but `reflect_module` did not actually import it.
2.  **Import Failure Ignored**: An error occurred during import, but it was silently handled.
3.  **Decorator Not Executed**: Although the module exists, the decorator code did not run.
4.  **Controller Definition Location**: The Controller is defined in the main file (`__main__`) instead of a separate module.

## Diagnostic Steps

### 1. Run the Diagnostic Tool

```bash
cd dist_nuitka\packaging_test.dist  # Standalone mode
packaging_test.exe  # This will fail, but that's okay

# Then run the diagnosis
python ..\..\..\examples\diagnose.py
```

The diagnostic tool will display:
-   Environment detection results
-   A list of modules in `sys.modules`
-   The number of registered handlers
-   Scanned user modules

### 2. Enable Verbose Logging

Modify `packaging_test.py` to enable `DEBUG` logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check for these key log entries:
-   `✓ Successfully imported: xxx` - Module imported successfully.
-   `✗ Import failed for xxx` - Module import failed.
-   `✓ Found in sys.modules: xxx` - Module found in `sys.modules`.

### 3. Check the Handler List

Add this to your application code:

```python
from cullinan.controller import handler_list

print(f"Registered handlers: {len(handler_list)}")
for handler in handler_list:
    print(f"  - {handler}")
```

## Solutions

### Solution 1: Place the Controller in a Separate Module (Recommended)

**Do not** define the Controller in the main file:

```python
# ❌ Incorrect: Defined in main.py
@Controller('/api')
class TestController:
    pass

def main():
    app = Application()
    app.run()
```

**Instead**, create a separate controller module:

```python
# examples/test_controller.py
from cullinan.controller import Controller, request_mapping

@Controller('/api')
class TestController:
    @request_mapping('/hello', method=['GET'])
    def hello(self, request):
        return {'message': 'Hello'}
```

Then, **explicitly import** it in the main file:

```python
# examples/packaging_test.py
from cullinan import Application

# Explicitly import the controller (important!)
try:
    from examples import test_controller
except ImportError:
    import test_controller

def main():
    app = Application()
    app.run()
```

### Solution 2: Update the Packaging Command

Ensure you use the `--include-module` parameter:

```bash
nuitka --standalone \
       --include-package=cullinan \
       --include-package=examples \
       --include-module=examples.test_controller \
       examples/packaging_test.py
```

### Solution 3: Use a Package Structure

Create a complete package structure:

```
your_app/
├── __init__.py
├── main.py
├── controllers/
│   ├── __init__.py          # Important: Import all controllers
│   └── test_controller.py
└── services/
    ├── __init__.py          # Important: Import all services
    └── test_service.py
```

In `controllers/__init__.py`:

```python
# Import all controller modules
from . import test_controller
```

In `main.py`:

```python
from cullinan import Application

# Explicitly import
from your_app import controllers
from your_app import services

def main():
    app = Application()
    app.run()
```

### Solution 4: Force Import

If none of the above methods work, you can force the import before the application starts:

```python
# main.py
import sys
import importlib

# Force import controller modules
controller_modules = [
    'examples.test_controller',
    # Add other controller modules
]

for mod_name in controller_modules:
    try:
        importlib.import_module(mod_name)
        print(f"✓ Imported: {mod_name}")
    except Exception as e:
        print(f"✗ Failed to import {mod_name}: {e}")

from cullinan import Application
app = Application()
app.run()
```

## Verifying the Fix

### 1. Check the Logs

After starting the application, you should see:

```
INFO:cullinan.application: ||| Starting module discovery...
INFO:cullinan.application: ||| === Using Nuitka scanning strategy ===
INFO:cullinan.application: ||| Found X user modules in sys.modules
INFO:cullinan.application: ✓ Found in sys.modules: examples.test_controller
```

### 2. Check the Handlers

You should see:

```
Registered handlers: 3
  - ('/api/hello', <handler>, ['GET'])
  - ('/api/info', <handler>, ['GET'])
  - ('/api/test', <handler>, ['GET'])
```

### 3. Test the API

```bash
curl http://localhost:8888/api/hello
# Should return: {"message": "Hello from Cullinan!", "status": "ok"}
```

## Improvements to the Current Implementation

I have made the following improvements to the code:

1.  **Prioritize `sys.modules` Check**: In a Nuitka environment, modules are usually already in `sys.modules`.
2.  **Detailed Logging**: Use `INFO`/`WARNING` levels to log import status.
3.  **`__main__` Handling**: Special handling for the `__main__` module.
4.  **Better Filtering**: Exclude standard libraries and third-party libraries to scan only user code.

## Debugging Checklist

-   [ ] Is the Controller in a separate module?
-   [ ] Does the main file explicitly import the controller module?
-   [ ] Does `__init__.py` exist and import sub-modules?
-   [ ] Does the packaging command include the `--include-module` parameter?
-   [ ] Do the logs show that the module was successfully imported?
-   [ ] Does `handler_list` contain the registered routes?
-   [ ] Is `DEBUG` logging enabled for detailed information?

## Recommended Project Structure

```
your_project/
├── setup.py or pyproject.toml
├── your_app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── controllers/
│   │   ├── __init__.py      # from . import user_controller
│   │   └── user_controller.py
│   └── services/
│       ├── __init__.py      # from . import user_service
│       └── user_service.py
└── build_scripts/
    ├── build_nuitka.bat
    └── build_pyinstaller.bat
```

## Contact Support

If the problem persists, please provide:

1.  The full output of the diagnostic tool.
2.  The complete logs from application startup (with `DEBUG` level).
3.  A screenshot of your project structure.
4.  The packaging command.
5.  The content of `handler_list`.

This will help us resolve your issue more quickly.

