# -*- coding: utf-8 -*-
"""Cullinan Tornado Adapter — Single-Handler Mode

Instead of creating one dynamic ``type('Servlet'+url, ...)`` per route,
this adapter registers **one** catch-all ``RequestHandler`` that delegates
every request to ``Dispatcher.dispatch()``.

Author: Plumeink
"""

import logging
import os
import signal
from typing import Any, Dict, Optional

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from cullinan.gateway.dispatcher import Dispatcher
from cullinan.gateway.request import CullinanRequest
from cullinan.gateway.response import CullinanResponse
from .base import ServerAdapter

logger = logging.getLogger(__name__)


class _CullinanTornadoHandler(tornado.web.RequestHandler):
    """The **single** Tornado ``RequestHandler`` that funnels all requests
    through the Cullinan ``Dispatcher``.

    This replaces the old per-URL dynamic Servlet classes.
    """

    # Class-level defaults — Tornado calls set_default_headers() inside
    # __init__() (via clear()), which runs *before* initialize().
    # Without these defaults the first access would raise AttributeError.
    _dispatcher: Dispatcher = None  # type: ignore[assignment]
    _global_headers: list = []

    def initialize(self, dispatcher: Dispatcher, global_headers: list = None) -> None:  # type: ignore[override]
        self._dispatcher = dispatcher
        self._global_headers = global_headers or []

    # Accept every HTTP method
    async def _handle(self) -> None:
        """Unified entry point for all HTTP methods.

        Catches any error during request conversion, dispatch, or response
        writing and falls back to a plain 500 so that Tornado's default
        error page is never triggered unexpectedly.
        """
        try:
            request = self._build_cullinan_request()
            response = await self._dispatcher.dispatch(request)
            self._write_cullinan_response(response)
        except Exception:
            # If the response has not been started yet, write a generic 500.
            # If finish() was already called, silently swallow — the client
            # already received *some* response.
            if not self._finished:
                try:
                    self.set_status(500)
                    self.write(b'{"error":"Internal Server Error","status":500}')
                    self.finish()
                except Exception:
                    pass
            logger.exception('Uncaught error in _CullinanTornadoHandler._handle')

    # Map all standard methods to _handle
    async def get(self, *_args: Any, **_kwargs: Any) -> None:
        await self._handle()

    async def post(self, *_args: Any, **_kwargs: Any) -> None:
        await self._handle()

    async def put(self, *_args: Any, **_kwargs: Any) -> None:
        await self._handle()

    async def delete(self, *_args: Any, **_kwargs: Any) -> None:
        await self._handle()

    async def patch(self, *_args: Any, **_kwargs: Any) -> None:
        await self._handle()

    async def options(self, *_args: Any, **_kwargs: Any) -> None:
        await self._handle()

    async def head(self, *_args: Any, **_kwargs: Any) -> None:
        await self._handle()

    # ------------------------------------------------------------------
    # Request conversion
    # ------------------------------------------------------------------

    def _build_cullinan_request(self) -> CullinanRequest:
        """Convert the Tornado request into a ``CullinanRequest``."""
        tr = self.request  # tornado.httputil.HTTPServerRequest

        headers: Dict[str, str] = {}
        for name, value in tr.headers.get_all():
            headers[name] = value

        # Parse cookies
        cookies: Dict[str, str] = {}
        for k, morsel in self.cookies.items():
            cookies[k] = morsel.value

        scheme = tr.protocol or 'http'
        host = tr.host or 'localhost'
        port = 80
        if ':' in host:
            host_part, port_str = host.rsplit(':', 1)
            try:
                port = int(port_str)
                host = host_part
            except ValueError:
                pass

        query_string = ''
        if '?' in tr.uri:
            query_string = tr.uri.split('?', 1)[1]

        return CullinanRequest(
            method=tr.method,
            path=tr.path,
            headers=headers,
            body=tr.body or b'',
            query_string=query_string,
            client_ip=tr.remote_ip or '127.0.0.1',
            scheme=scheme,
            server_host=host,
            server_port=port,
            full_url=tr.full_url(),
            cookies=cookies,
        )

    # ------------------------------------------------------------------
    # Response conversion
    # ------------------------------------------------------------------

    def _write_cullinan_response(self, resp: CullinanResponse) -> None:
        """Write a ``CullinanResponse`` onto the Tornado response.

        Guards against double-finish and connection-close scenarios.
        """
        if self._finished:
            return

        # Global headers
        for h in self._global_headers:
            if isinstance(h, (list, tuple)) and len(h) >= 2:
                self.set_header(str(h[0]), str(h[1]))

        # Response headers
        for name, value in resp.headers:
            self.set_header(name, value)

        # Content-Type
        ct = resp.content_type
        if ct:
            self.set_header('Content-Type', ct)

        self.set_status(resp.status_code)

        body_bytes = resp.render_body()
        if body_bytes:
            self.write(body_bytes)

        if not self._finished:
            self.finish()

    def write_error(self, status_code: int = 500, **kwargs: Any) -> None:
        """Override Tornado's default HTML error page.

        Produces a JSON error body consistent with
        ``CullinanResponse.error()``.
        """
        reason = self._reason if hasattr(self, '_reason') else 'Server Error'
        payload = {'error': reason, 'status': status_code}

        exc_info = kwargs.get('exc_info')
        if exc_info:
            logger.error(
                'Handler error %s: %s',
                status_code,
                exc_info[1],
                exc_info=exc_info,
            )

        self.set_header('Content-Type', 'application/json')
        import json as _json
        self.finish(_json.dumps(payload, ensure_ascii=False))

    def on_connection_close(self) -> None:
        """Cleanup hook when the client drops the connection mid-request."""
        logger.debug('Client disconnected during request: %s %s',
                      self.request.method, self.request.uri)

    def set_default_headers(self) -> None:
        """Apply global headers from the legacy HeaderRegistry."""
        for h in getattr(self, '_global_headers', []):
            if isinstance(h, (list, tuple)) and len(h) >= 2:
                self.set_header(str(h[0]), str(h[1]))


class TornadoAdapter(ServerAdapter):
    """Tornado runtime adapter — single-handler mode.

    Creates a ``tornado.web.Application`` with one catch-all route that
    delegates to the ``Dispatcher``.  WebSocket routes are registered separately.

    Usage::

        adapter = TornadoAdapter(dispatcher)
        adapter.run(host='0.0.0.0', port=4080)
    """

    def __init__(
        self,
        dispatcher: Dispatcher,
        settings: Optional[Dict[str, Any]] = None,
        global_headers: Optional[list] = None,
        extra_handlers: Optional[list] = None,
    ) -> None:
        super().__init__(dispatcher)
        self._settings: Dict[str, Any] = settings or {}
        self._global_headers: list = global_headers or []
        self._extra_handlers: list = extra_handlers or []
        self._http_server: Optional[tornado.httpserver.HTTPServer] = None
        self._app: Optional[tornado.web.Application] = None

    def create_app(self) -> tornado.web.Application:
        """Create a ``tornado.web.Application`` with a catch-all handler."""
        handlers = list(self._extra_handlers)

        # Register WebSocket handlers (if any)
        try:
            from cullinan.websocket_registry import get_websocket_registry
            ws_registry = get_websocket_registry()
            for url, name in ws_registry.list_urls().items():
                ws_cls = ws_registry.get(name)
                if ws_cls is not None:
                    handlers.append((url, ws_cls))
                    logger.info('WebSocket route: %s -> %s', url, name)
        except Exception as exc:
            logger.debug('WebSocket registry not available: %s', exc)

        # The catch-all handler — MUST be last
        handlers.append(
            (r'.*', _CullinanTornadoHandler, {
                'dispatcher': self._dispatcher,
                'global_headers': self._global_headers,
            })
        )

        self._app = tornado.web.Application(handlers=handlers, **self._settings)
        return self._app

    def run(self, host: str = '0.0.0.0', port: int = 4080, **kwargs: Any) -> None:
        """Start the Tornado HTTP server (blocking)."""
        if self._app is None:
            self.create_app()

        server_thread = kwargs.get('threads') or os.getenv('SERVER_THREAD')
        self._http_server = tornado.httpserver.HTTPServer(self._app)

        if server_thread is not None:
            self._http_server.bind(port)
            self._http_server.start(int(server_thread))
            logger.info('Tornado server starting (multi-process: %s)', server_thread)
        else:
            self._http_server.listen(port, address=host)

        logger.info('Tornado server listening on %s:%s', host, port)

        # Signal handling
        self._install_signal_handlers()

        try:
            tornado.ioloop.IOLoop.current().start()
        except KeyboardInterrupt:
            logger.info('KeyboardInterrupt received, shutting down...')
        finally:
            self._cleanup()

    async def shutdown(self) -> None:
        """Gracefully stop the Tornado server."""
        if self._http_server:
            self._http_server.stop()
        try:
            loop = tornado.ioloop.IOLoop.current()
            loop.add_callback(loop.stop)
        except Exception:
            pass

    def _install_signal_handlers(self) -> None:
        try:
            def _handle(signum: int, frame: Any) -> None:
                logger.info('Signal %s received, stopping...', signum)
                try:
                    tornado.ioloop.IOLoop.current().add_callback(
                        tornado.ioloop.IOLoop.current().stop
                    )
                except Exception:
                    pass

            signal.signal(signal.SIGINT, _handle)
            try:
                signal.signal(signal.SIGTERM, _handle)
            except Exception:
                pass
        except Exception:
            pass

    def _cleanup(self) -> None:
        if self._http_server:
            try:
                self._http_server.stop()
            except Exception:
                pass

