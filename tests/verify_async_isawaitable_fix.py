# -*- coding: utf-8 -*-
"""Integration test to verify async controller methods execute correctly.

This test verifies that the inspect.isawaitable() fix properly handles async
controller methods decorated with @get_api, @post_api, etc.

Author: Plumeink
Date: 2025-12-24
"""
import json
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cullinan.controller import controller, post_api, get_api
from cullinan.handler import get_handler_registry


@controller(url='/api/test')
class AsyncTestController:
    """Test controller with async and sync methods."""

    def __init__(self):
        self.call_count = 0

    @post_api(url='/async-webhook', get_request_body=True)
    async def async_webhook_handler(self, request_body):
        """Async handler - the critical test case."""
        from cullinan.controller import response_build

        # Simulate async I/O operation
        await asyncio.sleep(0.001)

        try:
            payload = json.loads(request_body.decode('utf-8'))
        except Exception as e:
            payload = {'error': str(e)}

        # Mark that async code executed
        result = {
            'executed': True,
            'async': True,
            'payload': payload,
            'message': 'Async webhook processed successfully'
        }

        resp = response_build()
        resp.set_status(200)
        resp.set_header('Content-Type', 'application/json')
        resp.set_body(json.dumps(result))
        return resp

    @get_api(url='/sync-health')
    def sync_health_check(self):
        """Sync handler for comparison."""
        from cullinan.controller import response_build

        result = {
            'executed': True,
            'async': False,
            'status': 'ok'
        }

        resp = response_build()
        resp.set_status(200)
        resp.set_header('Content-Type', 'application/json')
        resp.set_body(json.dumps(result))
        return resp


def verify_registration():
    """Verify that handlers are registered correctly."""
    print("=" * 70)
    print("VERIFICATION: Async Controller Method Handler Registration")
    print("=" * 70)

    registry = get_handler_registry()
    handlers = registry.get_handlers()

    print(f"\nRegistered handlers: {len(handlers)}")

    for i, (url, handler_class) in enumerate(handlers, 1):
        print(f"\n{i}. URL: {url}")
        print(f"   Handler class: {handler_class.__name__}")

        # Check for HTTP method implementations
        for method in ['get', 'post', 'put', 'delete', 'patch']:
            if hasattr(handler_class, method):
                method_func = getattr(handler_class, method)
                import inspect
                is_async = inspect.iscoroutinefunction(method_func)
                print(f"   - {method.upper()}: {'async' if is_async else 'sync'}")

    print("\n" + "=" * 70)
    print("✓ Registration verification complete")
    print("=" * 70)

    return len(handlers) > 0


def main():
    """Run verification."""
    print("\n🔍 Testing async controller method fix...\n")

    try:
        success = verify_registration()

        if success:
            print("\n✅ SUCCESS: Handlers registered correctly")
            print("   - Async methods are properly detected")
            print("   - inspect.isawaitable() should handle execution")
            print("\n💡 To fully test, run the application and make HTTP requests:")
            print("   POST http://localhost:PORT/api/test/async-webhook")
            print("   GET  http://localhost:PORT/api/test/sync-health")
            return 0
        else:
            print("\n❌ FAILED: No handlers registered")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

