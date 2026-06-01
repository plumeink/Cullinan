import asyncio
import importlib
import json
import sys

import pytest

from cullinan import configure, get_asgi_app, get_config
from cullinan.application_model import Application
from cullinan.controller import reset_controller_registry
from cullinan.core import PendingRegistry, set_application_context
from cullinan.core.semantic_rules import reset_semantic_warnings
from cullinan.gateway import WebRuntime, reset_gateway
from cullinan.middleware import reset_middleware_registry


def _clear_example_modules(prefix: str):
    for name in list(sys.modules):
        if name == prefix or name.startswith(f"{prefix}."):
            sys.modules.pop(name, None)


def _load_root_module(module_path: str, root_name: str = "RootModule"):
    prefix = module_path.rsplit(".", 1)[0]
    _clear_example_modules(prefix)
    module = importlib.import_module(module_path)
    return getattr(module, root_name)


async def _invoke_asgi_app(app, path: str, method: str = "GET", body: bytes = b"", query_string: bytes = b""):
    messages = []
    delivered = False

    async def receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": query_string,
        "headers": [
            (b"host", b"example.test"),
            (b"content-type", b"application/json"),
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("example.test", 80),
    }

    await app(scope, receive, send)

    start = next(message for message in messages if message["type"] == "http.response.start")
    body_message = next(message for message in messages if message["type"] == "http.response.body")
    payload = json.loads(body_message["body"].decode("utf-8"))
    headers = {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in start.get("headers", [])
    }
    return start["status"], headers, payload


@pytest.fixture(autouse=True)
def _reset_runtime_state():
    cfg = get_config()
    original = cfg.to_dict()
    reset_semantic_warnings()
    PendingRegistry.reset()
    reset_controller_registry()
    reset_middleware_registry()
    WebRuntime.clear_active()
    reset_gateway()
    set_application_context(None)

    yield

    current = Application.current()
    if current is not None:
        current.uninstall()

    reset_semantic_warnings()
    PendingRegistry.reset()
    reset_controller_registry()
    reset_middleware_registry()
    WebRuntime.clear_active()
    reset_gateway()
    set_application_context(None)
    cfg.from_dict(original)


def test_minimal_app_example_serves_public_entrypoint():
    root_module = _load_root_module("examples.minimal_app.root")
    configure(root_module=root_module)
    app = get_asgi_app()

    status, _, payload = asyncio.run(_invoke_asgi_app(app, "/hello"))

    assert status == 200
    assert payload["entrypoint"] == "configure(root_module=...) + run()"


def test_controller_service_inject_example_uses_business_layers():
    root_module = _load_root_module("examples.controller_service_inject.root")
    configure(root_module=root_module)
    app = get_asgi_app()

    status, _, payload = asyncio.run(_invoke_asgi_app(app, "/users/2"))

    assert status == 200
    assert payload["name"] == "Linus"
    assert payload["role"] == "maintainer"


def test_middleware_and_module_example_marks_module_boundary():
    root_module = _load_root_module("examples.middleware_and_module.root")
    configure(root_module=root_module)
    app = get_asgi_app()

    status, headers, payload = asyncio.run(_invoke_asgi_app(app, "/inventory/summary"))

    assert status == 200
    assert payload["module_boundary"] == "examples.middleware_and_module"
    assert headers["x-cullinan-example"] == "middleware-and-module"
    assert headers["x-module-boundary"] == "examples.middleware_and_module"


def test_parameter_handling_example_maps_path_query_and_body():
    root_module = _load_root_module("examples.parameter_handling.root")
    configure(root_module=root_module)
    app = get_asgi_app()

    get_status, _, get_payload = asyncio.run(
        _invoke_asgi_app(
            app,
            "/catalog/items/7",
            query_string=b"include_meta=true&locale=zh-CN",
        )
    )
    post_status, _, post_payload = asyncio.run(
        _invoke_asgi_app(
            app,
            "/catalog/search",
            method="POST",
            body=json.dumps({"keyword": "cullinan", "page": 2, "limit": 5}).encode("utf-8"),
        )
    )

    assert get_status == 200
    assert get_payload["item_id"] == 7
    assert get_payload["include_meta"] is True
    assert get_payload["locale"] == "zh-CN"
    assert get_payload["meta"]["source"] == "parameter-system"

    assert post_status == 200
    assert post_payload["keyword"] == "cullinan"
    assert post_payload["page"] == 2
    assert post_payload["limit"] == 5


def test_testing_flow_example_stays_executable():
    _clear_example_modules("examples.testing_flow")
    module = importlib.import_module("examples.testing_flow.test_app")
    module.run_example_assertions()
