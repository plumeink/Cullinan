# -*- coding: utf-8 -*-
"""Integration coverage for ASGI and Tornado adapters."""

import asyncio
import json

import pytest

from cullinan.adapter import ASGIAdapter, TornadoAdapter
from cullinan.adapter.asgi_adapter import _build_request_from_scope
from cullinan.adapter.tornado_adapter import _CullinanTornadoHandler
from cullinan.gateway import (
    Dispatcher,
    GatewayMiddleware,
    MiddlewarePipeline,
    Router,
    WebResponse,
)


def _build_dispatcher() -> Dispatcher:
    router = Router()

    async def hello_handler(request):
        name = request.path_params.get("name", "world")
        return WebResponse.json({"message": f"Hello, {name}!"})

    async def echo_handler(request):
        payload = await request.json() if request.body else {}
        return WebResponse.json({"echo": payload, "params": dict(request.query_params)})

    async def error_handler(_request):
        raise ValueError("intentional error")

    router.add_route("GET", "/hello", handler=hello_handler)
    router.add_route("GET", "/hello/{name}", handler=hello_handler)
    router.add_route("POST", "/echo", handler=echo_handler)
    router.add_route("GET", "/error", handler=error_handler)

    class TestMiddleware(GatewayMiddleware):
        async def __call__(self, request, call_next):
            response = await call_next(request)
            response.set_header("X-Test", "middleware-works")
            return response

    pipeline = MiddlewarePipeline()
    pipeline.add(TestMiddleware())
    return Dispatcher(router=router, pipeline=pipeline, debug=True)


async def _dispatch_asgi(app, scope, body: bytes = b"") -> list[dict]:
    sent = []
    messages = [{"type": "http.request", "body": body, "more_body": False}]

    async def receive():
        if messages:
            return messages.pop(0)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    return sent


def _json_body(events: list[dict]) -> dict:
    body = b"".join(
        event.get("body", b"")
        for event in events
        if event.get("type") == "http.response.body"
    )
    return json.loads(body)


def test_asgi_scope_conversion_preserves_headers_and_query_string():
    request = _build_request_from_scope(
        {
            "type": "http",
            "method": "GET",
            "path": "/hello/Alice",
            "query_string": b"page=2&size=20",
            "headers": [
                (b"host", b"localhost:8000"),
                (b"x-test", b"a"),
                (b"x-test", b"b"),
            ],
            "server": ("localhost", 8000),
            "client": ("127.0.0.1", 54321),
            "scheme": "http",
        },
        b"",
    )

    assert request.method == "GET"
    assert request.path == "/hello/Alice"
    assert request.client_ip == "127.0.0.1"
    assert request.get_header("host") == "localhost:8000"
    assert request.header_all("x-test") == ["a", "b"]
    assert request.query_params["page"] == "2"
    assert request.query_params["size"] == "20"


def test_asgi_adapter_full_cycle_handles_routing_middleware_and_json_body():
    adapter = ASGIAdapter(dispatcher=_build_dispatcher())
    app = adapter.create_app()

    events = asyncio.run(
        _dispatch_asgi(
            app,
            {
                "type": "http",
                "method": "POST",
                "path": "/echo",
                "query_string": b"source=test",
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"host", b"localhost:8000"),
                ],
                "server": ("localhost", 8000),
                "client": ("127.0.0.1", 54321),
                "scheme": "http",
            },
            json.dumps({"key": "value"}).encode("utf-8"),
        )
    )

    assert events[0]["type"] == "http.response.start"
    assert events[0]["status"] == 200
    response_headers = [
        (name.decode("latin-1"), value.decode("latin-1"))
        for name, value in events[0]["headers"]
    ]
    assert ("x-test", "middleware-works") in [(name.lower(), value) for name, value in response_headers]
    assert _json_body(events) == {"echo": {"key": "value"}, "params": {"source": "test"}}


def test_asgi_adapter_surfaces_dispatcher_errors_as_http_responses():
    adapter = ASGIAdapter(dispatcher=_build_dispatcher())
    app = adapter.create_app()

    events = asyncio.run(
        _dispatch_asgi(
            app,
            {
                "type": "http",
                "method": "GET",
                "path": "/error",
                "query_string": b"",
                "headers": [],
                "server": ("localhost", 8000),
                "client": ("127.0.0.1", 0),
                "scheme": "http",
            },
        )
    )

    assert events[0]["status"] == 400
    assert _json_body(events)["status"] == 400


def test_tornado_adapter_creates_catch_all_application():
    tornado = pytest.importorskip("tornado.web")
    adapter = TornadoAdapter(dispatcher=_build_dispatcher(), settings={})
    app = adapter.create_app()

    assert isinstance(app, tornado.Application)
    assert adapter.get_engine_name() == "TornadoAdapter"
    handler_rules = [
        rule.target
        for rule in app.wildcard_router.rules
        if getattr(rule, "target", None) is not None
    ]
    assert _CullinanTornadoHandler in handler_rules
