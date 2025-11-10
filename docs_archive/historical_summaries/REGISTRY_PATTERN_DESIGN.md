# Registry Pattern Implementation Plan

## Status: Design Document (待实现状态 - TO BE IMPLEMENTED)

## Overview
This document outlines the design and implementation plan for migrating from global lists (`handler_list`, `header_list`) to a Registry Pattern architecture, improving testability, maintainability, and enabling dependency injection.

## Problem Statement

### Current Architecture Issues
1. **Global State**: `handler_list` and `header_list` are global mutable lists in `controller.py`
   ```python
   handler_list = []  # Global state makes testing difficult
   header_list = []   # Cannot easily isolate test cases
   ```

2. **Testing Challenges**:
   - Tests cannot easily create isolated handler registries
   - No clean way to reset state between tests
   - Difficult to mock or stub handler registration

3. **Lack of Encapsulation**:
   - Direct manipulation of global lists throughout codebase
   - No validation or metadata tracking
   - No lifecycle management

4. **Limited Extensibility**:
   - Hard to add features like middleware, hooks, or policies per route
   - Cannot easily implement route grouping or namespaces

## Proposed Solution: Registry Pattern

### Architecture Design

#### 1. Core Registry Classes

```python
class HandlerRegistry:
    """Central registry for HTTP request handlers with metadata support."""
    
    def __init__(self):
        self._handlers: Dict[str, HandlerMetadata] = {}
        self._sorted: bool = False
        self._sorted_handlers: List[Tuple[str, Any]] = []
    
    def register(
        self,
        url: str,
        servlet: Any,
        methods: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a handler with optional metadata."""
        pass
    
    def get_handlers(self) -> List[Tuple[str, Any]]:
        """Get all registered handlers (sorted)."""
        pass
    
    def find_handler(self, url: str) -> Optional[HandlerMetadata]:
        """Find handler by URL pattern."""
        pass
    
    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        pass


class HeaderRegistry:
    """Registry for global HTTP headers."""
    
    def __init__(self):
        self._headers: List[Tuple[str, str]] = []
    
    def register(self, name: str, value: str) -> None:
        """Register a global header."""
        pass
    
    def get_headers(self) -> List[Tuple[str, str]]:
        """Get all registered headers."""
        pass
    
    def clear(self) -> None:
        """Clear all headers (for testing)."""
        pass
```

#### 2. Handler Metadata

```python
@dataclass
class HandlerMetadata:
    """Metadata for a registered handler."""
    url: str
    servlet: Any
    methods: List[str]
    middleware: List[Callable] = field(default_factory=list)
    auth_required: bool = False
    rate_limit: Optional[RateLimit] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
```

### Migration Strategy

#### Phase 1: Preparation (Current Phase)
- [x] Create `registry.py` with basic implementation (Already exists)
- [x] Add comprehensive documentation
- [ ] Design metadata schema
- [ ] Create migration guide

#### Phase 2: Parallel Implementation
- [ ] Maintain both global lists and registries
- [ ] Add feature flag to switch between implementations
- [ ] Update decorators to use both systems
- [ ] Comprehensive testing of registry implementation

#### Phase 3: Gradual Migration
- [ ] Migrate application.py to use registries
- [ ] Migrate controller.py decorator logic
- [ ] Update all internal references
- [ ] Deprecation warnings for direct list access

#### Phase 4: Cleanup
- [ ] Remove global lists
- [ ] Remove compatibility shims
- [ ] Update all documentation
- [ ] Release as breaking change with migration guide

## Interface Specification

### Public API

```python
# Configuration
from cullinan.registry import get_handler_registry, get_header_registry

# Get registry instances (singleton pattern)
handler_registry = get_handler_registry()
header_registry = get_header_registry()

# Registration (used by decorators internally)
handler_registry.register(
    url='/api/users',
    servlet=UserServlet,
    methods=['GET', 'POST'],
    metadata={
        'auth_required': True,
        'rate_limit': {'requests': 100, 'window': 60},
        'description': 'User management endpoints'
    }
)

# Testing support
handler_registry.clear()  # Reset for test isolation
```

### Decorator Integration

```python
@get_api(url='/api/users', auth=True, rate_limit=100)
def get_users(self):
    """Decorator automatically registers with metadata."""
    pass
```

## Benefits

### 1. Improved Testability
```python
def test_handler_registration():
    # Create isolated registry for testing
    registry = HandlerRegistry()
    registry.register('/test', TestServlet)
    
    assert registry.count() == 1
    registry.clear()
    assert registry.count() == 0
```

### 2. Type Safety
- Full type hints on all registry methods
- Better IDE support and autocomplete
- Static type checking with mypy

### 3. Extensibility
- Easy to add middleware per route
- Support for route metadata (auth, rate limits, etc.)
- Plugin architecture for custom behaviors

### 4. Better Error Messages
```python
try:
    registry.register(url, handler)
except DuplicateHandlerError as e:
    print(f"Handler already registered: {e.url}")
    print(f"Existing handler: {e.existing_handler}")
    print(f"New handler: {e.new_handler}")
```

## Implementation Challenges

### 1. Backward Compatibility
**Challenge**: Existing code directly accesses `handler_list`

**Solution**: 
- Provide compatibility shim that proxies to registry
- Deprecation warnings for direct access
- Clear migration timeline

### 2. Performance
**Challenge**: Registry adds abstraction overhead

**Mitigation**:
- Keep sorted list cache like current implementation
- Lazy sorting on demand
- Benchmark to ensure no regression

### 3. Module Import Order
**Challenge**: Handlers registered at module import time

**Solution**:
- Registry must be available before any decorators execute
- Use lazy initialization pattern
- Document import order requirements

## Testing Plan

### Unit Tests
- [ ] Registry operations (add, remove, find)
- [ ] Sorting algorithm correctness
- [ ] Metadata handling
- [ ] Error cases (duplicates, invalid URLs)

### Integration Tests
- [ ] Full application with registry-based routing
- [ ] Decorator integration
- [ ] Handler resolution and execution
- [ ] Performance benchmarks

### Migration Tests
- [ ] Parallel operation of both systems
- [ ] Feature parity verification
- [ ] Performance comparison

## Timeline

### Short Term (Current Sprint)
- ✅ Create design document (this file)
- ✅ Review existing registry.py implementation
- [ ] Design metadata schema
- [ ] Create comprehensive test suite

### Medium Term (Next 2-3 Sprints)
- [ ] Implement parallel operation mode
- [ ] Migrate internal code to use registry
- [ ] Performance testing and optimization
- [ ] Documentation updates

### Long Term (Future Release)
- [ ] Remove global lists
- [ ] Release as major version with migration guide
- [ ] Community feedback and refinements

## Open Questions

1. **Metadata Schema**: What metadata should be supported out of the box?
   - Auth requirements?
   - Rate limiting?
   - CORS policies?
   - Custom tags/labels?

2. **Plugin Architecture**: Should we support third-party registry plugins?

3. **Route Grouping**: Should we support hierarchical route organization?

4. **Dynamic Registration**: Should handlers be registrable/unregistrable at runtime?

5. **Serialization**: Should registry state be serializable for inspection tools?

## References

### Related Files
- `cullinan/registry.py` - Current registry implementation
- `cullinan/controller.py` - Handler and header list usage
- `cullinan/application.py` - Handler sorting logic

### Design Patterns
- Registry Pattern (Gang of Four)
- Dependency Injection
- Service Locator Pattern

### Similar Implementations
- Flask's Blueprint system
- Django's URL dispatcher
- FastAPI's APIRouter

## Contributing

This is a design document. Feedback and suggestions are welcome:
1. Review the proposed architecture
2. Identify potential issues or improvements
3. Suggest alternative approaches
4. Help with implementation

## Version History

- 2025-11-09: Initial design document created
- Status: PENDING IMPLEMENTATION

---

**Note**: This is a DESIGN DOCUMENT for future implementation. The registry pattern is not yet integrated into the main framework. Current code still uses global lists (`handler_list`, `header_list`).
