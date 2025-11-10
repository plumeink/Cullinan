# Changelog

All notable changes to the Cullinan project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.7.0-alpha1] - 2025-11-10

### 🚀 Major Architectural Refactoring

This is a major release with breaking changes and a completely redesigned architecture. Version 0.7.0 is not backward compatible with 0.6.x.

### Added

#### Core Module (`cullinan.core`)

- **Registry Pattern**: Base `Registry` class for unified component registration
  - Abstract `Registry[T]` class with type safety
  - `SimpleRegistry` concrete implementation
  - Methods: `register()`, `get()`, `has()`, `list_all()`, `get_metadata()`, `clear()`
  
- **Dependency Injection**: `DependencyInjector` for managing component dependencies
  - Provider-based dependency resolution
  - Singleton instance management
  - Circular dependency detection
  - Optional dependency support
  
- **Lifecycle Management**: `LifecycleManager` for component lifecycle
  - `LifecycleState` enum (UNINITIALIZED, INITIALIZING, INITIALIZED, DESTROYED)
  - `LifecycleAware` interface for components
  - Hooks: `on_init()`, `on_destroy()`
  - Automatic initialization and cleanup
  
- **Request Context**: Thread-safe request context management
  - `RequestContext` class for request-scoped data
  - Context variables using `contextvars` for thread safety
  - `ContextManager` for automatic context lifecycle
  - Convenience functions: `get_current_context()`, `set_current_context()`
  - Methods: `set()`, `get()`, `has()`, `delete()`, `clear()`
  - Metadata support and cleanup callbacks

#### Enhanced Service Layer (`cullinan.service_new`)

- **Service Base Class**: Enhanced `Service` with lifecycle hooks
  - `on_init()`: Called when service is initialized
  - `on_destroy()`: Called on application shutdown
  - Access to dependencies via `self.dependencies`
  
- **ServiceRegistry**: Service-specific registry extending `core.Registry`
  - Dependency injection support
  - Singleton service instances
  - Automatic dependency resolution
  - Metadata storage
  
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

### Changed

#### Breaking Changes

- **Service Layer**: Old `cullinan.service` deprecated
  - Use `cullinan.service_new` or import from `cullinan` directly
  - New `Service` class with lifecycle hooks
  - `@service` decorator with dependency support
  - Old service implementation triggers deprecation warnings
  
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
  - `service_new/` - Service layer
  - `handler/` - HTTP handlers
  - `middleware/` - Middleware chain
  - `monitoring/` - Monitoring hooks
  - `testing/` - Testing utilities

### Deprecated

- **cullinan.service**: Old service module (will be removed in v0.8.0)
  - Use `from cullinan import service, Service` instead
  - Deprecation warnings added

### Migration Guide

For users upgrading from v0.6.x to v0.7.0:

1. **Service Layer**:
   ```python
   # Old (v0.6.x)
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

3. **WebSocket Handlers**:
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
- **Performance**: Minimal overhead from new architecture
- **Testability**: Enhanced with mock support and test utilities

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
