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
    StaticFiles,
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
    """Top-level facade that stays callable while exposing / delegating
    to the real ``cullinan.application`` submodule.

    This facade exists because ``cullinan/__init__.py`` needs to expose
    ``application`` both as a callable (the decorator) AND as a namespace
    that looks like the submodule.  Simple attribute-access delegation
    is enough for reads; for writes (``mock.patch``, ``setattr``, …) we
    must forward to the real module so that consumers that imported
    names *from* the real module see the change.
    """

    # ------------------------------------------------------------------
    # Recursion guard
    # ------------------------------------------------------------------
    # ``unittest.mock.patch('cullinan.application.…')`` resolves
    # ``cullinan.application`` through :func:`getattr` on the top-level
    # package, which returns *this* facade.  Asking the real module for
    # an attribute is normally idempotent, but some attribute lookups
    # (e.g. on partially‑initialised sub‑packages) can trigger imports
    # that walk back through the facade.  The set below breaks that cycle.
    # ------------------------------------------------------------------
    _accessing: set = set()

    def __call__(self, *args, **kwargs):
        return _application_decorator(*args, **kwargs)

    # -- read delegation ------------------------------------------------

    def __getattr__(self, name):
        if name in _ApplicationFacade._accessing:
            # We're already inside a getattr chain for this name — don't
            # re-enter.  Return a sentinel rather than raising
            # AttributeError, because mock.patch interprets
            # AttributeError as "attribute does not exist" and fails.
            return _RECURSION_SENTINEL
        _ApplicationFacade._accessing.add(name)
        try:
            return getattr(_application_module, name)
        finally:
            _ApplicationFacade._accessing.discard(name)

    # -- write / delete delegation -------------------------------------

    def __setattr__(self, name, value):
        # Internal bookkeeping stays on the facade instance.
        if name == "_accessing":
            object.__setattr__(self, name, value)
        else:
            setattr(_application_module, name, value)

    def __delattr__(self, name):
        if name == "_accessing":
            object.__delattr__(self, name)
        else:
            delattr(_application_module, name)


# Sentinel returned by _ApplicationFacade.__getattr__ when recursion is
# detected.  Using a sentinel instead of raising AttributeError prevents
# mock.patch from concluding the attribute doesn't exist.
_RECURSION_SENTINEL = object()


application = _ApplicationFacade()

__version__ = "0.93a13.post1"

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
    "StaticFiles",
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
