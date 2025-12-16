# Cullinan Framework Architecture (Updated)

> **Version**: v0.81+  
> **Last Updated**: 2025-12-16  
> **Author**: Plumeink  
> **Status**: Updated

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [IoC/DI System](#iocdi-system)
4. [Extension Mechanism](#extension-mechanism)
5. [Startup Flow](#startup-flow)
6. [Request Processing Flow](#request-processing-flow)
7. [Module Scanning](#module-scanning)
8. [Performance Optimization](#performance-optimization)

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
│  │    IoC/DI Container         │                     │
│  │  - IoCFacade (Unified API)  │                     │
│  │  - InjectionRegistry        │                     │
│  │  - ProviderRegistry         │                     │
│  │  - ServiceRegistry          │                     │
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

#### 1.1 IoC/DI Container

```
IoCFacade (Unified Entry Point)
    ├── InjectionRegistry (Injection Registry)
    ├── ProviderRegistry (Provider Registry)
    └── ServiceRegistry (Service Registry)
```

**Responsibilities**:
- **IoCFacade** (New in v0.81+): Unified dependency resolution interface
  - `resolve(Type)` - Resolve by type
  - `resolve_by_name(name)` - Resolve by name
  - `has_dependency(Type)` - Check dependency
  - Performance: 0.26 μs (cache hit)

- **InjectionRegistry**: Dependency injection coordinator
  - Scan type annotations (`Inject()`, `InjectByName()`)
  - Coordinate multiple Provider Registries
  - Circular dependency detection

- **ProviderRegistry**: Provider management
  - Manage different Provider types (Instance, Class, Factory, Scoped)
  - Support singleton and transient modes

- **ServiceRegistry**: Service lifecycle management
  - Register and initialize `@service` decorated classes
  - Manage Service lifecycle hooks
  - Dependency-ordered initialization

#### 1.2 Lifecycle Management

```python
class LifecycleManager:
    - initialize()    # Initialization phase
    - startup()       # Startup phase
    - shutdown()      # Shutdown phase
```

**Lifecycle Hooks**:
- `on_init()` - Execute after Service instantiation
- `on_startup()` - Execute after all Services are ready
- `on_shutdown()` - Execute during application shutdown

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
    
    def on_init(self):
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

@controller('/api/users')
class UserController:
    user_service: 'UserService' = Inject()
    
    @get_api('/<user_id>')
    def get_user(self, user_id: int):
        return self.user_service.get_user(user_id)
```

**Features**:
- RESTful route mapping
- Automatic dependency injection
- Request-level instances (new per request)
- Automatic parameter parsing and validation

---

### 4. Extension Mechanism (New in v0.81+)

#### 4.1 Middleware System

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

#### 4.2 Extension Point Discovery

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

## IoC/DI System

### Three-Tier Architecture + Facade

```
┌─────────────────────────────────────┐
│     IoCFacade (Unified Entry)        │
│  - resolve(Type)                    │
│  - resolve_by_name(name)            │
│  - has_dependency(Type)             │
│  - Cache management                 │
└───────────────┬─────────────────────┘
                │
      ┌─────────┼──────────┐
      ▼         ▼          ▼
┌──────────┐ ┌─────────┐ ┌──────────────┐
│ Service  │ │Provider │ │  Injection   │
│ Registry │ │Registry │ │  Registry    │
└──────────┘ └─────────┘ └──────────────┘
```

### Dependency Resolution Priority

1. **ServiceRegistry** - Highest priority (framework services)
2. **ProviderRegistry** - Medium priority (configured Providers)
3. **InjectionRegistry** - Fallback (uses provider registries)

### Usage Patterns

#### Pattern 1: Automatic Injection (Recommended)

```python
@service
class UserService(Service):
    email_service: EmailService = Inject()  # Auto-inject
```

#### Pattern 2: Manual Resolution

```python
from cullinan.core.facade import resolve_dependency

# Resolve by type
user_service = resolve_dependency(UserService)

# Resolve by name
config = resolve_dependency_by_name('Config')

# Optional dependency
cache = resolve_dependency(CacheService, required=False)
```

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
   ├── Call on_init() hooks
   ├── Call on_startup() hooks
   └── Error handling (per startup_error_policy)

5. Controller Registration
   ├── Register routes
   └── Configure Handlers

6. Middleware Chain Building
   ├── Sort by priority
   ├── Initialize middleware (on_init)
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

**Version**: v0.81+  
**Author**: Plumeink  
**Last Updated**: 2025-12-16

