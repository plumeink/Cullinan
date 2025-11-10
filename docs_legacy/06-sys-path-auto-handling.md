# Improved Startup and Automatic `sys.path` Handling

## Problem Background

Previously, when using Cullinan with code inside a package (e.g., `club/fnep/application.py`), you had to manually add:

```python
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')
```

The reason for this is that Python needs to know the package's root directory to correctly import modules and read environment variable files.

## Solution

Now, the `configure()` function **automatically detects and adds the project root directory to `sys.path`**, eliminating the need for manual additions!

---

## New Recommended Startup Method

### Simplified Startup Code

```python
# -*- coding: utf-8 -*-
# club/fnep/application.py

from cullinan import application, configure
from cullinan.hooks import MissingHeaderHandlerHook
from club.fnep.hooks import missing_header_handler

def main():
    # configure() automatically handles sys.path
    configure(user_packages=['club.fnep'])
    
    # Set hooks
    MissingHeaderHandlerHook.set_hook(missing_header_handler)
    
    # Start the application
    application.run()

if __name__ == '__main__':
    main()
```

The line `sys.path.append(...)` is **no longer needed**!

---

## How It Works

### Automatic Detection Logic

The `configure()` function automatically detects the project root directory based on the configured package name:

1.  **Get Caller's File Path**: Uses Python's `inspect` module to get the location of the file calling `configure()`.

2.  **Find Package Root by Traversing Upwards**:
    -   For example, if `user_packages=['club.fnep']` is configured.
    -   It searches upwards from the current file's location to find the parent directory containing the `club/` directory.
    -   It will search up to a maximum of 5 levels.

3.  **Automatically Add to `sys.path`**:
    -   Once the project root is found, it is automatically added to the beginning of `sys.path`.
    -   This ensures that subsequent import operations can find modules correctly.

### Example

Assume the project structure is:
```
/home/user/projects/my_discord_bot/
├── club/
│   └── fnep/
│       ├── application.py      # ← This is the startup file
│       ├── controllers/
│       ├── services/
│       └── hooks.py
├── .env
└── requirements.txt
```

When you call this in `club/fnep/application.py`:
```python
configure(user_packages=['club.fnep'])
```

Cullinan will:
1.  Detect that the current file is in `/home/user/projects/my_discord_bot/club/fnep/`.
2.  Know from the package name `club.fnep` that it needs to find the parent directory containing `club/`.
3.  Search upwards and find `/home/user/projects/my_discord_bot/`.
4.  Automatically add it to `sys.path`.

---

## Manually Specifying the Project Root (Optional)

If automatic detection is not accurate, you can specify it manually:

```python
configure(
    user_packages=['club.fnep'],
    project_root='/path/to/project/root'
)
```

---

## Detailed Output (for Debugging)

Enabling verbose mode will show changes to `sys.path`:

```python
configure(
    user_packages=['club.fnep'],
    verbose=True
)

# Output:
# Auto-added project root to sys.path: /home/user/projects/my_discord_bot
```

---

## Comparison: Old vs. New

### Old Way (Cumbersome)

```python
import sys
import os

# Need to manually calculate the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')

from cullinan import application, configure
from club.fnep.hooks import missing_header_handler

def main():
    configure(user_packages=['club.fnep'])
    application.run()
```

### New Way (Concise)

```python
from cullinan import application, configure
from club.fnep.hooks import missing_header_handler

def main():
    # configure() automatically handles sys.path
    configure(user_packages=['club.fnep'])
    application.run()
```

---

## Advantages

✅ **More Concise**: No need to manually manipulate `sys.path`.  
✅ **Safer**: Automatic calculation avoids path errors.  
✅ **Smarter**: Automatically adapts to different project structures.  
✅ **Backward Compatible**: Still supports manual specification of `project_root`.

---

## Important Notes

1.  **Package Name Must Be Accurate**: The package names in `user_packages` must match the actual file structure.

2.  **Maximum 5 Levels of Search**: If the project structure is nested more than 5 levels deep, it is recommended to manually specify `project_root`.

3.  **Development Mode Installation**: If the project is installed with `pip install -e .`, you usually don't need to worry about `sys.path` issues.

---

## Example: Complete Startup File

```python
# -*- coding: utf-8 -*-
"""
Discord Bot Application Entry Point
"""

from cullinan import application, configure
from cullinan.hooks import MissingHeaderHandlerHook
from club.fnep.hooks import missing_header_handler

def main():
    """Application startup entry point"""
    # Configure Cullinan (automatically handles sys.path)
    configure(
        user_packages=['club.fnep'],
        verbose=False,  # Set to False in production
        auto_scan=False  # Scan only specified packages
    )
    
    # Register global hooks
    MissingHeaderHandlerHook.set_hook(missing_header_handler)
    
    # Start the application
    print("Starting Discord Bot API...")
    application.run(port=8080)

if __name__ == '__main__':
    main()
```

---

## Testing

The new feature has been verified with unit tests:

```bash
$ python run_tests.py

Ran 29 tests in 0.081s
OK

✓ All tests passed! (29/29)
```

---

## Update Time

2025-11-06

## Related Files

-   `cullinan/config.py` - Implements automatic `sys.path` handling.
-   `tests/test_core.py` - Contains relevant test cases.

