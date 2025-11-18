"""Middleware demo: runs a small Tornado app with DI and middleware-like request context.
Performs two requests and prints responses. Exits automatically.
"""
import asyncio
import logging
import socket
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient

from cullinan.handler.registry import get_handler_registry
from cullinan.core.injection import (get_injection_registry, Inject)
from cullinan.core.provider import ProviderRegistry, ScopedProvider
from cullinan.core.scope import get_request_scope
from cullinan.core.context import ContextManager
from cullinan.core.registry import Registry
from typing import cast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        import uuid
        self._id = uuid.uuid4().hex

    def greet(self):
        return f"Hello from UserService ({self._id[:6]})"


class RequestCounter:
    def __init__(self):
        self._n = 0

    def count(self):
        self._n += 1
        return self._n


class DIHandler(tornado.web.RequestHandler):
    user_service: 'UserService' = Inject()
    request_counter: 'RequestCounter' = Inject()

    def prepare(self):
        self._ctx = ContextManager()
        self._ctx.__enter__()
        logger.info('Entered request context')
        try:
            get_injection_registry().inject(self)
            logger.info('Injected dependencies into handler')
        except Exception as e:
            logger.error('Injection failed in prepare(): %s', e)

    def get(self):
        svc_greeting = self.user_service.greet()
        cnt = self.request_counter.count()
        self.write(f"{svc_greeting} | request_count={cnt}")

    def on_finish(self):
        try:
            self._ctx.__exit__(None, None, None)
            logger.info('Exited request context')
        except Exception:
            pass


def _find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    addr = s.getsockname()
    port = addr[1]
    s.close()
    return port


def main():
    provider_registry = ProviderRegistry()
    provider_registry.register_class('UserService', UserService, singleton=True)
    request_scope = get_request_scope()
    provider_registry.register_provider('RequestCounter', ScopedProvider(lambda: RequestCounter(), request_scope, 'RequestCounter'))

    inj_registry = get_injection_registry()
    inj_registry.add_provider_registry(cast(Registry, cast(object, provider_registry)), priority=10)

    handler_registry = get_handler_registry()
    handler_registry.register(r"/middleware", DIHandler)

    app = tornado.web.Application(handlers=handler_registry.get_handlers())
    server = tornado.httpserver.HTTPServer(app)
    port = _find_free_port()
    server.listen(port)

    ioloop = tornado.ioloop.IOLoop.current()

    async def do_requests():
        client = tornado.httpclient.AsyncHTTPClient()
        url = f'http://127.0.0.1:{port}/middleware'

        logger.info('Performing request 1')
        r1 = await client.fetch(url)
        logger.info('Response1: %s', r1.body.decode())

        await asyncio.sleep(0.15)

        logger.info('Performing request 2')
        r2 = await client.fetch(url)
        logger.info('Response2: %s', r2.body.decode())

        ioloop.stop()

    ioloop.call_later(0.3, lambda: asyncio.ensure_future(do_requests()))

    logger.info('Starting IOLoop for middleware demo')
    ioloop.start()
    logger.info('IOLoop stopped, exiting')


if __name__ == '__main__':
    main()

