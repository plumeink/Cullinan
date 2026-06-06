import logging

logging.getLogger("cullinan").addHandler(logging.NullHandler())

import cullinan.application as _application_module

from cullinan.application import (
    CullinanConfig,
    application as _application_decorator,
    configure,
    get_config,
    module,
)
from cullinan.core.decorators import Inject, InjectByName, Lazy, component, service
from cullinan.core.injection_types import Provider
from cullinan.web import (
    Auto,
    AutoType,
    Body,
    BodyDecoderMiddleware,
    DynamicBody,
    File,
    Header,
    Middleware,
    Param,
    ParamResolver,
    ParamValidator,
    Path,
    Query,
    ResolveError,
    TypeConverter,
    UNSET,
    ValidationError,
    WebRequest,
    WebResponse,
    controller,
    delete_api,
    get_api,
    get_decoded_body,
    get_missing_header_handler,
    middleware,
    patch_api,
    post_api,
    put_api,
    response,
    set_decoded_body,
    set_missing_header_handler,
    websocket_handler,
)


class _ApplicationFacade:
    """Top-level facade that stays callable while exposing application submodule members."""

    def __call__(self, *args, **kwargs):
        return _application_decorator(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(_application_module, name)


application = _ApplicationFacade()

__version__ = "0.93a11"

__all__ = [
    "Auto",
    "AutoType",
    "Body",
    "BodyDecoderMiddleware",
    "CullinanConfig",
    "DynamicBody",
    "File",
    "Header",
    "Inject",
    "InjectByName",
    "Lazy",
    "Middleware",
    "Param",
    "ParamResolver",
    "ParamValidator",
    "Path",
    "Provider",
    "Query",
    "ResolveError",
    "TypeConverter",
    "UNSET",
    "ValidationError",
    "WebRequest",
    "WebResponse",
    "application",
    "component",
    "configure",
    "controller",
    "delete_api",
    "get_api",
    "get_config",
    "get_decoded_body",
    "get_missing_header_handler",
    "middleware",
    "module",
    "patch_api",
    "post_api",
    "put_api",
    "response",
    "service",
    "set_decoded_body",
    "set_missing_header_handler",
    "websocket_handler",
]
