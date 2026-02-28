# -*- coding: utf-8 -*-
"""Integration test for the v0.93 gateway layer.

Tests:
1. Router registration and matching
2. Dispatcher end-to-end dispatch (request → response)
3. Middleware pipeline execution
4. CullinanRequest / CullinanResponse construction
5. Exception handler
6. Response coercion (dict, str, tuple, None, legacy HttpResponse)
"""
import asyncio
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.gateway import (
    CullinanRequest, CullinanResponse, Router, Dispatcher,
    MiddlewarePipeline, GatewayMiddleware, ExceptionHandler,
    CORSMiddleware, RequestTimingMiddleware,
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
    print("Cullinan v0.93 Gateway Integration Test")
    print("=" * 60)

    # ====================================================================
    # 1. Router tests
    # ====================================================================
    print("\n--- 1. Router ---")
    router = Router()

    async def list_users(request):
        return CullinanResponse.json({"users": []})

    async def get_user(request):
        return CullinanResponse.json({"id": request.path_params.get("id")})

    async def create_user(request):
        return CullinanResponse.json({"created": True}, status_code=201)

    router.add_route('GET', '/api/users', handler=list_users)
    router.add_route('GET', '/api/users/{id}', handler=get_user)
    router.add_route('POST', '/api/users', handler=create_user)
    router.add_route('GET', '/health', handler=lambda r: CullinanResponse.text("OK"))

    check("Route count", router.route_count() == 4)

    m1 = router.match('GET', '/api/users')
    check("Static route match", m1 is not None and m1.entry.handler == list_users)

    m2 = router.match('GET', '/api/users/42')
    check("Param route match", m2 is not None and m2.path_params.get('id') == '42')

    m3 = router.match('POST', '/api/users')
    check("POST route match", m3 is not None and m3.entry.handler == create_user)

    m4 = router.match('DELETE', '/api/users')
    check("No match for DELETE", m4 is None)

    m5 = router.match('GET', '/nonexistent')
    check("No match for unknown path", m5 is None)

    # ====================================================================
    # 2. CullinanRequest tests
    # ====================================================================
    print("\n--- 2. CullinanRequest ---")
    req = CullinanRequest(
        method='POST',
        path='/api/users',
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer tok'},
        body=b'{"name": "Alice"}',
        query_string='page=1&size=10',
        client_ip='192.168.1.1',
    )
    check("Request method", req.method == 'POST')
    check("Request path", req.path == '/api/users')
    check("Case-insensitive headers", req.get_header('content-type') == 'application/json')
    check("Query params parsed", req.query_params.get('page') == '1')
    check("Query params size", req.query_params.get('size') == '10')
    check("is_json", req.is_json is True)
    json_body = await req.json()
    check("JSON body parse", json_body == {"name": "Alice"})
    check("Client IP", req.client_ip == '192.168.1.1')

    # ====================================================================
    # 3. CullinanResponse tests
    # ====================================================================
    print("\n--- 3. CullinanResponse ---")
    resp = CullinanResponse.json({"msg": "hello"}, status_code=200)
    check("JSON response status", resp.status_code == 200)
    check("JSON response content-type", resp.content_type == 'application/json')
    check("JSON response render", b'"msg": "hello"' in resp.render_body())

    resp2 = CullinanResponse.text("Hello World")
    check("Text response", resp2.render_body() == b'Hello World')

    resp3 = CullinanResponse.error(404, "Not Found", {"path": "/unknown"})
    check("Error response status", resp3.status_code == 404)

    resp4 = CullinanResponse.redirect("/new-location")
    check("Redirect status", resp4.status_code == 302)
    check("Redirect header", resp4.get_header('Location') == '/new-location')

    resp5 = CullinanResponse.no_content()
    check("No content status", resp5.status_code == 204)

    # Legacy compat
    check("Legacy get_status", resp.get_status() == 200)
    check("Legacy get_body", resp.get_body() == {"msg": "hello"})

    # Freeze
    resp.freeze()
    check("Frozen response", resp.is_frozen)
    try:
        resp.body = "modified"
        check("Frozen write rejected", False)
    except RuntimeError:
        check("Frozen write rejected", True)

    # ====================================================================
    # 4. Middleware Pipeline tests
    # ====================================================================
    print("\n--- 4. Middleware Pipeline ---")

    execution_log = []

    class LogMiddleware(GatewayMiddleware):
        async def __call__(self, request, call_next):
            execution_log.append('pre')
            resp = await call_next(request)
            execution_log.append('post')
            return resp

    class HeaderMiddleware(GatewayMiddleware):
        async def __call__(self, request, call_next):
            resp = await call_next(request)
            resp.set_header('X-Custom', 'test')
            return resp

    pipeline = MiddlewarePipeline()
    pipeline.add(LogMiddleware())
    pipeline.add(HeaderMiddleware())

    async def final_handler(request):
        execution_log.append('handler')
        return CullinanResponse.json({"ok": True})

    test_req = CullinanRequest(method='GET', path='/test')
    result = await pipeline.execute(test_req, final_handler)

    check("Pipeline execution order", execution_log == ['pre', 'handler', 'post'])
    check("Pipeline header injection", result.get_header('X-Custom') == 'test')
    check("Pipeline response body", result.get_body() == {"ok": True})

    # ====================================================================
    # 5. Dispatcher end-to-end
    # ====================================================================
    print("\n--- 5. Dispatcher ---")

    dispatcher = Dispatcher(router=router, debug=True)

    req_list = CullinanRequest(method='GET', path='/api/users')
    resp_list = await dispatcher.dispatch(req_list)
    check("Dispatch GET /api/users", resp_list.status_code == 200)

    req_get = CullinanRequest(method='GET', path='/api/users/99')
    resp_get = await dispatcher.dispatch(req_get)
    check("Dispatch GET /api/users/99", resp_get.status_code == 200)
    body = resp_get.get_body()
    check("Dispatch path param extracted", body.get("id") == "99" if isinstance(body, dict) else False)

    req_404 = CullinanRequest(method='GET', path='/nonexistent')
    resp_404 = await dispatcher.dispatch(req_404)
    check("Dispatch 404", resp_404.status_code == 404)

    # ====================================================================
    # 6. Exception Handler
    # ====================================================================
    print("\n--- 6. Exception Handler ---")

    exc_handler = ExceptionHandler(debug=True)

    @exc_handler.register(ValueError)
    def handle_value_error(request, exc):
        return CullinanResponse.error(400, str(exc))

    test_req2 = CullinanRequest(method='GET', path='/test')
    resp_ve = await exc_handler.handle(test_req2, ValueError("bad input"))
    check("Exception handler ValueError", resp_ve.status_code == 400)

    resp_500 = await exc_handler.handle(test_req2, RuntimeError("unknown"))
    check("Exception handler default 500", resp_500.status_code == 500)

    # ====================================================================
    # 7. Response coercion
    # ====================================================================
    print("\n--- 7. Response Coercion ---")
    check("Coerce dict", Dispatcher._coerce_response({"a": 1}).status_code == 200)
    check("Coerce str", Dispatcher._coerce_response("hello").render_body() == b'hello')
    check("Coerce None", Dispatcher._coerce_response(None).status_code == 204)
    check("Coerce tuple (body, status)", Dispatcher._coerce_response(({"a": 1}, 201)).status_code == 201)
    check("Coerce bytes", Dispatcher._coerce_response(b'\x00\x01').render_body() == b'\x00\x01')

    # Legacy HttpResponse bridge
    class FakeOldResponse:
        def get_status(self): return 200
        def get_body(self): return '{"legacy": true}'
        def get_headers(self): return [['X-Legacy', 'yes']]

    coerced = Dispatcher._coerce_response(FakeOldResponse())
    check("Coerce legacy HttpResponse", coerced.status_code == 200)
    check("Coerce legacy headers", coerced.get_header('X-Legacy') == 'yes')

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

