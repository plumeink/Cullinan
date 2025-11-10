# Legacy Code Cleanup - Quick Reference

## What Changed?

### 🗑️ Removed: `cullinan/hooks.py`

The old `hooks.py` file has been **removed**. It contained only the `MissingHeaderHandlerHook` class which was legacy v0.6x code.

### ✅ No Confusion with `cullinan/monitoring/hooks.py`

These were **two completely different files** with different purposes:

| File | Purpose | Status |
|------|---------|--------|
| ❌ `cullinan/hooks.py` | Simple missing header hook (v0.6x legacy) | **REMOVED** |
| ✅ `cullinan/monitoring/hooks.py` | Monitoring system with `MonitoringHook` & `MonitoringManager` (v0.7x) | **ACTIVE** |

## Migration Path

### If you used `MissingHeaderHandlerHook`:

**Before:**
```python
from cullinan.hooks import MissingHeaderHandlerHook

def my_handler(request, header_name):
    print(f"Missing header: {header_name}")

MissingHeaderHandlerHook.set_hook(my_handler)
```

**After:**
```python
from cullinan import set_missing_header_handler

def my_handler(request, header_name):
    print(f"Missing header: {header_name}")

set_missing_header_handler(my_handler)
```

### New API Functions

```python
from cullinan import (
    set_missing_header_handler,  # Set custom handler
    get_missing_header_handler,  # Get current handler
)

# Set custom handler
def custom_handler(request, header_name):
    # Your custom logic here
    pass

set_missing_header_handler(custom_handler)

# Get current handler (useful for testing)
handler = get_missing_header_handler()
```

## Deprecation Warnings

**UPDATE: These modules have been completely removed in the latest version.**

Two modules that previously showed deprecation warnings have now been **completely removed**:

### 1. `cullinan/registry.py` - ❌ REMOVED

**No longer available:**
```python
from cullinan.registry import HandlerRegistry  # ❌ ImportError
```

**Use new imports:**
```python
from cullinan.handler import HandlerRegistry  # ✅ Correct
# OR
from cullinan import HandlerRegistry  # ✅ Recommended
```

### 2. `cullinan/websocket.py` - ❌ REMOVED

**No longer available:**
```python
from cullinan.websocket import websocket  # ❌ ImportError

@websocket(url='/ws/chat')
class ChatHandler:
    pass
```

**Use new imports:**
```python
from cullinan import websocket_handler  # ✅ Recommended

@websocket_handler(url='/ws/chat')
class ChatHandler:
    pass
```

## Why These Changes?

1. **Cleaner Architecture**: Functionality moved to appropriate modules
2. **Less Confusion**: Clear separation between old and new monitoring systems
3. **Better Organization**: Related code grouped together
4. **Simplified Maintenance**: Removed redundant forwarding layers

## Timeline

- **v0.7x (Early)**: Legacy code removed, deprecated modules showed warnings
- **v0.7x (Current)**: Deprecated modules completely removed
- **v0.8x (Future)**: Continue architecture improvements

## Need Help?

- See full details: [Complete Technical Report](../彻底删除弃用文件完成报告.md) (Chinese)
- Migration guide: [API Migration Guide](API_MIGRATION_GUIDE.md)
- Architecture overview: [ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)
- Chinese version: [中文版本](zh/LEGACY_CLEANUP_REFERENCE.md)

