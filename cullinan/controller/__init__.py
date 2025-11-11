# -*- coding: utf-8 -*-
"""Controller module for Cullinan framework.

Provides HTTP request controller management using the core Registry pattern.
This package re-exports both the new registry components and the existing
controller decorators and utilities from controller.py for backward compatibility.
"""

from .registry import ControllerRegistry, get_controller_registry, reset_controller_registry

# Re-export all public APIs from controller.py module
# We need to import from parent directory to avoid circular imports
import sys
import os

# Add parent directory to path temporarily to import controller.py
_parent_path = os.path.dirname(os.path.dirname(__file__))
if _parent_path not in sys.path:
    sys.path.insert(0, _parent_path)

try:
    # Import controller.py as a separate module
    import importlib.util
    _controller_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'controller.py')

    if os.path.exists(_controller_py_path):
        _spec = importlib.util.spec_from_file_location("cullinan._controller_impl", _controller_py_path)
        if _spec and _spec.loader:
            _ctrl_impl = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_ctrl_impl)

            # Re-export decorators
            controller = _ctrl_impl.controller
            get_api = _ctrl_impl.get_api
            post_api = _ctrl_impl.post_api
            patch_api = _ctrl_impl.patch_api
            delete_api = _ctrl_impl.delete_api
            put_api = _ctrl_impl.put_api

            # Re-export utilities
            HeaderRegistry = _ctrl_impl.HeaderRegistry
            get_header_registry = _ctrl_impl.get_header_registry
            set_missing_header_handler = _ctrl_impl.set_missing_header_handler
            get_missing_header_handler = _ctrl_impl.get_missing_header_handler

            # Re-export handler classes
            Handler = _ctrl_impl.Handler
            HttpResponse = _ctrl_impl.HttpResponse
            StatusResponse = _ctrl_impl.StatusResponse
            EncapsulationHandler = _ctrl_impl.EncapsulationHandler

            # Utility functions
            response_build = _ctrl_impl.response_build
            url_resolver = _ctrl_impl.url_resolver
            request_resolver = _ctrl_impl.request_resolver
            header_resolver = _ctrl_impl.header_resolver
            request_handler = _ctrl_impl.request_handler
            emit_access_log = _ctrl_impl.emit_access_log
            enable_response_pooling = _ctrl_impl.enable_response_pooling
            disable_response_pooling = _ctrl_impl.disable_response_pooling

            # Re-export response proxy
            response = _ctrl_impl.response

            # Internal/testing functions
            _get_cached_signature = _ctrl_impl._get_cached_signature
            _get_cached_param_mapping = _ctrl_impl._get_cached_param_mapping

            # Response pooling functions (if they exist)
            ResponsePool = getattr(_ctrl_impl, 'ResponsePool', None)
            get_pooled_response = getattr(_ctrl_impl, 'get_pooled_response', None)
            return_pooled_response = getattr(_ctrl_impl, 'return_pooled_response', None)
            get_response_pool_stats = getattr(_ctrl_impl, 'get_response_pool_stats', None)

        else:
            raise ImportError("Could not load controller.py spec")
    else:
        raise ImportError(f"controller.py not found at {_controller_py_path}")

except Exception as e:
    import logging
    logging.warning(f"Could not re-export controller.py functions: {e}")
    # Define placeholders
    controller = None
    get_api = None
    post_api = None
    patch_api = None
    delete_api = None
    put_api = None
    HeaderRegistry = None
    get_header_registry = None
    set_missing_header_handler = None
    get_missing_header_handler = None
    Handler = None
    HttpResponse = None
    StatusResponse = None
    EncapsulationHandler = None
    response_build = None
    url_resolver = None
    request_resolver = None
    header_resolver = None
    request_handler = None
    emit_access_log = None
    enable_response_pooling = None
    disable_response_pooling = None
    response = None
    _get_cached_signature = None
    _get_cached_param_mapping = None
    ResponsePool = None
    get_pooled_response = None
    return_pooled_response = None
    get_response_pool_stats = None

finally:
    # Clean up path
    if _parent_path in sys.path:
        sys.path.remove(_parent_path)

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




