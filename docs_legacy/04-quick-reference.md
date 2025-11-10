# Cullinan Configuration Quick Reference

## One-Line Solution for Packaging Problems

```python
from cullinan import configure, Application

configure(user_packages=['your_app'])  # Your package name
app = Application()
app.run()
```

## Configuration Options

```python
configure(
    user_packages=['your_app'],   # Required: Packages to scan
    verbose=True,                   # Optional: Verbose logging
    auto_scan=False,                # Optional: Disable auto-scan
    project_root='/path/to/app',    # Optional: Project root directory
    exclude_packages=['test']       # Optional: Excluded packages
)
```

## Applicable Scenarios

✅ Nuitka Standalone  
✅ Nuitka Onefile  
✅ PyInstaller Onedir  
✅ PyInstaller Onefile  
✅ Development Environment  

## Simplified Packaging Commands

### Before

```bash
nuitka --standalone \
       --include-module=your_app.application \
       --include-module=your_app.controllers \
       --include-module=your_app.services \
       # ... and many more
```

### Now

```bash
nuitka --standalone \
       --include-package=your_app \
       application.py
```

## Verifying Configuration

```python
from cullinan import get_config
from cullinan.controller import handler_list

config = get_config()
print(f"Packages: {config.user_packages}")
print(f"Handlers: {len(handler_list)}")
```

## Complete Example

```python
# your_app/application.py

from cullinan import configure, Application

# Configuration (must be before Application)
configure(user_packages=['your_app'])

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
```

## JSON Configuration (Optional)

```json
{
  "user_packages": ["your_app"],
  "verbose": true,
  "auto_scan": false
}
```

```python
import json
from cullinan import get_config

with open('cullinan.json') as f:
    get_config().from_dict(json.load(f))
```

## Environment Variables (Optional)

```bash
export CULLINAN_USER_PACKAGES=your_app
```

```python
import os
from cullinan import configure

if pkg := os.getenv('CULLINAN_USER_PACKAGES'):
    configure(user_packages=pkg.split(','))
```

## Comparison

### Before Configuration

```
INFO: Found 0 user modules  ← Problem
API 404
```

### After Configuration

```
INFO: Using configured user packages: ['your_app']
INFO: Found 11 modules  ← Solved
API 200 OK
```

## Detailed Documentation

-   Complete Guide: `docs/CONFIGURATION_GUIDE.md`
-   Example Code: `examples/config_example.py`
-   JSON Example: `examples/cullinan.json`

