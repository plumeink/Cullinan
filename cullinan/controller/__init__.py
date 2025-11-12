# -*- coding: utf-8 -*-
"""Controller module for Cullinan framework.

Provides HTTP request controller management using the core Registry pattern.
This package re-exports both the new registry components and the existing
controller decorators and utilities from controller.py for backward compatibility.
"""

from .registry import ControllerRegistry, get_controller_registry, reset_controller_registry

# Re-export all public APIs from core module
from .core import (
    # Decorators
    controller,
    get_api,
    post_api,
    patch_api,
    delete_api,
    put_api,

    # Header utilities
    HeaderRegistry,
    get_header_registry,
    set_missing_header_handler,
    get_missing_header_handler,

    # Handler classes
    Handler,
    HttpResponse,
    StatusResponse,
    EncapsulationHandler,

    # Utility functions
    response_build,
    url_resolver,
    request_resolver,
    header_resolver,
    request_handler,
    emit_access_log,
    enable_response_pooling,
    disable_response_pooling,

    # Response proxy
    response,

    # Internal/testing functions
    _get_cached_signature,
    _get_cached_param_mapping,
)

# Response pooling functions (conditional import)
try:
    from .core import (
        ResponsePool,
        get_pooled_response,
        return_pooled_response,
        get_response_pool_stats,
    )
except ImportError:
    ResponsePool = None
    get_pooled_response = None
    return_pooled_response = None
    get_response_pool_stats = None


__all__ = [
    # Registry components
    'ControllerRegistry',
    'get_controller_registry',
    'reset_controller_registry',

    # Decorators
    'controller',
    'get_api',
    'post_api',
    'patch_api',
    'delete_api',
    'put_api',

    # Utilities
    'HeaderRegistry',
    'get_header_registry',
    'set_missing_header_handler',
    'get_missing_header_handler',

    # Handler classes
    'Handler',
    'HttpResponse',
    'StatusResponse',
    'EncapsulationHandler',

    # Utility functions
    'response_build',
    'url_resolver',
    'request_resolver',
    'header_resolver',
    'request_handler',
    'emit_access_log',
    'enable_response_pooling',
    'disable_response_pooling',

    # Response proxy
    'response',

    # Internal/testing functions (for backward compatibility)
    '_get_cached_signature',
    '_get_cached_param_mapping',
    'ResponsePool',
    'get_pooled_response',
    'return_pooled_response',
    'get_response_pool_stats',
]




