# Cullinan v0.7x Documentation

**[English](README.md)** | [中文](zh/README.md)

**Version**: 0.7x

---

## 📚 Complete Architecture Guide

For comprehensive architectural information, design decisions, and implementation details, see:

## **[ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)** 📖

This guide covers:

1. **Executive Summary** - Overview and key design decisions
2. **Service Layer** - Enhanced service layer with dependency injection
3. **Registry Pattern** - Unified component registration
4. **Core Module** - Architecture and components
5. **Implementation Details** - How everything works together
6. **Testing Strategy** - Testing approach and utilities
7. **Migration Guide** - Upgrading from v0.6x

---

## 🚀 Features Overview

The v0.7x architecture includes:

| Component | Status | Location |
|-----------|--------|----------|
| **Core Module** | ✅ Complete | `cullinan/core/` |
| - Registry Pattern | ✅ | `core/registry.py` |
| - Dependency Injection | ✅ | `core/injection.py` |
| - Lifecycle Management | ✅ | `core/lifecycle.py` |
| - Request Context | ✅ | `core/context.py` |
| **Service Layer** | ✅ Complete | `cullinan/service/` |
| - Enhanced Services | ✅ | `service/base.py` |
| - ServiceRegistry | ✅ | `service/registry.py` |
| - @service Decorator | ✅ | `service/decorators.py` |
| **WebSocket** | ✅ Complete | `cullinan/websocket_registry.py` |
| - WebSocketRegistry | ✅ | `websocket_registry.py` |
| - @websocket_handler | ✅ | `websocket_registry.py` |
| **Testing** | ✅ Complete | `cullinan/testing/` |
| - TestRegistry | ✅ | `testing/registry.py` |
| - Mock Services | ✅ | `testing/mocks.py` |
| **Documentation** | ✅ Complete | Multiple locations |
| - Main README | ✅ | `README.MD` |
| - CHANGELOG | ✅ | `CHANGELOG.md` |
| - Docs Index | ✅ | `docs/README.md` |
| **Examples** | ✅ Complete | `examples/` |
| - v0.7x Demo | ✅ | `examples/v070_demo.py` |

---

## Quick Start

### For Users

Want to use v0.7x? Check these resources:

1. **[Main README](../README.MD)** - Overview and quick start
2. **[v0.7x Demo](../examples/v070_demo.py)** - Comprehensive example
3. **[Migration Guide](MIGRATION_GUIDE.md)** - Upgrading from v0.6x
4. **[API Migration Guide](API_MIGRATION_GUIDE.md)** - Complete API migration guide ⚠️ **New**
5. **[Legacy Cleanup Reference](LEGACY_CLEANUP_REFERENCE.md)** - Quick reference for cleanup
6. **[CHANGELOG](../docs_archive/reports/CHANGELOG.md)** - Version history and changes

### For Developers

Want to understand the architecture?

1. **[ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)** - Complete design doc
2. **Source Code**:
   - `cullinan/core/` - Core components
   - `cullinan/service/` - Service layer
   - `cullinan/websocket_registry.py` - WebSocket integration
3. **[Testing Guide](ARCHITECTURE_MASTER.md#testing-strategy)** - How to test

---

## Key Features

### Service Layer with Dependency Injection

```python
from cullinan import service, Service

@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name, email):
        user = {'name': name, 'email': email}
        self.email.send_welcome(email)
        return user
```

### WebSocket with Registry Integration

```python
from cullinan import websocket_handler

@websocket_handler(url='/ws/chat')
class ChatHandler:
    def on_init(self):
        self.connections = set()
    
    def on_open(self):
        self.connections.add(self)
    
    def on_message(self, message):
        for conn in self.connections:
            conn.write_message(message)
```

### Request Context Management

```python
from cullinan import create_context, get_current_context

with create_context():
    ctx = get_current_context()
    ctx.set('user_id', 123)
    ctx.set('request_id', 'abc-123')
    # Context automatically cleaned up
```

---

## Migration from v0.6x

See [Migration Guide](MIGRATION_GUIDE.md) for detailed instructions.

**Quick summary**:

```python
# Old (v0.6x)
from cullinan.service import service, Service

# New (v0.7x)
from cullinan import service, Service

# New features available:
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        # Lifecycle hook
        pass
```

---

## Resources

- **Architecture Guide**: [ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)
- **Migration Guide**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **Documentation Index**: [README.md](README.md)
- **Examples**: [../examples/](../examples/)
- **Source Code**: [../cullinan/](../cullinan/)
- **Changelog**: [../CHANGELOG.md](../docs_archive/reports/CHANGELOG.md)

---

**Last Updated**: November 11, 2025  
**Status**: Implementation Complete  
**Maintained By**: Cullinan Development Team
