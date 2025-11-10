# Changelog

All notable changes to the Cullinan project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.71a1] - 2025-11-10

### 🚀 Major Architectural Refactoring

This is a major release with breaking changes and a completely redesigned architecture. Version 0.71a1 is not backward compatible with 0.6.x.

### Added

#### Core Module (`cullinan.core`)

- **Registry Pattern**: Base `Registry` class for unified component registration
  - Abstract `Registry[T]` class with type safety
  - `SimpleRegistry` concrete implementation
  - Methods: `register()`, `get()`, `has()`, `list_all()`, `get_metadata()`, `clear()`
  
- **Dependency Injection**: `DependencyInjector` for managing component dependencies
  - Provider-based dependency resolution
  - Singleton instance management (11x cache speedup)
  - Circular dependency detection
  - Optional dependency support
  
- **Lifecycle Management**: `LifecycleManager` for component lifecycle
  - `LifecycleState` enum (CREATED, INITIALIZING, INITIALIZED, DESTROYING, DESTROYED)
  - `LifecycleAware` interface for components
  - Hooks: `on_init()`, `on_destroy()` (both sync and async supported)
  - Automatic initialization and cleanup
  - **NEW**: Full async support with `initialize_all_async()` and `destroy_all_async()`
  
- **Request Context**: Thread-safe request context management
  - `RequestContext` class for request-scoped data
  - Context variables using `contextvars` for thread safety
  - `ContextManager` for automatic context lifecycle
  - Convenience functions: `get_current_context()`, `set_current_context()`
  - Methods: `set()`, `get()`, `has()`, `delete()`, `clear()`
  - Metadata support and cleanup callbacks

#### Enhanced Service Layer (`cullinan.service`)

- **Service Base Class**: Enhanced `Service` with lifecycle hooks
  - `on_init()`: Called when service is initialized (can be sync or async)
  - `on_destroy()`: Called on application shutdown (can be sync or async)
  - Access to dependencies via `self.dependencies`
  
- **ServiceRegistry**: Service-specific registry extending `core.Registry`
  - Dependency injection support
  - Singleton service instances
  - Automatic dependency resolution
  - Metadata storage
  - **NEW**: `initialize_all_async()` and `destroy_all_async()` for async services
  
- **@service Decorator**: Easy service registration
  - `@service` - Simple service without dependencies
  - `@service(dependencies=['ServiceName'])` - Service with dependencies
  - Automatic lifecycle management

#### WebSocket Integration

- **WebSocketRegistry**: Unified registry for WebSocket handlers
  - URL-based handler registration
  - Lifecycle hooks support
  - Metadata storage for dependencies
  
- **@websocket_handler Decorator**: Register WebSocket handlers
  - `@websocket_handler(url='/ws/path')` for easy registration
  - Integration with service layer
  - Lifecycle management (`on_init()`, `on_open()`, `on_message()`, `on_close()`)
  
- **Backward Compatibility**: Old `@websocket` decorator still works

#### Testing Utilities (`cullinan.testing`)

- **ServiceTestCase**: Base test class for service testing
- **MockService**: Mock service for testing
- **TestRegistry**: Isolated registry for testing
- Helper functions for mocking dependencies
- **NEW**: 10 comprehensive async tests covering:
  - Async component initialization and destruction
  - Mixed sync/async lifecycle methods
  - Async service dependencies
  - Warning when async methods called synchronously

#### Performance Optimizations

- **Registry Lookups**: 13.5M operations/sec (extremely fast)
- **Dependency Injection**: 
  - Cached resolution: 0.19µs per lookup
  - Uncached resolution: 2.1ms for complex dependencies
  - 11x speedup with singleton caching
- **Service Registry**: 0.23µs per cached service retrieval
- **Lifecycle Management**: Minimal overhead (~0.004ms per cycle)
- **Memory Efficiency**: ~26 bytes per registry item
- **Complex Dependencies**: 0.16ms to resolve 20 services with 34 dependencies

#### Documentation

- **Updated README.md**: Reflects v0.7.0 architecture
  - New feature highlights
  - Service layer examples
  - WebSocket examples
  - Dependency injection examples
  
- **Enhanced Examples**: 
  - `examples/v070_demo.py`: Comprehensive feature demonstration
  - Service layer with dependencies
  - WebSocket integration
  - Lifecycle hooks
  - Real-time notifications
  
- **Benchmarks**:
  - `benchmarks/benchmark_v070_features.py`: Comprehensive performance benchmarks
  - Registry lookup performance
  - Dependency injection resolution
  - Lifecycle management overhead
  - Async vs sync comparison
  - Memory usage analysis

### Changed

#### Breaking Changes

- **Service Layer**: Old `cullinan.service` removed (was deprecated)
  - Use `from cullinan import service, Service` instead
  - New `Service` class with lifecycle hooks (sync and async)
  - `@service` decorator with dependency support
  - Controller.py updated to use new service registry
  
- **Version**: Updated from v0.8.0-alpha to v0.7.0-alpha1
  - Following semantic versioning
  - Alpha release indicates API may still change

#### Architecture

- **Unified Registry**: All components use consistent registry pattern
  - Services: `ServiceRegistry`
  - Handlers: `HandlerRegistry`
  - WebSockets: `WebSocketRegistry`
  - All extend `core.Registry` base class
  
- **Modular Design**: Clear separation of concerns
  - `core/` - Foundation (registry, DI, lifecycle, context)
  - `service/` - Service layer (enhanced with async support)
  - `handler/` - HTTP handlers
  - `middleware/` - Middleware chain
  - `monitoring/` - Monitoring hooks
  - `testing/` - Testing utilities

- **Full Async Support**: All lifecycle methods support async/await
  - Use `initialize_all_async()` for async on_init methods
  - Use `destroy_all_async()` for async on_destroy methods
  - Warnings logged when async methods called synchronously
  - Seamless mixing of sync and async lifecycle hooks

### Removed

- **cullinan.service**: Old service module completely removed
  - All deprecation warnings eliminated
  - Clean break for v0.7.0 architecture
  
### Fixed

- Service instance access in controllers now uses new service registry
- Async lifecycle methods are properly awaited
- Circular dependency detection improved

### Performance

- 13.5 million registry lookups per second
- 11x faster dependency resolution with caching
- Minimal lifecycle management overhead
- Efficient memory usage (25.5 KB for 1000 items)
- Fast complex dependency graph resolution

### Migration Guide

For users upgrading from v0.6.x to v0.7.0:

1. **Service Layer**:
   ```python
   # Old (v0.6.x) - NO LONGER WORKS
   from cullinan.service import service, Service
   
   # New (v0.7.0)
   from cullinan import service, Service
   ```

2. **Service with Dependencies**:
   ```python
   # New feature in v0.7.0
   @service(dependencies=['EmailService'])
   class UserService(Service):
       def on_init(self):
           self.email = self.dependencies['EmailService']
   ```

3. **Async Service Lifecycle**:
   ```python
   # New in v0.7.0
   @service(dependencies=['DatabaseService'])
   class UserService(Service):
       async def on_init(self):
           self.db = self.dependencies['DatabaseService']
           await self.db.connect()
       
       async def on_destroy(self):
           await self.db.disconnect()
   
   # Initialize with async support
   registry = get_service_registry()
   await registry.initialize_all_async()
   # ... use services ...
   await registry.destroy_all_async()
   ```

4. **WebSocket Handlers**:
   ```python
   # Old (v0.6.x)
   from cullinan.websocket import websocket
   
   # New (v0.7.0) - both work, but new style preferred
   from cullinan import websocket_handler
   
   @websocket_handler(url='/ws/chat')
   class ChatHandler:
       def on_init(self):
           # New lifecycle hook
           pass
   ```

### Technical Details

- **Type Safety**: Generic types for registry pattern
- **Thread Safety**: Context variables for request context
- **Performance**: Benchmarked and optimized for production use
- **Testability**: Enhanced with mock support and test utilities
- **Async First**: Full async/await support throughout

### Test Coverage

- 284 tests passing (added 10 new async tests)
- Comprehensive async lifecycle testing
- Dependency injection tests
- Service registry tests
- Integration tests

---

## [0.6.x] - Legacy Features

### Summary of v0.6.x Features

All features from v0.6.x versions are consolidated here for reference:

#### Configuration System (v0.6.3)

- **Configuration-driven Module Scanning**: `configure()` function for package specification
  - `configure(user_packages=['your_app'])` - Specify packages to scan
  - Support for multiple configuration methods (code, JSON, environment variables)
  - Professional solution for packaging

#### Packaging Support (v0.6.2)

- **Nuitka Support**: Full support for Nuitka compilation (standalone and onefile modes)
  - Intelligent environment detection
  - Specialized module scanning for Nuitka's compilation characteristics
  - Support for both Windows and Linux/macOS
  
- **PyInstaller Support**: Full support for PyInstaller packaging (onedir and onefile modes)
  - _MEIPASS directory scanning
  - Executable directory scanning for onedir mode
  - sys.modules supplementary scanning
  
- **Smart Environment Detection**: 
  - `is_pyinstaller_frozen()`: Detects PyInstaller packaging
  - `is_nuitka_compiled()`: Detects Nuitka compilation
  - `get_pyinstaller_mode()`: Identifies onefile/onedir mode
  - `get_nuitka_standalone_mode()`: Identifies onefile/standalone mode

#### Module Scanning (v0.6.1)

- **Enhanced Module Scanning**:
  - `scan_modules_nuitka()`: Nuitka-specific scanning with 4-layer strategy
  - `scan_modules_pyinstaller()`: PyInstaller-specific scanning with 3-layer strategy
  - Enhanced `reflect_module()` with multiple import strategies
  - Improved `file_list_func()` with environment-aware routing

#### Basic Features (v0.6.0)

- **Controller System**: Decorator-based routing with `@controller` and HTTP method decorators
- **Service Layer**: Simple service registration with `@service` decorator (basic version)
- **Middleware Support**: Middleware chain for request/response processing
- **WebSocket Support**: Basic WebSocket handler registration
- **SQLAlchemy Integration**: Built-in ORM support
- **Cross-Platform**: Windows, Linux, and macOS support

### Fixed (v0.6.x)

- Controller and Service modules not being scanned after Nuitka compilation
- Controller and Service modules not being scanned after PyInstaller packaging
- Incorrect module discovery in onefile mode
- Missing modules in standalone/onedir mode

### Technical Details (v0.6.x)

- **Backward Compatible**: All v0.6.x changes were backward compatible
- **Performance**: Minimal performance impact (< 100ms for scanning)
- **Zero Configuration**: Works out of the box in v0.6.x

---

## Notes

- **v0.7.0+**: New architecture, not backward compatible
- **v0.6.x**: Legacy version, documentation available in `docs/v0.6x/`
- **Migration**: See migration guide above for upgrading from v0.6.x to v0.7.0
