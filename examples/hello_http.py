"""Minimal Cullinan HTTP example (for docs/getting_started)

This script registers a simple Tornado handler with the Cullinan handler registry,
starts a short-lived HTTP server, performs a single request to verify the response,
and exits. It is intended for local verification in documentation and tests.
"""

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient
import asyncio
import logging

from cullinan.handler.registry import get_handler_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HelloHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Hello Cullinan')


def main():
    # Register handler in the Cullinan handler registry
    registry = get_handler_registry()
    registry.register(r"/hello", HelloHandler)

    # Build Tornado application from registered handlers
    handlers = registry.get_handlers()
    app = tornado.web.Application(handlers=handlers)
    server = tornado.httpserver.HTTPServer(app)
    port = 4080
    server.listen(port)

    ioloop = tornado.ioloop.IOLoop.current()

    async def do_request_and_stop_async():
        try:
            url = f'http://127.0.0.1:{port}/hello'
            logger.info('Async Requesting %s', url)
            client = tornado.httpclient.AsyncHTTPClient()
            resp = await client.fetch(url, request_timeout=10)
            body = resp.body.decode('utf-8') if resp.body else ''
            logger.info('Response status: %s', resp.code)
            logger.info('Response body: %s', body)
        except Exception as e:
            logger.error('Async Request failed: %s', e)
        finally:
            ioloop.stop()

    # Schedule the async request shortly after server starts
    ioloop.call_later(0.6, lambda: asyncio.ensure_future(do_request_and_stop_async()))

    logger.info('Starting IOLoop... (will stop after one verification request)')
    ioloop.start()
    logger.info('IOLoop stopped, exiting')


if __name__ == '__main__':
    main()
