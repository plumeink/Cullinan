import logging

# Prevent "No handlers could be found" warnings when library is imported
# Applications should configure logging (console/file) at their entry point.
logging.getLogger('cullinan').addHandler(logging.NullHandler())

# 导出配置接口
from cullinan.config import configure, get_config, CullinanConfig

# Export path utilities for packaging-aware path resolution
from cullinan.path_utils import (
    # Environment detection
    is_frozen,
    is_pyinstaller_frozen,
    is_nuitka_compiled,
    get_packaging_mode,
    # Path resolution
    get_base_path,
    get_cullinan_package_path,
    get_resource_path,
    get_module_file_path,
    get_executable_dir,
    get_user_data_dir,
    # Utilities
    find_file_with_fallbacks,
    import_module_from_path,
    get_path_info,
    log_path_info,
)

# Export core module (foundational components)
from cullinan.core import (
    # IoC/DI 2.0
    ApplicationContext,
    service,
    controller,
    component,
    Inject,
    InjectByName,
    Lazy,
    Provider,
    PendingRegistry,
    CullinanSemanticWarning,
    ComponentDiscoveryWarning,
    CompatibilitySemanticWarning,
    InjectionSemanticWarning,
    PublicAPISemanticWarning,
    # Core infrastructure
    Registry,
    SimpleRegistry,
    LifecycleManager,
    LifecycleState,
    LifecycleAware,
    RequestContext,
    get_current_context,
    set_current_context,
    create_context,
    destroy_context,
    ContextManager,
    get_context_value,
    set_context_value,
    # Compatibility
    injectable,
    get_injection_registry,
    reset_injection_registry,
)

from cullinan.application_model import (
    Application,
    Module,
    Runtime,
    current_app,
    module,
)

# Export enhanced service layer
from cullinan.service import (
    Service,
    ServiceRegistry,
    get_service_registry,
    reset_service_registry,
)


# Export middleware module
from cullinan.middleware import (
    Middleware,
    MiddlewareChain,
    MiddlewareRegistry,
    get_middleware_registry,
    reset_middleware_registry,
    middleware,
)

# Export extensions module
from cullinan.extensions import (
    ExtensionCategory,
    ExtensionPoint,
    ExtensionRegistry,
    get_extension_registry,
    reset_extension_registry,
    list_extension_points,
)

# Export monitoring module
from cullinan.monitoring import (
    MonitoringHook,
    MonitoringManager,
    get_monitoring_manager,
    reset_monitoring_manager,
)

# Export testing utilities
from cullinan.testing import (
    ServiceTestCase,
    MockService,
    TestRegistry,
)

# Export WebSocket support
from cullinan.websocket_registry import (
    WebSocketRegistry,
    websocket_handler,
    get_websocket_registry,
    reset_websocket_registry,
)

# Export codec module
from cullinan.codec import (
    BodyCodec,
    ResponseCodec,
    CodecError,
    DecodeError,
    EncodeError,
    JsonBodyCodec,
    JsonResponseCodec,
    FormBodyCodec,
    CodecRegistry,
    get_codec_registry,
    reset_codec_registry,
)

# Export params module
from cullinan.params import (
    Param,
    UNSET,
    Path,
    Query,
    Body,
    Header,
    File,
    TypeConverter,
    ConversionError,
    Auto,
    AutoType,
    DynamicBody,
    ParamValidator,
    ValidationError,
    ModelResolver,
    ModelError,
    ParamResolver,
    ResolveError,
)

# Export body decoder middleware
from cullinan.middleware import (
    BodyDecoderMiddleware,
    get_decoded_body,
    set_decoded_body,
)

# Export gateway module (v0.93 transport-agnostic layer)
from cullinan.gateway import (
    WebRequest,
    WebResponse,
    WebHeaders,
    WebCookies,
    WebExchange,
    HeaderPolicy,
    Router,
    Dispatcher,
    MiddlewarePipeline,
    GatewayMiddleware,
    CORSMiddleware,
    RequestTimingMiddleware,
    AccessLogMiddleware,
    ExceptionHandler,
    WebRuntime,
    WebRuntimeConfig,
    WebRuntimeState,
    OpenAPIGenerator,
    get_router,
    get_dispatcher,
    get_pipeline,
    get_exception_handler,
    reset_gateway,
)

# Export adapter module (v0.93 server runtime adapters)
from cullinan.adapter import WebAdapter, ASGIAdapter
try:
    from cullinan.adapter import TornadoAdapter
except (ImportError, TypeError):
    TornadoAdapter = None  # type: ignore[assignment,misc]

# Export controller registry and decorators from controller package
# Note: 'controller' is both a package and a decorator function
# To avoid naming conflicts in Nuitka and other packagers:
# - The package cullinan.controller contains all controller-related code
# - Import the controller decorator as: from cullinan.controller import controller
from cullinan.controller import (
    ControllerRegistry,
    get_controller_registry,
    reset_controller_registry,
    # Controller decorators (import from cullinan.controller, not directly from cullinan)
    get_api,
    post_api,
    patch_api,
    delete_api,
    put_api,
    Handler,
    response,
    # Missing header handler API
    set_missing_header_handler,
    get_missing_header_handler,
)

from cullinan.public_api import get_asgi_app, run

# Restore decorator-style public names after importing same-named submodules.
from cullinan.core import (
    service as _service_decorator,
    controller as _controller_decorator,
    component as _component_decorator,
    warn_semantic_once,
)
from cullinan.application_model import module as _module_decorator
from cullinan.middleware import middleware as _middleware_decorator

service = _service_decorator
controller = _controller_decorator
component = _component_decorator
module = _module_decorator
middleware = _middleware_decorator
_public_api_semantic_warning = PublicAPISemanticWarning


__version__ = '0.93a6.post1'

__all__ = [
    'configure',
    'get_config',
    'CullinanConfig',
    'run',
    'get_asgi_app',
    'service',
    'controller',
    'component',
    'module',
    'middleware',
    'websocket_handler',
    'Inject',
    'InjectByName',
    'Lazy',
    'Provider',
    'Service',
    'Middleware',
    'BodyDecoderMiddleware',
    'get_decoded_body',
    'Param',
    'UNSET',
    'Path',
    'Query',
    'Body',
    'Header',
    'File',
    'TypeConverter',
    'ConversionError',
    'Auto',
    'AutoType',
    'DynamicBody',
    'ParamValidator',
    'ValidationError',
    'ModelResolver',
    'ModelError',
    'ParamResolver',
    'ResolveError',
    'WebRequest',
    'WebResponse',
    'WebAdapter',
    'get_api',
    'post_api',
    'patch_api',
    'delete_api',
    'put_api',
    'response',
]

_COMPAT_EXPORT_NAMES = [
    'Registry',
    'SimpleRegistry',
    'LifecycleManager',
    'LifecycleState',
    'LifecycleAware',
    'RequestContext',
    'get_current_context',
    'set_current_context',
    'create_context',
    'destroy_context',
    'ContextManager',
    'get_context_value',
    'set_context_value',
    'ServiceRegistry',
    'get_service_registry',
    'reset_service_registry',
    'MiddlewareChain',
    'MiddlewareRegistry',
    'get_middleware_registry',
    'reset_middleware_registry',
    'ExtensionCategory',
    'ExtensionPoint',
    'ExtensionRegistry',
    'get_extension_registry',
    'reset_extension_registry',
    'list_extension_points',
    'MonitoringHook',
    'MonitoringManager',
    'get_monitoring_manager',
    'reset_monitoring_manager',
    'ServiceTestCase',
    'MockService',
    'TestRegistry',
    'WebSocketRegistry',
    'get_websocket_registry',
    'reset_websocket_registry',
    'BodyCodec',
    'ResponseCodec',
    'CodecError',
    'DecodeError',
    'EncodeError',
    'JsonBodyCodec',
    'JsonResponseCodec',
    'FormBodyCodec',
    'CodecRegistry',
    'get_codec_registry',
    'reset_codec_registry',
    'set_decoded_body',
    'WebHeaders',
    'WebCookies',
    'WebExchange',
    'HeaderPolicy',
    'Router',
    'Dispatcher',
    'MiddlewarePipeline',
    'GatewayMiddleware',
    'CORSMiddleware',
    'RequestTimingMiddleware',
    'AccessLogMiddleware',
    'ExceptionHandler',
    'WebRuntime',
    'WebRuntimeConfig',
    'WebRuntimeState',
    'OpenAPIGenerator',
    'get_router',
    'get_dispatcher',
    'get_pipeline',
    'get_exception_handler',
    'reset_gateway',
    'TornadoAdapter',
    'ASGIAdapter',
    'ControllerRegistry',
    'get_controller_registry',
    'reset_controller_registry',
    'Handler',
    'set_missing_header_handler',
    'get_missing_header_handler',
    'is_frozen',
    'is_pyinstaller_frozen',
    'is_nuitka_compiled',
    'get_packaging_mode',
    'get_base_path',
    'get_cullinan_package_path',
    'get_resource_path',
    'get_module_file_path',
    'get_executable_dir',
    'get_user_data_dir',
    'find_file_with_fallbacks',
    'import_module_from_path',
    'get_path_info',
    'log_path_info',
    'CullinanSemanticWarning',
    'ComponentDiscoveryWarning',
    'CompatibilitySemanticWarning',
    'InjectionSemanticWarning',
    'PublicAPISemanticWarning',
    'injectable',
    'get_injection_registry',
    'reset_injection_registry',
    'ApplicationContext',
    'PendingRegistry',
    'Application',
    'Module',
    'Runtime',
    'current_app',
]
_COMPAT_EXPORTS = {name: globals()[name] for name in _COMPAT_EXPORT_NAMES if name in globals()}

for _compat_name in _COMPAT_EXPORT_NAMES:
    globals().pop(_compat_name, None)


def __getattr__(name):
    if name in _COMPAT_EXPORTS:
        warn_semantic_once(
            key=f"public-api:top-level:{name}",
            rule_key="public-api-boundary",
            problem=f"顶层导入 {name} 会绕过 Cullinan 推荐 API 分层。",
            guidance="常规业务应用请优先使用 from cullinan import configure, run 以及业务装饰器；如果确实需要高级能力，请从对应子模块显式导入。",
            category=_public_api_semantic_warning,
            stacklevel=2,
        )
        value = _COMPAT_EXPORTS[name]
        globals()[name] = value
        return value
    raise AttributeError(f"module 'cullinan' has no attribute {name!r}")


def __dir__():
    return sorted(set(__all__ + ['__version__']))
