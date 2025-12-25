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
    PendingRegistry,
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

# Export enhanced service layer
from cullinan.service import (
    Service,
    ServiceRegistry,
    get_service_registry,
    reset_service_registry,
)

# Export handler module
from cullinan.handler import (
    HandlerRegistry,
    get_handler_registry,
    reset_handler_registry,
    BaseHandler,
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


__version__ = '0.90'

__all__ = [
    # Configuration
    'configure',
    'get_config',
    'CullinanConfig',
    
    # Core module
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
    
    # Service layer
    'Service',
    'ServiceRegistry',
    'service',
    'get_service_registry',
    'reset_service_registry',
    
    # Handler layer
    'HandlerRegistry',
    'get_handler_registry',
    'reset_handler_registry',
    'BaseHandler',
    
    # Middleware
    'Middleware',
    'MiddlewareChain',
    'MiddlewareRegistry',
    'get_middleware_registry',
    'reset_middleware_registry',
    'middleware',

    # Extensions
    'ExtensionCategory',
    'ExtensionPoint',
    'ExtensionRegistry',
    'get_extension_registry',
    'reset_extension_registry',
    'list_extension_points',

    # Monitoring
    'MonitoringHook',
    'MonitoringManager',
    'get_monitoring_manager',
    'reset_monitoring_manager',
    
    # Testing
    'ServiceTestCase',
    'MockService',
    'TestRegistry',
    
    # WebSocket
    'WebSocketRegistry',
    'websocket_handler',
    'get_websocket_registry',
    'reset_websocket_registry',

    # Controller module (import controller decorator from cullinan.controller)
    'ControllerRegistry',
    'get_controller_registry',
    'reset_controller_registry',
    'get_api',
    'post_api',
    'patch_api',
    'delete_api',
    'put_api',
    'Handler',
    'response',
    'set_missing_header_handler',
    'get_missing_header_handler',

    # Path utilities (packaging support)
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

    # Dependency Injection
    'Inject',
    'InjectByName',
    'Lazy',
    'injectable',
    'get_injection_registry',
    'reset_injection_registry',

    # IoC/DI 2.0
    'ApplicationContext',
    'PendingRegistry',
    'service',
    'controller',
    'component',
]

# ============================================================================
# IMPORTANT: Re-import decorators to override submodule names
# Python's import system may return submodules (cullinan.service, cullinan.controller)
# instead of the decorator functions we imported earlier.
# These explicit assignments ensure the decorators are available at package level.
# ============================================================================
from cullinan.core.decorators import service, controller, component
from cullinan.core.decorators import Inject, InjectByName, Lazy

