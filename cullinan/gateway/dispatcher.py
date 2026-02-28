# -*- coding: utf-8 -*-
"""Cullinan Dispatcher — The Single Entry Point for All HTTP Requests

Every HTTP request is funnelled through ``Dispatcher.dispatch()`` regardless
of the underlying server (Tornado / ASGI).

Lifecycle:
    1. Adapter converts native request → ``CullinanRequest``
    2. ``Dispatcher.dispatch(cullinan_request)`` is called
    3. Middleware pipeline runs (onion model)
    4. Router matches the request
    5. Parameter resolution (leveraging existing ``cullinan.params``)
    6. Controller method invocation (with DI)
    7. Response assembly → ``CullinanResponse``
    8. Adapter converts ``CullinanResponse`` → native response

Author: Plumeink
"""

import inspect
import json
import logging
from typing import Any, Callable, Dict, Optional, Tuple, Type

from .request import CullinanRequest
from .response import CullinanResponse
from .router import Router
from .pipeline import MiddlewarePipeline
from .exception_handler import ExceptionHandler
from .route_types import RouteMatch

logger = logging.getLogger(__name__)


class Dispatcher:
    """Central request dispatcher.

    Attributes:
        router: The route-matching engine.
        pipeline: The middleware pipeline.
        exception_handler: Global exception handler.
    """

    def __init__(
        self,
        router: Optional[Router] = None,
        pipeline: Optional[MiddlewarePipeline] = None,
        exception_handler: Optional[ExceptionHandler] = None,
        debug: bool = False,
    ) -> None:
        self.router: Router = router or Router()
        self.pipeline: MiddlewarePipeline = pipeline or MiddlewarePipeline()
        self.exception_handler: ExceptionHandler = exception_handler or ExceptionHandler(debug=debug)
        self._debug: bool = debug

    # ------------------------------------------------------------------
    # Main dispatch entry point
    # ------------------------------------------------------------------

    async def dispatch(self, request: CullinanRequest) -> CullinanResponse:
        """Dispatch a request through the full pipeline.

        This is THE single entry point that every adapter calls.

        Args:
            request: The unified request object.

        Returns:
            A ``CullinanResponse`` ready for the adapter to serialise.
        """
        try:
            return await self.pipeline.execute(request, self._core_dispatch)
        except Exception as exc:
            return await self.exception_handler.handle(request, exc)

    # ------------------------------------------------------------------
    # Core dispatch logic (called inside the pipeline)
    # ------------------------------------------------------------------

    async def _core_dispatch(self, request: CullinanRequest) -> CullinanResponse:
        """Route → resolve params → invoke controller → build response.

        This method sits at the centre of the onion; all middleware have
        already processed the request before it reaches here.
        """
        # 1. Route matching
        match: Optional[RouteMatch] = self.router.match(request.method, request.path)
        if match is None:
            # Try OPTIONS for CORS pre-flight (auto-allow if any route exists for this path)
            if request.method == 'OPTIONS':
                return CullinanResponse(status_code=204)
            return CullinanResponse.error(404, f'No route for {request.method} {request.path}')

        # 2. Inject path params into request
        request.path_params = match.path_params

        entry = match.entry
        handler = entry.handler

        if handler is None:
            return CullinanResponse.error(500, 'Route matched but no handler registered')

        # 3. Resolve parameters and invoke handler
        try:
            response = await self._invoke_handler(request, match)
        except Exception as exc:
            return await self.exception_handler.handle(request, exc)

        return response

    # ------------------------------------------------------------------
    # Handler invocation
    # ------------------------------------------------------------------

    async def _invoke_handler(
        self,
        request: CullinanRequest,
        match: RouteMatch,
    ) -> CullinanResponse:
        """Resolve parameters and call the matched handler.

        Supports:
        - Plain functions
        - Bound controller methods (via DI singleton lookup)
        - Both sync and async handlers
        - Return types: CullinanResponse, dict, str, None
        """
        entry = match.entry
        handler = entry.handler
        controller_cls = entry.controller_cls

        # Determine the actual callable and 'self' (if controller method)
        controller_instance = None
        if controller_cls is not None:
            controller_instance = self._get_controller_instance(controller_cls)

        # Build arguments from request + path params
        args, kwargs = await self._resolve_params(
            handler, request, match.path_params, controller_instance,
        )

        # Invoke
        if controller_instance is not None:
            result = handler(controller_instance, *args, **kwargs)
        else:
            result = handler(*args, **kwargs)

        if inspect.isawaitable(result):
            result = await result

        # Convert result → CullinanResponse
        return self._coerce_response(result)

    # ------------------------------------------------------------------
    # Parameter resolution
    # ------------------------------------------------------------------

    async def _resolve_params(
        self,
        handler: Callable,
        request: CullinanRequest,
        path_params: Dict[str, str],
        controller_instance: Optional[Any],
    ) -> Tuple[list, dict]:
        """Resolve function parameters from the request.

        Strategy:
        1. If the function uses the new ``cullinan.params`` annotation system
           (Path, Query, Body, Header, etc.), delegate to ``ParamResolver``.
        2. Otherwise, use a convention-based approach matching parameter names
           to known sources (``url_params``, ``query_params``, ``body_params``,
           ``headers``, ``request_body``, ``request``).

        Returns:
            (positional_args, keyword_args)
        """
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        # Skip 'self' for bound methods
        if params and params[0].name == 'self':
            params = params[1:]

        # Attempt new param system first
        try:
            from cullinan.params import ParamResolver, ResolveError, Param, DynamicBody
            analysis = ParamResolver.analyze_params(handler)
            use_new = any(
                cfg.get('param_spec') is not None
                or cfg.get('type') is DynamicBody
                or cfg.get('source') in ('path', 'query', 'body', 'header', 'file', 'auto')
                for cfg in analysis.values()
            )
            if use_new:
                return await self._resolve_new_params(
                    handler, request, path_params, analysis, params,
                )
        except Exception:
            pass

        # Convention-based fallback
        return await self._resolve_convention_params(
            request, path_params, params,
        )

    async def _resolve_new_params(
        self,
        handler: Callable,
        request: CullinanRequest,
        path_params: Dict[str, str],
        analysis: Dict[str, Dict],
        params: list,
    ) -> Tuple[list, dict]:
        """Resolve using ``cullinan.params.ParamResolver``."""
        from cullinan.params import ParamResolver

        # Build data sources from CullinanRequest
        query_dict = dict(request.query_params)
        body_dict: Dict[str, Any] = {}
        headers_dict: Dict[str, str] = dict(request.headers.items()) if request.headers else {}

        if request.body:
            try:
                body_dict = json.loads(request.body.decode('utf-8'))
                if not isinstance(body_dict, dict):
                    body_dict = {}
            except Exception:
                body_dict = {}

        resolved = ParamResolver.resolve(
            func=handler,
            request=request,  # CullinanRequest (has .body for RawBody support)
            url_params=path_params,
            query_params=query_dict,
            body_data=body_dict,
            headers=headers_dict,
            files={},
        )

        # Build ordered arg list
        sig = ParamResolver.get_signature(handler)
        args: list = []
        for name, p in sig.parameters.items():
            if name == 'self':
                continue
            args.append(resolved.get(name))

        return args, {}

    async def _resolve_convention_params(
        self,
        request: CullinanRequest,
        path_params: Dict[str, str],
        params: list,
    ) -> Tuple[list, dict]:
        """Convention-based parameter resolution.

        Maps parameter names to request data:
        - ``request`` / ``req``       → CullinanRequest
        - ``url_params``              → path_params dict
        - ``path_params``             → path_params dict
        - ``query_params``            → query_params dict
        - ``body_params``             → parsed body dict
        - ``headers``                 → headers dict
        - ``request_body``            → raw body bytes
        - ``body``                    → parsed body (JSON or form)
        - Any name matching a path param → that param's value
        - Otherwise                   → None
        """
        args: list = []
        body_cache: Any = None
        body_parsed = False

        for p in params:
            name = p.name

            if name in ('request', 'req'):
                args.append(request)
            elif name == 'url_params' or name == 'path_params':
                args.append(path_params)
            elif name == 'query_params':
                args.append(dict(request.query_params))
            elif name == 'body_params':
                if not body_parsed:
                    body_cache = await self._parse_body(request)
                    body_parsed = True
                args.append(body_cache)
            elif name == 'body':
                if not body_parsed:
                    body_cache = await self._parse_body(request)
                    body_parsed = True
                args.append(body_cache)
            elif name == 'headers':
                args.append(dict(request.headers.items()) if request.headers else {})
            elif name == 'request_body':
                args.append(request.body)
            elif name in path_params:
                args.append(path_params[name])
            else:
                # Try query param
                qv = request.query_params.get(name)
                if qv is not None:
                    args.append(qv)
                else:
                    args.append(None)

        return args, {}

    @staticmethod
    async def _parse_body(request: CullinanRequest) -> Any:
        """Parse body as JSON or form data."""
        if request.is_json:
            try:
                return await request.json()
            except Exception:
                return {}
        if request.is_form:
            return await request.form()
        if request.body:
            try:
                return json.loads(request.body.decode('utf-8'))
            except Exception:
                return {}
        return {}

    # ------------------------------------------------------------------
    # Controller instance resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _get_controller_instance(controller_cls: Type) -> Any:
        """Get the singleton controller instance from the IoC container."""
        try:
            from cullinan.controller.registry import get_controller_registry
            registry = get_controller_registry()
            instance = registry.get_instance(controller_cls.__name__)
            if instance is not None:
                return instance
        except Exception as exc:
            logger.debug('Could not get controller instance from registry: %s', exc)

        # Fallback: try ApplicationContext
        try:
            from cullinan.core import get_application_context
            ctx = get_application_context()
            if ctx is not None:
                return ctx.try_get(controller_cls.__name__)
        except Exception:
            pass

        # Last resort: create a fresh instance
        logger.warning('Creating ad-hoc controller instance for %s', controller_cls.__name__)
        return controller_cls()

    # ------------------------------------------------------------------
    # Response coercion
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce_response(result: Any) -> CullinanResponse:
        """Convert a handler return value into a ``CullinanResponse``.

        Accepted return types:
        - ``CullinanResponse``   → used directly
        - ``dict`` / ``list``    → JSON 200
        - ``str``                → text 200
        - ``bytes``              → binary 200
        - ``None``               → 204 No Content
        - Legacy ``HttpResponse``→ bridge
        - ``tuple``              → (body, status) or (body, status, headers)
        """
        if isinstance(result, CullinanResponse):
            return result

        if result is None:
            return CullinanResponse.no_content()

        if isinstance(result, tuple):
            return _coerce_tuple(result)

        if isinstance(result, (dict, list)):
            return CullinanResponse.json(result)

        if isinstance(result, str):
            return CullinanResponse.text(result)

        if isinstance(result, bytes):
            return CullinanResponse(body=result, content_type='application/octet-stream')

        # Legacy HttpResponse bridge
        if hasattr(result, 'get_status') and hasattr(result, 'get_body') and hasattr(result, 'get_headers'):
            resp = CullinanResponse(
                body=result.get_body(),
                status_code=result.get_status(),
            )
            for h in (result.get_headers() or []):
                if isinstance(h, (list, tuple)) and len(h) >= 2:
                    resp.add_header(str(h[0]), str(h[1]))
            return resp

        # Fallback: JSON-encode anything else
        return CullinanResponse.json(result)


def _coerce_tuple(t: tuple) -> CullinanResponse:
    """Handle tuple returns: (body,), (body, status), (body, status, headers)."""
    if len(t) == 1:
        return Dispatcher._coerce_response(t[0])
    if len(t) == 2:
        body, status = t
        resp = Dispatcher._coerce_response(body)
        resp.status_code = int(status)
        return resp
    if len(t) >= 3:
        body, status, headers = t[0], t[1], t[2]
        resp = Dispatcher._coerce_response(body)
        resp.status_code = int(status)
        if isinstance(headers, dict):
            for k, v in headers.items():
                resp.set_header(k, v)
        return resp
    return CullinanResponse.no_content()

