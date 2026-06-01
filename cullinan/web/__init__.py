# -*- coding: utf-8 -*-
"""Business-facing Web facade for Cullinan."""

from cullinan.web.controller import (
    Handler,
    get_api,
    get_missing_header_handler,
    patch_api,
    post_api,
    put_api,
    delete_api,
    response,
    set_missing_header_handler,
)
from cullinan.core import controller
from cullinan.web.gateway import WebRequest, WebResponse
from cullinan.web.middleware import BodyDecoderMiddleware, Middleware, get_decoded_body, middleware, set_decoded_body
from cullinan.web.params import (
    Auto,
    AutoType,
    Body,
    DynamicBody,
    File,
    Header,
    Param,
    ParamResolver,
    ParamValidator,
    Path,
    Query,
    ResolveError,
    TypeConverter,
    UNSET,
    ValidationError,
)
from cullinan.web.websocket_registry import websocket_handler

__all__ = [
    "Auto",
    "AutoType",
    "Body",
    "BodyDecoderMiddleware",
    "DynamicBody",
    "File",
    "Handler",
    "Header",
    "Middleware",
    "Param",
    "ParamResolver",
    "ParamValidator",
    "Path",
    "Query",
    "ResolveError",
    "TypeConverter",
    "UNSET",
    "ValidationError",
    "WebRequest",
    "WebResponse",
    "controller",
    "delete_api",
    "get_api",
    "get_decoded_body",
    "get_missing_header_handler",
    "middleware",
    "patch_api",
    "post_api",
    "put_api",
    "response",
    "set_decoded_body",
    "set_missing_header_handler",
    "websocket_handler",
]
