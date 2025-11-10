# Cullinan v0.71a1 Architecture Documentation

**[English](README.md)** | [中文](zh/README.md)

**Status**: ✅ IMPLEMENTED  
**Version**: 0.71a1  
**Date**: November 10, 2025

---

## 📌 Documentation Status

All planning and analysis documents have been **consolidated** into a single master document:

## **[ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)** 📖

This comprehensive document contains:

1. **Executive Summary** - What was built and key decisions
2. **Service Layer Analysis** - Why we kept and enhanced the service layer
3. **Registry Pattern Evaluation** - Unified registry design
4. **Core Module Design** - Architecture overview and components
5. **Implementation Details** - How everything works
6. **Testing Strategy** - Unit and integration testing
7. **Migration Guide** - Upgrading from v0.6.x to v0.71a1
8. **Future Roadmap** - Plans for future releases and v1.0.0

---

## Implementation Complete ✅

The v0.71a1 architecture has been **fully implemented**:

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
| - v0.71a1 Demo | ✅ | `examples/v070_demo.py` |

---

## Quick Start

### For Users

Want to use v0.71a1? Check these resources:

1. **[Main README](../README.MD)** - Overview and quick start
2. **[v0.71a1 Demo](../examples/v070_demo.py)** - Comprehensive example
3. **[CHANGELOG](../CHANGELOG.md)** - Migration guide from v0.6.x
4. **[Docs Index](README.md)** - Complete documentation

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

## Historical Documents (Archived)

The following planning documents were consolidated into ARCHITECTURE_MASTER.md:

- `01-service-layer-analysis.md` - Service layer value analysis
- `02-registry-pattern-evaluation.md` - Registry pattern evaluation
- `03-architecture-comparison.md` - Framework comparisons
- `04-core-module-design.md` - Core module specifications
- `05-implementation-plan.md` - Implementation roadmap
- `06-migration-guide.md` - Migration instructions
- `07-api-specifications.md` - API reference
- `08-testing-strategy.md` - Testing approach
- `09-code-examples.md` - Code examples
- `10-backward-compatibility.md` - Compatibility analysis

These files remain for historical reference but are no longer actively maintained.

---

## What Changed from Planning?

The implementation closely follows the original plan with these refinements:

| Aspect | Planned | Implemented | Notes |
|--------|---------|-------------|-------|
| Core Module | ✅ | ✅ | As designed |
| Service DI | ✅ | ✅ | As designed |
| Lifecycle Hooks | ✅ | ✅ | As designed |
| Request Context | ✅ | ✅ | Implemented as designed |
| WebSocket | ✅ | ✅ | Enhanced with lifecycle |
| Testing | ✅ | ✅ | Implemented as designed |
| Version | 0.8.0 | 0.71a1 | Changed for clarity |

---

## Migration from v0.6.x

See [CHANGELOG Migration Guide](../CHANGELOG.md#migration-guide) for detailed instructions.

**Quick summary**:

```python
# Old (v0.6.x)
from cullinan.service import service, Service

# New (v0.7.0)
from cullinan import service, Service

# New features available:
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        # Lifecycle hook
        pass
```

---

## Future Roadmap

See [ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md#future-roadmap) for details.

**Short term (v0.7.x)**:
- Additional lifecycle hooks
- Performance optimizations
- More middleware

**Medium term (v0.8.0)**:
- Remove deprecated modules
- Advanced scoping
- Service mesh integration

**Long term (v1.0.0)**:
- Stable API guarantee
- Full async/await
- Cloud-native features

---

## Resources

- **Architecture**: [ARCHITECTURE_MASTER.md](ARCHITECTURE_MASTER.md)
- **Summary**: [SUMMARY.md](SUMMARY.md)
- **Main Docs**: [README.md](README.md)
- **Examples**: [../examples/](../examples/)
- **Source**: [../cullinan/](../cullinan/)

---

**Last Updated**: November 10, 2025  
**Status**: Implementation Complete  
**Maintained By**: Cullinan Development Team
