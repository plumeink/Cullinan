# -*- coding: utf-8 -*-
"""Test actual request handling to diagnose the 200 response issue"""

import asyncio
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient
import logging
import socket

from cullinan.core import Inject, get_injection_registry, reset_injection_registry
from cullinan.service import service, Service, get_service_registry, reset_service_registry
from cullinan.controller import controller, get_api, post_api, get_controller_registry, reset_controller_registry
from cullinan.handler import get_handler_registry, reset_handler_registry

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    # Reset all registries
    reset_injection_registry()
    reset_service_registry()
    reset_controller_registry()
    reset_handler_registry()

    # Configure injection
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    # Define a service
    @service
    class TestService(Service):
        def get_data(self):
            return "Service Data"

    # Define a controller with method decorators
    @controller(url='/api/test')
    class TestController:
        test_service: TestService = Inject()

        @get_api(url='')
        def index(self):
            import json
            logger.info("===== INDEX METHOD CALLED =====")
            data = self.test_service.get_data()
            logger.info(f"Service returned: {data}")
            result = {"message": "Hello from index", "data": data}
            self.response.set_body(json.dumps(result))
            self.response.add_header("Content-Type", "application/json")

        @post_api(url='/create', body_params=['name', 'value'])
        def create(self, body_params):
            import json
            logger.info("===== CREATE METHOD CALLED =====")
            logger.info(f"Received body_params: {body_params}")
            result = {"created": True, "data": body_params}
            self.response.set_body(json.dumps(result))
            self.response.add_header("Content-Type", "application/json")

    # Check registrations
    controller_registry = get_controller_registry()
    handler_registry = get_handler_registry()

    logger.info("\n=== Registration Status ===")
    logger.info(f"Controller registered: {controller_registry.has('TestController')}")
    logger.info(f"Handler count: {handler_registry.count()}")

    handlers = handler_registry.get_handlers()
    logger.info(f"\nRegistered handlers:")
    for url, servlet in handlers:
        logger.info(f"  {url} -> {servlet}")
        # Check what methods the servlet has
        logger.info(f"    Methods: {[m for m in dir(servlet) if not m.startswith('_')]}")

    # Build Tornado application
    app = tornado.web.Application(handlers=handlers)
    server = tornado.httpserver.HTTPServer(app)

    # Find free port
    def _find_free_port():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        addr = s.getsockname()
        port = addr[1]
        s.close()
        return port

    port = _find_free_port()
    server.listen(port)

    ioloop = tornado.ioloop.IOLoop.current()

    async def do_requests():
        client = tornado.httpclient.AsyncHTTPClient()

        try:
            # Test GET request
            url = f'http://127.0.0.1:{port}/api/test'
            logger.info(f'\n===== Testing GET {url} =====')
            r1 = await client.fetch(url)
            logger.info(f'GET Response status: {r1.code}')
            logger.info(f'GET Response body: {r1.body.decode()}')

            # Test POST request
            url = f'http://127.0.0.1:{port}/api/test/create'
            logger.info(f'\n===== Testing POST {url} =====')
            import json
            body = json.dumps({'name': 'test', 'value': 123})
            r2 = await client.fetch(url, method='POST', body=body, headers={'Content-Type': 'application/json'})
            logger.info(f'POST Response status: {r2.code}')
            logger.info(f'POST Response body: {r2.body.decode()}')

        except Exception as e:
            logger.error(f'Request failed: {e}', exc_info=True)
        finally:
            ioloop.stop()

    # Schedule the async request
    ioloop.call_later(0.5, lambda: asyncio.ensure_future(do_requests()))

    logger.info(f'\n===== Starting server on port {port} =====')
    ioloop.start()
    logger.info('Server stopped')


if __name__ == '__main__':
    main()

