# -*- coding: utf-8 -*-

import asyncio

from cullinan.transport.adapter import ASGIAdapter, TornadoAdapter
from cullinan.web.gateway import (
    Dispatcher,
    HeaderPolicy,
    Router,
    WebRequest,
    WebResponse,
    WebHeaders,
    WebRuntime,
    WebRuntimeConfig,
    WebRuntimeState,
)


def test_web_headers_are_case_insensitive_and_multi_value():
    headers = WebHeaders([
        ("X-Test", "a"),
        ("x-test", "b"),
        ("Set-Cookie", "a=1"),
        ("Set-Cookie", "b=2"),
    ])

    assert headers.get("x-test") == "b"
    assert headers.get_all("X-Test") == ["a", "b"]
    assert headers.get_all("set-cookie") == ["a=1", "b=2"]


def test_response_freeze_blocks_mutation_and_emits_cookies():
    response = WebResponse.json({"ok": True})
    response.set_cookie("sid", "abc", http_only=True, secure=True)

    header_names = [name for name, _ in response.iter_headers(include_content_type=True)]
    assert "Content-Type" in header_names
    assert "Set-Cookie" in header_names

    response.freeze()

    try:
        response.set_header("X-After", "nope")
        raised = False
    except RuntimeError:
        raised = True

    assert raised is True


def test_dispatcher_applies_header_policy_and_return_value_handler():
    router = Router()
    router.add_route("GET", "/health", handler=lambda: {"status": "ok"})
    dispatcher = Dispatcher(
        router=router,
        header_policy=HeaderPolicy(
            default_security_headers={"X-Frame-Options": "DENY"},
            allow_origins="*",
        ),
    )

    request = WebRequest(method="GET", path="/health")
    response = asyncio.run(dispatcher.dispatch(request))

    assert response.status_code == 200
    assert response.get_header("X-Frame-Options") == "DENY"
    assert response.get_header("Access-Control-Allow-Origin") == "*"
    assert b'"status": "ok"' in response.render_body()


def test_runtime_switch_is_atomic_and_drains_previous_runtime():
    # Ensure no leftover _active_runtime from other tests.
    WebRuntime.clear_active()

    calls = []

    def warmup(runtime):
        calls.append(("warmup", id(runtime)))

    first = WebRuntime(config=WebRuntimeConfig(warmup_checks=(warmup,)))
    previous = WebRuntime.activate_runtime(first)

    assert previous is None
    assert first.state == WebRuntimeState.ACTIVE
    assert calls == [("warmup", id(first))]

    first.begin_request()

    second = WebRuntime(config=WebRuntimeConfig())
    previous = WebRuntime.activate_runtime(second)

    assert previous is first
    assert WebRuntime.current() is second
    assert first.state == WebRuntimeState.DRAINING
    assert second.state == WebRuntimeState.ACTIVE

    first.end_request()
    assert first.state == WebRuntimeState.CLOSED

    WebRuntime.clear_active()


def test_asgi_adapter_preserves_multi_headers_and_writes_cookies():
    adapter = ASGIAdapter(Dispatcher())
    request = asyncio.run(
        adapter.create_request_adapter().build_request(
            {
                "type": "http",
                "method": "GET",
                "path": "/items",
                "headers": [
                    (b"x-test", b"a"),
                    (b"x-test", b"b"),
                    (b"cookie", b"sid=abc; mode=dark"),
                ],
                "query_string": b"page=1",
                "client": ("127.0.0.1", 9000),
                "server": ("localhost", 8080),
                "scheme": "http",
            },
            b"",
        )
    )

    assert request.header_all("x-test") == ["a", "b"]
    assert request.cookie("sid") == "abc"

    response = WebResponse.text("ok")
    response.set_cookie("sid", "abc")
    events = []

    async def send(event):
        events.append(event)

    asyncio.run(adapter.create_response_writer().write_response(response, send))

    start_event = events[0]
    header_pairs = [(name.decode("latin-1"), value.decode("latin-1")) for name, value in start_event["headers"]]
    assert ("content-type", "text/plain; charset=utf-8") in [(k.lower(), v) for k, v in header_pairs]
    assert any(name.lower() == "set-cookie" and "sid=abc" in value for name, value in header_pairs)


def test_tornado_writer_preserves_duplicate_set_cookie_headers():
    writer = TornadoAdapter(Dispatcher()).create_response_writer()
    response = WebResponse.text("ok")
    response.set_cookie("a", "1")
    response.set_cookie("b", "2")

    class FakeHandler:
        def __init__(self):
            self._finished = False
            self.set_headers = []
            self.added_headers = []
            self.status_code = None
            self.body = b""

        def set_header(self, name, value):
            self.set_headers.append((name, value))

        def add_header(self, name, value):
            self.added_headers.append((name, value))

        def set_status(self, status):
            self.status_code = status

        def write(self, body):
            self.body += body

        def finish(self):
            self._finished = True

    handler = FakeHandler()
    writer.write_response(response, handler)

    assert handler.status_code == 200
    assert handler.body == b"ok"
    assert len([h for h in handler.added_headers if h[0].lower() == "set-cookie"]) == 2
