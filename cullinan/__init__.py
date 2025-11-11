import logging

# Prevent "No handlers could be found" warnings when library is imported
# Applications should configure logging (console/file) at their entry point.
logging.getLogger('cullinan').addHandler(logging.NullHandler())

# 导出配置接口
from cullinan.config import configure, get_config, CullinanConfig

# Export core module (foundational components)
from cullinan.core import (
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
    # Dependency Injection
    Inject,
    injectable,
    get_injection_registry,
    reset_injection_registry,
)

# Export enhanced service layer
from cullinan.service import (
    Service,
    ServiceRegistry,
    service,
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

# Export controller registry from controller package
from cullinan.controller import (
    ControllerRegistry,
    get_controller_registry,
    reset_controller_registry,
)

# Import controller utilities from controller.py file
# Note: After importing the controller package above, we need to access the original controller.py module
# It's been loaded but the name is shadowed. We can access it through parent imports in other modules.
# The utilities (HeaderRegistry, etc.) are defined in controller.py which is imported by application.py
# For now, we'll make them available by importing them when controller.py is loaded elsewhere

# Placeholder - these will be available when controller.py is imported
# They are exported from controller.py, not the controller package
def _get_controller_utils():
    """Lazy getter for controller utilities from controller.py module."""
    import sys
    # Try to find the actual controller.py module in sys.modules
    for key in sys.modules:
        if key.endswith('.controller') and hasattr(sys.modules[key], 'HeaderRegistry'):
            mod = sys.modules[key]
            if hasattr(mod, 'set_missing_header_handler'):
                return mod
    return None

# We'll document that these should be imported directly from controller.py when needed
# For backward compatibility, applications should use:
#   from cullinan import controller as controller_decorators
# or import controller.py functions directly in their code

__version__ = '0.7x'

__all__ = [
    # Configuration
    'configure',
    'get_config',
    'CullinanConfig',
    
    # Core module
    'Registry',
    'SimpleRegistry',
    'DependencyInjector',
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

    # Controller module
    'ControllerRegistry',
    'get_controller_registry',
    'reset_controller_registry',
]

