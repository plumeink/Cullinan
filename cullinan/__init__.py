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
    DependencyInjector,
    LifecycleManager,
    LifecycleState,
    LifecycleAware,
)

# Export enhanced service layer
from cullinan.service_new import (
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

__version__ = '0.8.0-alpha'

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
]

