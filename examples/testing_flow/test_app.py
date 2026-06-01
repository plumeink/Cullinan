import asyncio
import json

from cullinan.application import Application, get_asgi_app

from .app import configure_example


def _run_request(path: str):
    configure_example()
    app = get_asgi_app()
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [(b"host", b"example.test")],
        "client": ("127.0.0.1", 12345),
        "server": ("example.test", 80),
    }

    try:
        asyncio.run(app(scope, receive, send))
    finally:
        current = Application.current()
        if current is not None:
            current.uninstall()

    start = next(message for message in messages if message["type"] == "http.response.start")
    body = next(message for message in messages if message["type"] == "http.response.body")
    return start, json.loads(body["body"].decode("utf-8"))


def run_example_assertions():
    start, payload = _run_request("/notes/sample")
    assert start["status"] == 200
    assert payload["message"] == "Public API testing keeps examples stable."
    assert payload["tested_via"] == "get_asgi_app()"


def test_testing_flow_example():
    run_example_assertions()
