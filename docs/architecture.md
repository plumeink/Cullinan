# Cullinan Framework Architecture Document (Updated)

> **Version**: v0.92  
> **Last Updated**: 2026-02-19  
> **Author**: Plumeink  
> **Status**: Updated

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [IoC/DI 2.0 System](#iocdi-20-system)
4. [Extension Mechanism](#extension-mechanism)
5. [Startup Flow](#startup-flow)
6. [Request Processing Flow](#request-processing-flow)
7. [Module Scanning](#module-scanning)
8. [Performance Optimization](#performance-optimization)
9. [Migration from 0.83](#migration-from-083)

---

## Architecture Overview

Cullinan is a Tornado-based web framework that adopts the **IoC/DI** (Inversion of Control/Dependency Injection) design pattern and provides a decorator-driven development experience.

### Core Design Principles

- **Non-invasive**: Implement features through decorators and annotations without inheriting complex base classes
- **Dependency Injection**: Automatically manage component dependencies
- **Extension-friendly**: Unified extension point registration and discovery mechanism
- **High Performance**: Optimized startup and runtime performance

### Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│          Application Layer                           │
│  - Business Logic (Controllers)                      │
│  - Service Layer (Services)                          │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┼───────────────────────────────────┐
│          Framework Layer                             │
│  ┌──────────────┴──────────────┐                     │
│  │    Extension Mechanism      │                     │
│  │  - Middleware               │                     │
│  │  - Extension Points         │                     │
│  └──────────────┬──────────────┘                     │
│  ┌──────────────┴──────────────┐                     │
│  │  IoC/DI 2.0 Container       │                     │
│  │  - ApplicationContext       │                     │
│  │  - Definition + Factory     │                     │
│  │  - ScopeManager             │                     │
│  │  - Structured Diagnostics   │                     │
│  └──────────────┬──────────────┘                     │
│  ┌──────────────┴──────────────┐                     │
│  │    Core Foundation          │                     │
│  │  - Lifecycle Management     │                     │
│  │  - Request Context          │                     │
│  │  - Module Scanner           │                     │
│  └─────────────────────────────┘                     │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│          Web Server Layer (Tornado)                  │
│  - IOLoop                                            │
│  - HTTP Server                                       │
│  - Request Handler                                   │
└─────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Core Module (`cullinan/core/`)

Provides framework infrastructure.

**Main Components**:

#### 1.1 IoC/DI 2.0 Container

```
ApplicationContext (Single Entry Point)
    ├── Definition Registry (Immutable definitions)
    ├── Factory (Instance creation)
    └── ScopeManager (Scope management)
        ├── SingletonScope
        ├── PrototypeScope
        └── RequestScope
```

**Core Components (v0.90)**:
- **ApplicationContext**: Single entry point for all container operations
  - `register(Definition)` - Register dependency definition
  - `get(name)` / `try_get(name)` - Resolve dependency
  - `refresh()` - Freeze registry, initialize eager beans
  - `shutdown()` - Clean up resources

- **Definition**: Immutable dependency definition
  - `name` - Unique identifier
  - `factory` - Instance creation function
  - `scope` - ScopeType (SINGLETON/PROTOTYPE/REQUEST)
  - `source` - Source description for diagnostics

- **Factory**: Unified instance creation
  - Creates instances via Definition.factory
  - Delegates to ScopeManager for caching

- **ScopeManager**: Unified scope management
  - `SINGLETON` - Application-level singleton (thread-safe)
  - `PROTOTYPE` - New instance per resolution
  - `REQUEST` - Request-scoped instances

**New Directory Structure (v0.90)**:
```
cullinan/core/
├── container/      # IoC/DI 2.0 API
│   ├── context.py
│   ├── definitions.py
│   ├── factory.py
│   └── scope.py
├── diagnostics/    # Exceptions + rendering
├── lifecycle/      # Lifecycle management
├── request/        # Request context
└── legacy/         # Deprecated 1.x components
```

#### 1.2 Lifecycle Management

```python
class LifecycleManager:
    - initialize()    # Initialization phase
    - startup()       # Startup phase
    - shutdown()      # Shutdown phase
```

#### 1.2 Lifecycle Management

```python
class LifecycleManager:
    - refresh()       # Initialize/Startup phase
    - shutdown()      # Shutdown phase
```

**Unified Lifecycle Hooks (v0.92+)**:
- `on_post_construct()` - Execute after dependency injection
- `on_startup()` - Execute during application startup
- `on_shutdown()` - Execute during application shutdown
- `on_pre_destroy()` - Execute before destruction

All hooks support async versions (append `_async` suffix).

#### 1.3 Request Context

```python
class RequestContext:
    - request_id: str
    - start_time: float
    - _metadata: Dict (lazy initialization)
    - _cleanup_callbacks: List (lazy initialization)
```

**Optimizations** (v0.81+):
- Lazy initialization: Save 20-55% memory
- Performance: Initialization from 500ns → 350ns

#### 1.4 Scope System

- **SingletonScope**: Singleton scope
- **TransientScope**: Transient scope (create new each time)
- **RequestScope**: Request scope
- **Custom Scope**: Support user extensions (e.g., SessionScope)

---

### 2. Service Layer (`cullinan/service/`)

Manages application business services.

**Usage**:
```python
from cullinan.service import service, Service
from cullinan.core import Inject

@service
class UserService(Service):
    email_service: 'EmailService' = Inject()
    
    def on_startup(self):
        # Initialize resources
        self.db = connect_database()
    
    def on_shutdown(self):
        # Clean up resources
        self.db.close()
```

**Features**:
- Singleton pattern (application-level)
- Automatic dependency injection
- Lifecycle management
- Startup error policies (strict/warn/ignore)

---

### 3. Controller Layer (`cullinan/controller/`)

Handles HTTP requests.

**Usage**:
```python
from cullinan.controller import controller, get_api
from cullinan.core import Inject
from cullinan.params import Path

@controller(url='/api/users')
class UserController:
    user_service: 'UserService' = Inject()
    
    @get_api(url='/{user_id}')
    async def get_user(self, user_id: int = Path()):
        return self.user_service.get_user(user_id)
```

**Features**:
- RESTful route mapping
- Automatic dependency injection
- Request-level instances (new per request)
- Automatic parameter parsing and validation

---

### 4. Parameter System (`cullinan/params/`, `cullinan/codec/`) - New in v0.90

Type-safe parameter handling with automatic conversion and validation.

**Module Structure**:
```
cullinan/
├── codec/           # Encoding/Decoding layer
│   ├── base.py     # BodyCodec / ResponseCodec abstractions
│   ├── errors.py   # DecodeError / EncodeError
│   ├── json_codec.py
│   ├── form_codec.py
│   └── registry.py # CodecRegistry
├── params/          # Parameter handling layer
│   ├── base.py     # Param base class + UNSET
│   ├── types.py    # Path/Query/Body/Header/File
│   ├── converter.py # TypeConverter
│   ├── auto.py     # Auto type inference
│   ├── dynamic.py  # DynamicBody
│   ├── validator.py # ParamValidator
│   ├── model.py    # ModelResolver (dataclass)
│   └── resolver.py # ParamResolver
└── middleware/
    └── body_decoder.py # BodyDecoderMiddleware
```

**Usage**:
```python
from cullinan.params import Path, Query, Body, DynamicBody

@controller(url='/api/users')
class UserController:
    @get_api(url='/{id}')
    async def get_user(
        self,
        id: int = Path(),
        include_posts: bool = Query(default=False),
    ):
        return {"id": id}
    
    @post_api(url='/')
    async def create_user(
        self,
        name: str = Body(required=True),
        age: int = Body(default=0, ge=0, le=150),
    ):
        return {"name": name, "age": age}
```

**Features**:
- Type-safe parameter declaration
- Automatic type conversion
- Built-in validators (ge, le, regex, etc.)
- dataclass and DynamicBody support
- Custom codec registration

See [Parameter System Guide](parameter_system_guide.md) for details.

---

### 5. Extension Mechanism

#### 5.1 Middleware System

```python
from cullinan.middleware import middleware, Middleware

@middleware(priority=100)
class LoggingMiddleware(Middleware):
    def process_request(self, handler):
        logger.info(f"Request: {handler.request.uri}")
        return handler
    
    def process_response(self, handler, response):
        logger.info(f"Response: {response}")
        return response
```

**Features**:
- Decorator-driven registration
- Priority control (lower numbers execute first)
- Bidirectional request/response interception
- Support short-circuiting (return None to stop)

#### 5.2 Extension Point Discovery

```python
from cullinan.extensions import list_extension_points

# Query available extension points
points = list_extension_points(category='middleware')
for point in points:
    print(f"{point['name']}: {point['description']}")
```

**6 Extension Categories**:
1. **Middleware** - Request/response interception
2. **Lifecycle** - Lifecycle hooks
3. **Injection** - Dependency injection extensions
4. **Routing** - Route handling
5. **Configuration** - Configuration management
6. **Handler** - Request handlers

---

## IoC/DI 2.0 System

### New Architecture (v0.90)

```
┌─────────────────────────────────────┐
│   ApplicationContext (Entry Point)  │
│  - register(Definition)             │
│  - get(name) / try_get(name)        │
│  - refresh() / shutdown()           │
└───────────────┬─────────────────────┘
                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼
┌──────────┐ ┌─────────┐ ┌────────────┐
│Definition│ │ Factory │ │ScopeManager│
│ Registry │ │         │ │            │
└──────────┘ └─────────┘ └────────────┘
```

### Key Improvements

| Feature | 0.83 (Legacy) | 0.90 (2.0) |
|---------|---------------|------------|
| Entry Point | Multiple (IoCFacade, Registries) | Single (ApplicationContext) |
| Definition | Mutable | Immutable (frozen) |
| Registry | Modifiable at runtime | Frozen after refresh() |
| Scopes | Implicit | Explicit ScopeType enum |
| Diagnostics | String-based errors | Structured exceptions |

### Usage Patterns

#### Pattern 1: Decorator-Based Automatic Injection (Recommended)

```python
from cullinan.service import service, Service
from cullinan.core import Inject

@service
class UserService(Service):
    email_service: EmailService = Inject()  # Auto-inject
    
    def on_post_construct(self):
        # Execute after dependency injection
        pass
    
    def on_startup(self):
        # Execute during application startup
        pass
```

**Features**:
- Decorators internally use the new IoC/DI 2.0 registration logic
- Automatic dependency resolution and lifecycle management
- Supports `Inject()` attribute injection

#### Pattern 2: Definition-Based Registration (Advanced)

```python
from cullinan.core.container import ApplicationContext, Definition, ScopeType

ctx = ApplicationContext()

# Register with explicit definition (for complex scenarios or third-party integration)
ctx.register(Definition(
    name='UserService',
    factory=lambda c: UserService(c.get('UserRepository')),
    scope=ScopeType.SINGLETON,
    source='service:UserService'
))

ctx.refresh()  # Freeze registry
user_service = ctx.get('UserService')
```

**Use Cases**:
- Custom instance creation logic required
- Integrating third-party library components
- Dynamic dependency registration needed

---

## Extension Mechanism

### Middleware Execution Flow

```
Client Request
  ↓
CorsMiddleware (priority=10)      → process_request
  ↓
AuthMiddleware (priority=50)      → process_request
  ↓
LoggingMiddleware (priority=100)  → process_request
  ↓
Handler Processing
  ↓
LoggingMiddleware (priority=100)  → process_response
  ↓
AuthMiddleware (priority=50)      → process_response
  ↓
CorsMiddleware (priority=10)      → process_response
  ↓
Client Response
```

**Priority Guidelines**:
- `0-50`: Critical middleware (CORS, security)
- `51-100`: Standard middleware (logging, metrics)
- `101-200`: Application-specific middleware

---

## Startup Flow

### Startup Sequence

```
1. configure(...)
   └── Load configuration

2. Module Scanning
   ├── Auto-scan mode
   │   ├── Detect packaging environment (development/nuitka/pyinstaller)
   │   ├── Scan user packages (user_packages)
   │   └── Collect statistics (New in v0.81+)
   │
   └── Explicit registration mode (New in v0.81+)
       └── Skip scanning, use configured classes directly

3. IoC Container Initialization
   ├── Initialize IoCFacade
   ├── Register Providers
   └── Configure InjectionRegistry

4. Service Initialization
   ├── Initialize in dependency order
   ├── Call on_post_construct() hooks
   ├── Call on_startup() hooks
   └── Error handling (per startup_error_policy)

5. Controller Registration
   ├── Register routes
   └── Configure Handlers

6. Middleware Chain Building
   ├── Sort by priority
   ├── Initialize middleware (on_startup)
   └── Build processing chain

7. Start Web Server
   ├── Create Tornado Application
   ├── Register signal handlers (SIGINT/SIGTERM)
   └── Start IOLoop
```

### Startup Performance (v0.81+ Optimized)

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| Explicit registration mode | 69.56 ms | 0.08 ms | **902x** |
| Small project (10 modules) | 50-100 ms | 50-100 ms | - |
| Medium project (50 modules) | 300-800 ms | 150-300 ms | **2x** |

---

## Request Processing Flow

```
1. Request arrives at Tornado
   └── IOLoop dispatches to Handler

2. Create request context
   ├── RequestContext.create()
   ├── Set request_id
   └── Initialize request-level Scope

3. Middleware processing (request phase)
   ├── Execute process_request() by priority
   ├── May short-circuit (e.g., auth failure)
   └── Pass to next middleware

4. Controller instantiation
   ├── Create Controller instance
   ├── Inject dependencies (via InjectionRegistry)
   └── Parse request parameters

5. Execute business logic
   ├── Call Controller method
   ├── Service layer processing
   └── Return response

6. Middleware processing (response phase)
   ├── Execute process_response() in reverse
   ├── Can modify response
   └── Add response headers

7. Clean up request context
   ├── Execute cleanup callbacks
   ├── Clear request-level dependencies
   └── Destroy RequestContext

8. Return response to client
```

---

## Module Scanning

### Scanning Strategy (Multi-environment Support)

```
┌─────────────────────────────────────┐
│    Detect Packaging Environment      │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┬─────────┬─────────┐
     ▼           ▼         ▼         ▼
Development  Nuitka   PyInstaller  Other
     │           │         │         │
     ▼           ▼         ▼         ▼
  Standard   sys.modules  _MEIPASS  Fallback
  Scanning
```

### Scanning Statistics (New in v0.81+)

```python
from cullinan.scan_stats import get_scan_stats_collector

collector = get_scan_stats_collector()
stats = collector.get_aggregate_stats()

# Output:
# {
#   'total_scans': 1,
#   'avg_duration_ms': 66.06,
#   'total_modules': 35,
#   'fastest_scan_ms': 66.06,
#   'slowest_scan_ms': 66.06
# }
```

**Collected Metrics**:
- Total duration (phased)
- Module count (discovered/filtered/cached)
- Scan mode (auto/explicit/cached)
- Packaging environment (development/nuitka/pyinstaller)
- Error recording

---

## Performance Optimization

### Implemented Optimizations (v0.81+)

| Optimization | Before | After | Improvement |
|-------------|--------|-------|-------------|
| **Module Scanning (Explicit)** | 69.56 ms | 0.08 ms | **902x** |
| **RequestContext Init** | 500 ns | 350 ns | **30%** |
| **RequestContext Memory** | 536 B | 240 B | **55%** |
| **Dependency Resolution (Cached)** | - | 0.26 μs | **Extremely Fast** |
| **Logging Overhead (Production)** | 150 ns | 100 ns | **33%** |

### Optimization Strategies

#### 1. Explicit Registration Mode

```python
from cullinan import configure

configure(
    explicit_services=[DatabaseService, CacheService],
    explicit_controllers=[UserController, AdminController],
    auto_scan=False  # Skip scanning
)
```

**Benefit**: 902x startup speed improvement (test scenario)

#### 2. Lazy Initialization

- RequestContext fields created on demand
- 55% memory reduction

#### 3. Smart Caching

- Module scanning result cache
- IoC dependency resolution cache (0.26 μs)
- Provider instance cache

#### 4. Structured Logging

- Production log optimization
- Lazy evaluation reduces overhead

---

## Configuration Options

### Core Configuration

```python
from cullinan import configure

configure(
    # Basic configuration
    port=8080,
    debug=True,
    
    # Performance optimization
    explicit_services=[...],      # Explicit service registration
    explicit_controllers=[...],   # Explicit controller registration
    auto_scan=False,              # Disable auto-scanning
    user_packages=['myapp'],      # Limit scan scope
    
    # Startup behavior
    startup_error_policy='strict', # 'strict'/'warn'/'ignore'
    
    # Extension configuration
    middlewares=[...],            # Custom middleware
    handlers=[...],               # Custom Handler
)
```

---

## Best Practices

### 1. Dependency Injection

✅ **Recommended**: Use type injection
```python
@service
class UserService(Service):
    email_service: EmailService = Inject()
```

❌ **Avoid**: Manually getting dependencies
```python
# Not recommended
registry = get_service_registry()
email_service = registry.get_instance('EmailService')
```

### 2. Performance Optimization

✅ **Recommended**: Use explicit registration (large projects)
```python
configure(
    explicit_services=[...],
    explicit_controllers=[...],
    auto_scan=False
)
```

✅ **Recommended**: Limit scan scope
```python
configure(
    user_packages=['myapp', 'myapp.extensions'],
    exclude_packages=['tests', '__pycache__']
)
```

### 3. Middleware Design

✅ **Recommended**: Single responsibility
```python
@middleware(priority=50)
class AuthMiddleware(Middleware):  # Only handles auth
    pass

@middleware(priority=60)
class RoleMiddleware(Middleware):  # Only handles permissions
    pass
```

❌ **Avoid**: Mixed responsibilities
```python
@middleware(priority=50)
class AuthAndLoggingMiddleware(Middleware):  # Mixed
    pass
```

---

## References

- [Extension Development Guide](./extension_development_guide.md)
- [API Reference](./api_reference.md)
- [Getting Started](./getting_started.md)
- [Migration Guide](./migration_guide.md)

---

## Migration from 0.83

For migration from version 0.83 to 0.90, see the [Import Migration Guide](./import_migration_090.md).

Key changes:
- `cullinan.core.application_context` → `cullinan.core.container`
- `cullinan.core.definitions` → `cullinan.core.container`
- `cullinan.core.exceptions` → `cullinan.core.diagnostics`
- `cullinan.core.context` → `cullinan.core.request`
- Legacy components moved to `cullinan.core.legacy/`

---

**Version**: v0.90  
**Author**: Plumeink  
**Last Updated**: 2025-12-25

