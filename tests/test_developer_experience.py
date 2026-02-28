# -*- coding: utf-8 -*-
"""Cullinan v0.93 â€?Developer Experience Test

Simulates the typical developer workflow with the new architecture:
1. Define a service with @service
2. Define a controller with @controller + route decorators
3. Build a Router manually (simulating what ApplicationContext does)
4. Dispatch requests through the full stack
5. Verify responses

This test does NOT start a real HTTP server â€?it exercises the entire
dispatch pipeline in-process.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.gateway import (
    CullinanRequest, CullinanResponse, Router, Dispatcher,
    MiddlewarePipeline, GatewayMiddleware, CORSMiddleware,
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


# ====================================================================
# Simulate a real application with services and controllers
# ====================================================================

class UserService:
    """A mock service (normally decorated with @service)."""
    def __init__(self):
        self._users = {
            "1": {"id": "1", "name": "Alice", "email": "alice@example.com"},
            "2": {"id": "2", "name": "Bob", "email": "bob@example.com"},
        }

    def list_users(self):
        return list(self._users.values())

    def get_user(self, user_id):
        return self._users.get(str(user_id))

    def create_user(self, data):
        uid = str(len(self._users) + 1)
        user = {"id": uid, **data}
        self._users[uid] = user
        return user


# Controller methods (normally defined in a @controller class)
user_service = UserService()


async def list_users_handler(request):
    """GET /api/users â€?list all users."""
    users = user_service.list_users()
    return CullinanResponse.json({"users": users, "count": len(users)})


async def get_user_handler(request):
    """GET /api/users/{id} â€?get a single user."""
    uid = request.path_params.get("id")
    user = user_service.get_user(uid)
    if user is None:
        return CullinanResponse.error(404, f"User {uid} not found")
    return CullinanResponse.json(user)


async def create_user_handler(request):
    """POST /api/users â€?create a new user."""
    body = await request.json()
    if not body or "name" not in body:
        return CullinanResponse.error(400, "Missing required field: name")
    user = user_service.create_user(body)
    return CullinanResponse.json(user, status_code=201)


async def health_handler(request):
    """GET /health â€?health check."""
    return {"status": "healthy", "version": "0.93"}


async def main():
    print("=" * 60)
    print("Cullinan v0.93 â€?Developer Experience Test")
    print("=" * 60)

    # ====================================================================
    # 1. Build the application
    # ====================================================================
    print("\n--- 1. Application Setup ---")

    router = Router()
    router.add_route("GET", "/api/users", handler=list_users_handler)
    router.add_route("GET", "/api/users/{id}", handler=get_user_handler)
    router.add_route("POST", "/api/users", handler=create_user_handler)
    router.add_route("GET", "/health", handler=health_handler)

    check("Routes registered", router.route_count() == 4)

    # Add CORS and custom middleware
    pipeline = MiddlewarePipeline()
    pipeline.add(CORSMiddleware(allow_origins="https://example.com"))

    class RequestIdMiddleware(GatewayMiddleware):
        _counter = 0
        async def __call__(self, request, call_next):
            RequestIdMiddleware._counter += 1
            resp = await call_next(request)
            resp.set_header("X-Request-Id", f"req-{RequestIdMiddleware._counter}")
            return resp

    pipeline.add(RequestIdMiddleware())

    dispatcher = Dispatcher(router=router, pipeline=pipeline, debug=True)
    check("Dispatcher created", dispatcher is not None)

    # ====================================================================
    # 2. GET /health
    # ====================================================================
    print("\n--- 2. GET /health ---")
    resp = await dispatcher.dispatch(CullinanRequest(method="GET", path="/health"))
    check("Health status 200", resp.status_code == 200)
    body = resp.get_body()
    check("Health body", body.get("status") == "healthy")
    check("CORS header", resp.get_header("Access-Control-Allow-Origin") == "https://example.com")
    check("Request-Id header", resp.get_header("X-Request-Id") is not None)

    # ====================================================================
    # 3. GET /api/users
    # ====================================================================
    print("\n--- 3. GET /api/users ---")
    resp = await dispatcher.dispatch(CullinanRequest(method="GET", path="/api/users"))
    check("List users status 200", resp.status_code == 200)
    body = resp.get_body()
    check("List users count", body.get("count") == 2)
    check("List users data", len(body.get("users", [])) == 2)

    # ====================================================================
    # 4. GET /api/users/1
    # ====================================================================
    print("\n--- 4. GET /api/users/1 ---")
    resp = await dispatcher.dispatch(CullinanRequest(method="GET", path="/api/users/1"))
    check("Get user status 200", resp.status_code == 200)
    body = resp.get_body()
    check("Get user name", body.get("name") == "Alice")
    check("Get user email", body.get("email") == "alice@example.com")

    # ====================================================================
    # 5. GET /api/users/999 (not found)
    # ====================================================================
    print("\n--- 5. GET /api/users/999 ---")
    resp = await dispatcher.dispatch(CullinanRequest(method="GET", path="/api/users/999"))
    check("User not found status 404", resp.status_code == 404)

    # ====================================================================
    # 6. POST /api/users (create)
    # ====================================================================
    print("\n--- 6. POST /api/users ---")
    import json
    resp = await dispatcher.dispatch(CullinanRequest(
        method="POST",
        path="/api/users",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"name": "Charlie", "email": "charlie@example.com"}).encode(),
    ))
    check("Create user status 201", resp.status_code == 201)
    body = resp.get_body()
    check("Create user name", body.get("name") == "Charlie")
    check("Create user has id", body.get("id") is not None)

    # ====================================================================
    # 7. POST /api/users (invalid - no name)
    # ====================================================================
    print("\n--- 7. POST /api/users (invalid) ---")
    resp = await dispatcher.dispatch(CullinanRequest(
        method="POST",
        path="/api/users",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"email": "noname@example.com"}).encode(),
    ))
    check("Invalid create status 400", resp.status_code == 400)

    # ====================================================================
    # 8. OPTIONS (CORS preflight)
    # ====================================================================
    print("\n--- 8. OPTIONS /api/users (CORS) ---")
    resp = await dispatcher.dispatch(CullinanRequest(method="OPTIONS", path="/api/users"))
    check("OPTIONS status 204", resp.status_code == 204)
    check("OPTIONS CORS origin", resp.get_header("Access-Control-Allow-Origin") == "https://example.com")

    # ====================================================================
    # 9. 404 on unknown route
    # ====================================================================
    print("\n--- 9. Unknown route ---")
    resp = await dispatcher.dispatch(CullinanRequest(method="GET", path="/nonexistent"))
    check("Unknown route 404", resp.status_code == 404)

    # ====================================================================
    # 10. Verify dict return auto-coercion
    # ====================================================================
    print("\n--- 10. Auto-coercion ---")
    # health_handler returns a plain dict â€?should auto-coerce to JSON 200
    resp = await dispatcher.dispatch(CullinanRequest(method="GET", path="/health"))
    check("Dict auto-coercion status", resp.status_code == 200)
    check("Dict auto-coercion body type", isinstance(resp.get_body(), dict))

    # ====================================================================
    # 11. Request-Id increments
    # ====================================================================
    print("\n--- 11. Middleware state ---")
    check("Request-Id incremented", resp.get_header("X-Request-Id") is not None)

    # ====================================================================
    # 12. Full ASGI simulation
    # ====================================================================
    print("\n--- 12. Full ASGI simulation ---")
    from cullinan.adapter.asgi_adapter import ASGIAdapter

    adapter = ASGIAdapter(dispatcher=dispatcher)
    app = adapter.create_app()

    sent = []
    async def receive():
        return {"body": b"", "more_body": False}
    async def send(msg):
        sent.append(msg)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/users",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
        "client": ("10.0.0.1", 0),
        "scheme": "http",
    }
    await app(scope, receive, send)
    check("ASGI start msg", sent[0]["type"] == "http.response.start")
    check("ASGI status 200", sent[0]["status"] == 200)
    body_parsed = json.loads(sent[1]["body"])
    check("ASGI body has users", "users" in body_parsed)

    # ====================================================================
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

