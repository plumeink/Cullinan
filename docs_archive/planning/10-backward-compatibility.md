# Backward Compatibility Strategy

## Executive Summary

This document outlines Cullinan's commitment to backward compatibility and provides detailed strategies for maintaining it during the core module and service layer enhancements.

## 1. Compatibility Commitment

### 1.1 Guarantee

**Cullinan guarantees**:
✅ All code using v0.7.x APIs will work in v0.8.x without modification
✅ No breaking changes in public APIs
✅ Deprecated features will be supported for at least 2 major versions
✅ Clear migration path for any future breaking changes

### 1.2 Semantic Versioning

Cullinan follows [Semantic Versioning](https://semver.org/):

**MAJOR.MINOR.PATCH** (e.g., 1.2.3)

- **MAJOR**: Breaking changes (rare, planned well in advance)
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

**Examples**:
- `0.7.x` → `0.8.0`: New features, no breaking changes ✅
- `0.8.x` → `1.0.0`: May include breaking changes (well documented) ⚠️
- `1.0.x` → `1.1.0`: New features, backward compatible ✅

## 2. Current API Support

### 2.1 Service Decorator (Legacy)

**Current Usage**:
```python
@service
class UserService(Service):
    pass
```

**Support Status**: ✅ **FULLY SUPPORTED** in v0.8+

**Implementation**:
```python
def service(cls_or_dependencies=None):
    """Backward compatible decorator."""
    # Handle legacy usage: @service
    if callable(cls_or_dependencies):
        cls = cls_or_dependencies
        _global_service_registry.register(cls.__name__, cls)
        service_list[cls.__name__] = cls()  # Maintain global dict
        return cls
    
    # Handle new usage: @service(dependencies=[...])
    def decorator(cls):
        dependencies = cls_or_dependencies.get('dependencies', [])
        _global_service_registry.register(cls.__name__, cls, dependencies=dependencies)
        service_list[cls.__name__] = None  # Will be populated on first access
        return cls
    
    return decorator
```

### 2.2 Global service_list Dictionary

**Current Usage**:
```python
from cullinan.service import service_list

# Access service
user_service = service_list['UserService']
```

**Support Status**: ✅ **FULLY SUPPORTED** in v0.8+

**Implementation**:
```python
# cullinan/service/__init__.py
service_list = {}  # Maintained for backward compatibility

# When service registered, also add to service_list
@service
class UserService(Service):
    pass

# Result: service_list['UserService'] exists
```

### 2.3 Controller Service Access

**Current Usage**:
```python
@controller(url='/api')
class UserController:
    @post_api(url='/users')
    def create_user(self, body_params):
        user = self.service['UserService'].create_user(...)
        return self.response_build(status=201, data=user)
```

**Support Status**: ✅ **FULLY SUPPORTED** in v0.8+

**No changes required**. Controllers access services the same way.

## 3. New Features (Opt-In)

### 3.1 Dependency Injection

**New Feature**:
```python
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
```

**Compatibility**: ✅ **ADDITIVE** - Old code unaffected

**Migration**: Optional, at your own pace

### 3.2 Lifecycle Hooks

**New Feature**:
```python
@service
class DatabaseService(Service):
    def on_init(self):
        self.pool = create_pool()
    
    def on_destroy(self):
        self.pool.close()
```

**Compatibility**: ✅ **ADDITIVE** - Services without hooks work normally

**Migration**: Optional, add hooks when needed

### 3.3 Testing Utilities

**New Feature**:
```python
from cullinan.testing import TestRegistry, MockService

registry = TestRegistry()
registry.register_mock('EmailService', MockEmailService())
```

**Compatibility**: ✅ **NEW MODULE** - Doesn't affect existing code

**Migration**: Optional, use when writing new tests

## 4. Deprecation Policy

### 4.1 Deprecation Process

When a feature needs to be deprecated:

**Step 1: Announce** (Version N)
- Add deprecation warning to documentation
- Feature still works normally

**Step 2: Warn** (Version N+1)
- Add runtime deprecation warning
```python
import warnings
warnings.warn(
    "feature_name is deprecated and will be removed in version X.X",
    DeprecationWarning
)
```

**Step 3: Remove** (Version N+2 or next major)
- Feature removed
- Migration guide provided

**Example Timeline**:
```
v0.8: Announce deprecation of old_feature
v0.9: old_feature warns when used
v1.0: old_feature removed (with migration guide)
```

### 4.2 Current Deprecations

**None**. No features are deprecated in v0.8.

## 5. Testing Backward Compatibility

### 5.1 Compatibility Test Suite

**Purpose**: Ensure old code works in new version.

```python
# tests/compatibility/test_legacy_service.py
class TestLegacyServiceUsage(unittest.TestCase):
    """Test that v0.7.x service code works in v0.8+."""
    
    def test_simple_service_decorator(self):
        """Test: @service decorator works as before."""
        @service
        class LegacyService(Service):
            def do_something(self):
                return "works"
        
        # Access via global dict (old way)
        from cullinan.service import service_list
        svc = service_list['LegacyService']
        result = svc.do_something()
        
        self.assertEqual(result, "works")
    
    def test_service_in_controller(self):
        """Test: Controllers can access services as before."""
        @controller(url='/test')
        class LegacyController:
            @get_api(url='/test')
            def test_endpoint(self, query_params):
                # Old way of accessing services
                result = self.service['LegacyService'].do_something()
                return self.response_build(status=200, data=result)
        
        # Test the controller works
        # ... (controller testing code)
```

### 5.2 Automated Compatibility Checks

**CI Pipeline Step**:
```yaml
# .github/workflows/compatibility.yml
- name: Test Backward Compatibility
  run: |
    # Run compatibility test suite
    python -m pytest tests/compatibility/ -v
    
    # Ensure no deprecation warnings in compatibility tests
    python -m pytest tests/compatibility/ -W error::DeprecationWarning
```

## 6. Migration Support

### 6.1 Migration Tools

**Version Checker**:
```python
# cullinan/migration/version_checker.py
def check_compatibility(current_version, target_version):
    """Check if migration is needed."""
    # Returns list of breaking changes and migration steps
    pass
```

**Migration Script**:
```python
# cullinan/migration/migrate.py
def migrate_service_decorators(file_path):
    """Automatically update service decorators to new syntax."""
    # Optional tool for users who want to adopt new features
    pass
```

### 6.2 Documentation

**Migration Guide**: `06-migration-guide.md` provides:
- Step-by-step migration instructions
- Code examples (before/after)
- Common pitfalls
- Rollback procedures

## 7. Version-Specific Notes

### 7.1 v0.7.x → v0.8.0

**Breaking Changes**: ❌ NONE

**New Features**:
- ✅ Core module (Registry, DependencyInjector, LifecycleManager)
- ✅ Dependency injection in services (opt-in)
- ✅ Lifecycle hooks (opt-in)
- ✅ Testing utilities

**Migration Required**: NO

**Recommended Actions**:
1. Update to v0.8.0
2. Run existing tests (should all pass)
3. Gradually adopt new features
4. Read migration guide for best practices

### 7.2 v0.8.x → v0.9.0 (Planned)

**Breaking Changes**: ❌ NONE (planned)

**New Features** (tentative):
- Request-scoped services
- Advanced scope management
- Service health checks
- Enhanced monitoring

**Migration Required**: NO

### 7.3 v0.9.x → v1.0.0 (Future)

**Breaking Changes**: ⚠️ POSSIBLE (to be determined)

**Approach**:
- Will be announced well in advance
- Deprecation warnings in v0.9.x
- Comprehensive migration guide
- Migration tools provided

## 8. API Stability Levels

### 8.1 Stable APIs

**Guaranteed to remain backward compatible**:
- `@service` decorator
- `@controller` decorator
- `@get_api`, `@post_api`, etc.
- `self.service[...]` in controllers
- `Service` base class
- `service_list` global dictionary

### 8.2 Experimental APIs

**May change in minor versions** (clearly marked in docs):
- None currently

### 8.3 Internal APIs

**No backward compatibility guarantee** (use at own risk):
- APIs starting with `_` (e.g., `_resolve_dependencies`)
- Modules in `cullinan.internal`
- Test-only APIs (unless in `cullinan.testing`)

## 9. Community Feedback

### 9.1 Breaking Change Proposals

**Process for proposing breaking changes**:
1. Create GitHub discussion
2. Gather community feedback
3. Document use cases and migration path
4. Wait at least 1 month before implementing
5. Include in next major version

### 9.2 Compatibility Issues

**If you find a compatibility issue**:
1. Check if it's documented as breaking
2. Report on GitHub Issues
3. Include:
   - Version numbers (old and new)
   - Code that broke
   - Error message
   - Expected behavior

**We commit to**:
- Respond within 48 hours
- Fix or provide workaround
- Update documentation

## 10. Long-Term Support

### 10.1 LTS Versions

**Long-Term Support policy**:
- Major versions receive security fixes for 2 years
- Critical bug fixes for 1 year after next major release
- Example: v1.0.0 released → v1.x supported until v2.0.0 + 1 year

### 10.2 End-of-Life

**When a version reaches EOL**:
- Announced 6 months in advance
- Migration guide to latest version provided
- Community support continues (no official support)

## 11. Guarantees Summary

### 11.1 What We Guarantee

✅ **No breaking changes in minor/patch versions**
✅ **Clear migration path for major versions**
✅ **At least 2 versions of deprecation notice**
✅ **Comprehensive testing for backward compatibility**
✅ **Quick response to compatibility issues**

### 11.2 What We Don't Guarantee

❌ Internal API stability
❌ Experimental feature stability
❌ Support for Python versions past EOL
❌ Third-party package version compatibility

## 12. Checklist for Contributors

**Before making a change**:
- [ ] Does it break existing APIs?
- [ ] Can it be made backward compatible?
- [ ] Is deprecation needed?
- [ ] Are compatibility tests added?
- [ ] Is documentation updated?
- [ ] Is migration guide updated?

---

**Document Version**: 1.0  
**Author**: Cullinan Framework Team  
**Date**: 2025-11-10  
**Status**: Final Draft
