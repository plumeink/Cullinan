# -*- coding: utf-8 -*-
"""Quick verification test for async handler fix.

Author: Plumeink
"""
import json
import asyncio
import tornado.testing
import tornado.web
from cullinan.controller import controller, post_api, get_api
from cullinan.handler import get_handler_registry


@controller(url='/api')
class TestAsyncController:
    """Test controller with async methods"""

    @post_api(url='/webhook', get_request_body=True)
    async def handle_webhook(self, request_body):
        """Async webhook handler - should execute and return response"""
        from cullinan.controller import response_build

        # Simulate async work
        await asyncio.sleep(0.01)

        try:
            payload = json.loads(request_body.decode('utf-8'))
        except Exception as e:
            payload = {'error': str(e)}

        result = {
            'processed': True,
            'payload': payload,
            'message': 'Webhook processed successfully'
        }

        resp = response_build()
        resp.set_status(200)
        resp.set_header('Content-Type', 'application/json')
        resp.set_body(json.dumps(result))
        return resp

    @get_api(url='/health')
    def health_check(self):
        """Sync method for comparison"""
        from cullinan.controller import response_build
        resp = response_build()
        resp.set_status(200)
        resp.set_header('Content-Type', 'application/json')
        resp.set_body(json.dumps({'status': 'ok'}))
        return resp


class TestAsyncFix(tornado.testing.AsyncHTTPTestCase):
    """Test async controller fix"""

    def get_app(self):
        handlers = get_handler_registry().get_handlers()
        return tornado.web.Application(handlers)

    def test_async_post_handler(self):
        """Test that async POST handler executes and returns data"""
        response = self.fetch(
            '/api/webhook',
            method='POST',
            body=json.dumps({'test': 'data'}),
            headers={'Content-Type': 'application/json'}
        )

        print(f"Status: {response.code}")
        print(f"Body: {response.body}")

        self.assertEqual(response.code, 200)
        self.assertIsNotNone(response.body)
        self.assertNotEqual(response.body, b'')

        data = json.loads(response.body)
        self.assertTrue(data.get('processed'))
        print(f"SUCCESS: Async handler executed correctly: {data}")

    def test_sync_get_handler(self):
        """Test that sync GET handler still works"""
        response = self.fetch('/api/health')

        print(f"Status: {response.code}")
        print(f"Body: {response.body}")

        self.assertEqual(response.code, 200)
        data = json.loads(response.body)
        self.assertEqual(data.get('status'), 'ok')
        print(f"SUCCESS: Sync handler works: {data}")


if __name__ == '__main__':
    import unittest
    unittest.main()

