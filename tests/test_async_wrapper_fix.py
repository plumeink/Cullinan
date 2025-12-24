# -*- coding: utf-8 -*-
"""Regression test: verify async wrapper fix for "coroutine was never awaited" bug.

This test ensures that controller methods decorated with @post_api/@get_api
are properly awaited by the framework, preventing the RuntimeWarning and
ensuring the method actually executes.

作者：Plumeink
日期：2025-12-24
"""

import json
import tornado.testing
import tornado.web
from cullinan.controller import controller, post_api, get_api
from cullinan.service import service
from cullinan.core import Inject
from cullinan.handler import get_handler_registry


@service
class AsyncTestService:
    async def async_operation(self):
        """Simulate async operation"""
        return {'async': True, 'executed': True}


@controller(url='/api/async')
class AsyncController:
    test_service: AsyncTestService = Inject()

    @post_api(url='/test', get_request_body=True)
    async def async_post_handler(self, request_body):
        """Async handler that must be properly awaited"""
        from cullinan.controller import response_build

        # This async call must be awaited
        result = await self.test_service.async_operation()

        resp = response_build()
        resp.set_status(200)
        resp.set_header('Content-Type', 'application/json')
        resp.set_body(json.dumps(result))
        return resp

    @get_api(url='/sync')
    def sync_get_handler(self):
        """Sync handler for comparison"""
        from cullinan.controller import response_build
        resp = response_build()
        resp.set_status(200)
        resp.set_header('Content-Type', 'application/json')
        resp.set_body(json.dumps({'sync': True}))
        return resp


class TestAsyncWrapperFix(tornado.testing.AsyncHTTPTestCase):
    """Test that async controller methods are properly awaited"""

    def get_app(self):
        handlers = get_handler_registry().get_handlers()
        return tornado.web.Application(handlers)

    def test_async_post_handler_executes(self):
        """POST with async handler should execute and return result (not empty body)"""
        resp = self.fetch(
            '/api/async/test',
            method='POST',
            body='{}',
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(resp.code, 200, f"Expected 200, got {resp.code}")
        self.assertIsNotNone(resp.body, "Response body is None")
        self.assertNotEqual(resp.body, b'', "Response body is empty!")

        data = json.loads(resp.body)
        self.assertTrue(data.get('async'), "Async flag not set")
        self.assertTrue(data.get('executed'), "Handler did not execute")

        print(f"✅ Async POST handler properly executed: {data}")

    def test_sync_get_handler_still_works(self):
        """GET with sync handler should still work"""
        resp = self.fetch('/api/async/sync', method='GET')

        self.assertEqual(resp.code, 200)
        self.assertIsNotNone(resp.body)
        self.assertNotEqual(resp.body, b'')

        data = json.loads(resp.body)
        self.assertTrue(data.get('sync'))

        print(f"✅ Sync GET handler works: {data}")


if __name__ == '__main__':
    import unittest
    unittest.main()

