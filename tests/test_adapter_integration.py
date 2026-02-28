# -*- coding: utf-8 -*-
"""End-to-end test for TornadoAdapter and ASGIAdapter.

Tests the full request lifecycle:
  Native Request → Adapter → CullinanRequest → Dispatcher → CullinanResponse → Native Response
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.gateway import (
    CullinanRequest, CullinanResponse, Router, Dispatcher,
    MiddlewarePipeline, GatewayMiddleware,
)

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")


async def main():
    print("=" * 60)
    print("Cullinan v0.93 Adapter Integration Test")
    print("=" * 60)

    # ====================================================================
    # Build a Router + Dispatcher like the real framework would
    # ====================================================================
    router = Router()

    async def hello_handler(request):
        name = request.path_params.get('name', 'world')
        return CullinanResponse.json({"message": f"Hello, {name}!"})

    async def echo_body(request):
        data = await request.json() if request.body else {}
        return CullinanResponse.json({"echo": data}, status_code=200)

    async def query_test(request):
        return CullinanResponse.json({"params": dict(request.query_params)})

    async def error_handler(request):
        raise ValueError("intentional error")

    router.add_route('GET', '/hello', handler=hello_handler)
    router.add_route('GET', '/hello/{name}', handler=hello_handler)
    router.add_route('POST', '/echo', handler=echo_body)
    router.add_route('GET', '/query', handler=query_test)
    router.add_route('GET', '/error', handler=error_handler)

    # Add a timing middleware
    class TestMiddleware(GatewayMiddleware):
        async def __call__(self, request, call_next):
            resp = await call_next(request)
            resp.set_header('X-Test', 'middleware-works')
            return resp

    pipeline = MiddlewarePipeline()
    pipeline.add(TestMiddleware())

    dispatcher = Dispatcher(router=router, pipeline=pipeline, debug=True)

    # ====================================================================
    # 1. Test ASGI Adapter (simulated ASGI scope/receive/send)
    # ====================================================================
    print("\n--- 1. ASGI Adapter ---")

    from cullinan.adapter.asgi_adapter import (
        _build_request_from_scope, _send_response, _handle_http,
    )

    # Simulate GET /hello/Alice
    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/hello/Alice',
        'query_string': b'',
        'headers': [
            (b'host', b'localhost:8000'),
            (b'user-agent', b'test'),
        ],
        'server': ('localhost', 8000),
        'client': ('127.0.0.1', 54321),
        'scheme': 'http',
    }

    req_from_scope = _build_request_from_scope(scope, b'')
    check("ASGI request method", req_from_scope.method == 'GET')
    check("ASGI request path", req_from_scope.path == '/hello/Alice')
    check("ASGI request client_ip", req_from_scope.client_ip == '127.0.0.1')
    check("ASGI request headers", req_from_scope.get_header('host') == 'localhost:8000')

    # Dispatch through the real dispatcher
    resp = await dispatcher.dispatch(req_from_scope)
    check("ASGI dispatch status", resp.status_code == 200)
    body = resp.get_body()
    check("ASGI dispatch body", isinstance(body, dict) and body.get("message") == "Hello, Alice!")
    check("ASGI middleware header", resp.get_header('X-Test') == 'middleware-works')

    # Simulate POST /echo with JSON body
    scope_post = {
        'type': 'http',
        'method': 'POST',
        'path': '/echo',
        'query_string': b'',
        'headers': [
            (b'content-type', b'application/json'),
        ],
        'server': ('localhost', 8000),
        'client': ('127.0.0.1', 12345),
        'scheme': 'http',
    }
    post_body = json.dumps({"key": "value"}).encode('utf-8')
    req_post = _build_request_from_scope(scope_post, post_body)
    check("ASGI POST body", req_post.body == post_body)

    resp_post = await dispatcher.dispatch(req_post)
    check("ASGI POST status", resp_post.status_code == 200)
    resp_body = resp_post.get_body()
    check("ASGI POST echo", isinstance(resp_body, dict) and resp_body.get("echo") == {"key": "value"})

    # Simulate ASGI send
    sent_messages = []
    async def mock_send(msg):
        sent_messages.append(msg)

    await _send_response(mock_send, resp, [])
    check("ASGI send start", sent_messages[0]['type'] == 'http.response.start')
    check("ASGI send body", sent_messages[1]['type'] == 'http.response.body')
    check("ASGI send status code", sent_messages[0]['status'] == 200)

    # Simulate query params
    scope_query = {
        'type': 'http',
        'method': 'GET',
        'path': '/query',
        'query_string': b'page=2&size=20',
        'headers': [],
        'server': ('localhost', 8000),
        'client': ('127.0.0.1', 0),
        'scheme': 'http',
    }
    req_query = _build_request_from_scope(scope_query, b'')
    resp_query = await dispatcher.dispatch(req_query)
    qbody = resp_query.get_body()
    check("ASGI query params", qbody.get("params", {}).get("page") == "2")
    check("ASGI query params size", qbody.get("params", {}).get("size") == "20")

    # ====================================================================
    # 2. Test Tornado Adapter (request/response conversion)
    # ====================================================================
    print("\n--- 2. Tornado Adapter ---")

    try:
        from cullinan.adapter.tornado_adapter import TornadoAdapter, _CullinanTornadoHandler
        check("TornadoAdapter import", True)

        # Create adapter (don't run it, just verify creation)
        adapter = TornadoAdapter(dispatcher=dispatcher, settings={})
        app = adapter.create_app()
        check("TornadoAdapter create_app", app is not None)
        check("TornadoAdapter engine name", adapter.get_engine_name() == 'TornadoAdapter')
    except ImportError:
        print("  [SKIP] Tornado not installed")

    # ====================================================================
    # 3. Test error handling through dispatcher
    # ====================================================================
    print("\n--- 3. Error Handling ---")

    req_err = CullinanRequest(method='GET', path='/error')
    resp_err = await dispatcher.dispatch(req_err)
    check("Error handler status 400 (ValueError)", resp_err.status_code == 400)

    req_404 = CullinanRequest(method='GET', path='/does-not-exist')
    resp_404 = await dispatcher.dispatch(req_404)
    check("404 for unknown route", resp_404.status_code == 404)

    # ====================================================================
    # 4. Test ASGI app callable creation
    # ====================================================================
    print("\n--- 4. ASGI App Creation ---")
    from cullinan.adapter import ASGIAdapter
    asgi_adapter = ASGIAdapter(dispatcher=dispatcher)
    asgi_app = asgi_adapter.create_app()
    check("ASGI app is callable", callable(asgi_app))

    # Simulate a full ASGI request through the app
    received_response = []

    async def test_receive():
        return {'body': b'', 'more_body': False}

    async def test_send(msg):
        received_response.append(msg)

    test_scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/hello',
        'query_string': b'',
        'headers': [],
        'server': ('localhost', 8000),
        'client': ('127.0.0.1', 0),
        'scheme': 'http',
    }

    await asgi_app(test_scope, test_receive, test_send)
    check("Full ASGI cycle - start message", received_response[0]['type'] == 'http.response.start')
    check("Full ASGI cycle - status 200", received_response[0]['status'] == 200)
    check("Full ASGI cycle - body message", received_response[1]['type'] == 'http.response.body')
    body_bytes = received_response[1].get('body', b'')
    body_parsed = json.loads(body_bytes)
    check("Full ASGI cycle - body content", body_parsed.get('message') == 'Hello, world!')

    # ====================================================================
    # Summary
    # ====================================================================
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")
    return failed == 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

