# -*- coding: utf-8 -*-
"""Cullinan Gateway Module

The gateway layer provides the transport-agnostic HTTP abstraction:
- CullinanRequest  – unified request object
- CullinanResponse – unified response object
- Router           – prefix-tree route matching
- Dispatcher       – single entry-point request dispatcher
- MiddlewarePipeline – onion-model middleware chain
- ExceptionHandler – global exception → response conversion

Author: Plumeink
"""

from .request import CullinanRequest
from .response import CullinanResponse
from .route_types import RouteEntry, RouteMatch, RouteGroup, HTTP_METHODS
from .router import Router
from .dispatcher import Dispatcher
from .pipeline import (
    MiddlewarePipeline,
    GatewayMiddleware,
    HandlerCallable,
    CORSMiddleware,
    RequestTimingMiddleware,
    AccessLogMiddleware,
    LegacyMiddlewareBridge,
)
from .exception_handler import ExceptionHandler
from .openapi import OpenAPIGenerator
from .globals import (
    get_router,
    get_dispatcher,
    get_pipeline,
    get_exception_handler,
    reset_gateway,
)

__all__ = [
    # Request / Response
    'CullinanRequest',
    'CullinanResponse',
    # Routing
    'Router',
    'RouteEntry',
    'RouteMatch',
    'RouteGroup',
    'HTTP_METHODS',
    # Dispatch
    'Dispatcher',
    # Pipeline
    'MiddlewarePipeline',
    'GatewayMiddleware',
    'HandlerCallable',
    'CORSMiddleware',
    'RequestTimingMiddleware',
    'AccessLogMiddleware',
    'LegacyMiddlewareBridge',
    # Exception handling
    'ExceptionHandler',
    # OpenAPI
    'OpenAPIGenerator',
    # Global accessors
    'get_router',
    'get_dispatcher',
    'get_pipeline',
    'get_exception_handler',
    'reset_gateway',
]

