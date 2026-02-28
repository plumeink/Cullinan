# -*- coding: utf-8 -*-
"""Cullinan Middleware Pipeline

Implements the onion-model middleware pipeline that wraps the core
dispatch logic.  Every request flows through all middleware in order;
responses flow back in reverse order.

Author: Plumeink
"""

import logging
import time
from typing import Any, Callable, Awaitable, List, Optional, Type

from .request import CullinanRequest
from .response import CullinanResponse

logger = logging.getLogger(__name__)

# Type alias for the "next" callable in the pipeline
HandlerCallable = Callable[[CullinanRequest], Awaitable[CullinanResponse]]


class GatewayMiddleware:
    """Base class for gateway-level middleware (onion model).

    Subclasses override :meth:`__call__` and invoke ``await call_next(request)``
    to continue the chain.

    Example::

        class TimingMiddleware(GatewayMiddleware):
            async def __call__(self, request, call_next):
                start = time.time()
                response = await call_next(request)
                elapsed = time.time() - start
                response.set_header('X-Response-Time', f'{elapsed:.4f}s')
                return response
    """

    async def __call__(
        self,
        request: CullinanRequest,
        call_next: HandlerCallable,
    ) -> CullinanResponse:
        """Process the request.

        Default implementation simply forwards to the next handler.

        Args:
            request: The incoming request.
            call_next: Awaitable that invokes the next middleware or the final handler.

        Returns:
            The response from downstream.
        """
        return await call_next(request)


class MiddlewarePipeline:
    """Ordered middleware chain using the onion (wrap) model.

    Middleware are executed in registration order for the *request* phase
    and in reverse order for the *response* phase.

    Usage::

        pipeline = MiddlewarePipeline()
        pipeline.add(LoggingMiddleware())
        pipeline.add(AuthMiddleware())

        response = await pipeline.execute(request, final_handler)
    """

    def __init__(self) -> None:
        self._middleware: List[GatewayMiddleware] = []

    def add(self, mw: GatewayMiddleware) -> None:
        """Append a middleware to the pipeline."""
        self._middleware.append(mw)
        logger.debug('Middleware added: %s', mw.__class__.__name__)

    def add_class(self, mw_cls: Type[GatewayMiddleware], **kwargs: Any) -> GatewayMiddleware:
        """Instantiate and add a middleware class.  Returns the instance."""
        inst = mw_cls(**kwargs)
        self.add(inst)
        return inst

    async def execute(
        self,
        request: CullinanRequest,
        final_handler: HandlerCallable,
    ) -> CullinanResponse:
        """Run the full pipeline and return the final response.

        Args:
            request: The incoming request.
            final_handler: The core dispatch callable that produces the response
                           after all middleware have processed the request.

        Returns:
            The response (potentially modified by middleware).
        """
        # Build the chain from inside-out (last middleware wraps final_handler first)
        handler = final_handler
        for mw in reversed(self._middleware):
            handler = _wrap(mw, handler)
        return await handler(request)

    @property
    def count(self) -> int:
        return len(self._middleware)

    def clear(self) -> None:
        self._middleware.clear()


def _wrap(mw: GatewayMiddleware, next_handler: HandlerCallable) -> HandlerCallable:
    """Create a closure that calls ``mw(request, next_handler)``."""
    async def _inner(request: CullinanRequest) -> CullinanResponse:
        return await mw(request, next_handler)
    return _inner


# ======================================================================
# Built-in middleware implementations
# ======================================================================

class CORSMiddleware(GatewayMiddleware):
    """Cross-Origin Resource Sharing middleware.

    Handles preflight ``OPTIONS`` requests and injects CORS headers.

    Args:
        allow_origins: Allowed origins (``'*'`` for all).
        allow_methods: Allowed HTTP methods.
        allow_headers: Allowed request headers.
        allow_credentials: Whether to allow credentials.
        max_age: Preflight cache duration in seconds.
    """

    def __init__(
        self,
        allow_origins: str = '*',
        allow_methods: str = 'GET,POST,PUT,DELETE,PATCH,OPTIONS',
        allow_headers: str = '*',
        allow_credentials: bool = False,
        max_age: int = 86400,
    ) -> None:
        self._origins = allow_origins
        self._methods = allow_methods
        self._headers = allow_headers
        self._credentials = allow_credentials
        self._max_age = str(max_age)

    async def __call__(self, request: CullinanRequest, call_next: HandlerCallable) -> CullinanResponse:
        # Preflight
        if request.method == 'OPTIONS':
            resp = CullinanResponse(status_code=204)
            self._set_cors_headers(resp)
            return resp

        resp = await call_next(request)
        self._set_cors_headers(resp)
        return resp

    def _set_cors_headers(self, resp: CullinanResponse) -> None:
        resp.set_header('Access-Control-Allow-Origin', self._origins)
        resp.set_header('Access-Control-Allow-Methods', self._methods)
        resp.set_header('Access-Control-Allow-Headers', self._headers)
        resp.set_header('Access-Control-Max-Age', self._max_age)
        if self._credentials:
            resp.set_header('Access-Control-Allow-Credentials', 'true')


class RequestTimingMiddleware(GatewayMiddleware):
    """Adds an ``X-Response-Time`` header with the request duration."""

    async def __call__(self, request: CullinanRequest, call_next: HandlerCallable) -> CullinanResponse:
        start = time.perf_counter()
        resp = await call_next(request)
        elapsed = time.perf_counter() - start
        resp.set_header('X-Response-Time', f'{elapsed:.6f}s')
        return resp


class AccessLogMiddleware(GatewayMiddleware):
    """Emits an access-log entry for each request."""

    def __init__(self, log_name: str = 'cullinan.access') -> None:
        self._logger = logging.getLogger(log_name)

    async def __call__(self, request: CullinanRequest, call_next: HandlerCallable) -> CullinanResponse:
        start = time.perf_counter()
        resp: Optional[CullinanResponse] = None
        try:
            resp = await call_next(request)
            return resp
        finally:
            elapsed = time.perf_counter() - start
            status = resp.status_code if resp else 500
            self._logger.info(
                '%s - "%s %s" %s %.3fs',
                request.client_ip,
                request.method,
                request.path,
                status,
                elapsed,
            )


class LegacyMiddlewareBridge(GatewayMiddleware):
    """Bridge that adapts legacy ``cullinan.middleware.Middleware`` instances
    into the new gateway pipeline.

    This allows existing ``@middleware`` decorated classes to participate
    in the new pipeline without modification.
    """

    def __init__(self, legacy_chain: Any) -> None:
        """
        Args:
            legacy_chain: A ``MiddlewareChain`` instance from ``cullinan.middleware``.
        """
        self._chain = legacy_chain

    async def __call__(self, request: CullinanRequest, call_next: HandlerCallable) -> CullinanResponse:
        # Process request through legacy chain
        processed = self._chain.process_request(request)
        if processed is None:
            # Short-circuited by legacy middleware
            return CullinanResponse.error(403, 'Request rejected by middleware')

        resp = await call_next(request)

        # Process response through legacy chain (reverse)
        self._chain.process_response(request, resp)
        return resp

