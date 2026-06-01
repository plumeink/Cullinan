# -*- coding: utf-8 -*-

import importlib
import json
import os
import subprocess
import sys
import textwrap
import warnings
from pathlib import Path

import pytest

import cullinan
from cullinan import configure, get_config, get_asgi_app, run
from cullinan.application import Application
from cullinan.application import public as public_api
from cullinan.web.controller import reset_controller_registry
from cullinan.web.params import FileInfo
from cullinan.core import PendingRegistry, set_application_context
from cullinan.core.semantic_rules import reset_semantic_warnings
from cullinan.web.gateway import WebRuntime, reset_gateway


def _write_package(tmp_path: Path, package_name: str, files: dict[str, str]) -> str:
    root = tmp_path / package_name
    for relative_path, content in files.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return package_name


def _clear_modules(prefix: str) -> None:
    for module_name in list(sys.modules):
        if module_name == prefix or module_name.startswith(f"{prefix}."):
            sys.modules.pop(module_name, None)


@pytest.fixture(autouse=True)
def _reset_semantic_once_and_config():
    cfg = get_config()
    original = cfg.to_dict()
    reset_semantic_warnings()
    set_application_context(None)
    PendingRegistry.reset()
    WebRuntime.clear_active()
    reset_gateway()
    reset_controller_registry()
    yield
    reset_semantic_warnings()
    set_application_context(None)
    PendingRegistry.reset()
    WebRuntime.clear_active()
    reset_gateway()
    reset_controller_registry()
    cfg.from_dict(original)


def test_top_level_public_api_hides_advanced_runtime_symbols():
    public_exports = set(cullinan.__all__)

    assert "run" in public_exports
    assert "get_asgi_app" in public_exports
    assert "create_app" not in public_exports
    assert "current_app" not in public_exports
    assert "Application" not in public_exports
    assert "ApplicationContext" not in public_exports
    assert "TornadoAdapter" not in public_exports
    assert "reset_controller_registry" not in public_exports


def test_top_level_does_not_expose_advanced_runtime_symbols():
    module = importlib.reload(cullinan)
    with pytest.raises(AttributeError):
        getattr(module, "Application")
    with pytest.raises(AttributeError):
        getattr(module, "create_app")
    with pytest.raises(AttributeError):
        getattr(module, "current_app")


def test_web_fileinfo_keeps_backend_neutral_upload_factory():
    assert hasattr(FileInfo, "from_upload_payload")
    assert not hasattr(FileInfo, "from_tornado_file")


def test_top_level_import_does_not_eagerly_load_tornado(monkeypatch):
    output = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "import importlib, sys; importlib.import_module('cullinan'); "
            "print(any(name.startswith('tornado') for name in sys.modules))",
        ],
        text=True,
        cwd=os.getcwd(),
    ).strip()

    assert output == "False"


def test_application_import_does_not_eagerly_load_tornado(monkeypatch):
    output = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "import importlib, sys; importlib.import_module('cullinan.application'); "
            "print(any(name.startswith('tornado') for name in sys.modules))",
        ],
        text=True,
        cwd=os.getcwd(),
    ).strip()

    assert output == "False"


def test_direct_application_run_stays_explicit_runtime_api(tmp_path, monkeypatch):
    package_name = "boundary_application_run"
    _write_package(
        tmp_path,
        package_name,
        {
            "__init__.py": "",
            "root.py": """
                from cullinan import module

                @module
                class RootModule:
                    pass
            """,
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _clear_modules(package_name)

    root_module = importlib.import_module(f"{package_name}.root").RootModule
    app = Application.run(root_module)

    try:
        assert app.root_module is root_module
    finally:
        app.uninstall()
        _clear_modules(package_name)


def test_public_run_uses_configured_root_module_without_boundary_warning(tmp_path, monkeypatch):
    package_name = "boundary_public_run"
    _write_package(
        tmp_path,
        package_name,
        {
            "__init__.py": "",
            "root.py": """
                from cullinan import get_api, module, service, controller, Inject

                @service
                class GreetingService:
                    def greet(self):
                        return "hello"

                @controller(url="/api")
                class GreetingController:
                    greeting_service: GreetingService = Inject()

                    @get_api(url="/ping")
                    def ping(self):
                        return {"message": self.greeting_service.greet()}

                @module
                class RootModule:
                    pass
            """,
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _clear_modules(package_name)
    root_module = importlib.import_module(f"{package_name}.root").RootModule

    captured: dict[str, object] = {}

    class DummyTornadoAdapter:
        def __init__(self, dispatcher, settings=None, global_headers=None, runtime=None):
            captured["dispatcher"] = dispatcher
            captured["settings"] = settings
            captured["global_headers"] = global_headers
            captured["runtime"] = runtime

        def run(self, host="0.0.0.0", port=4080, **kwargs):
            captured["host"] = host
            captured["port"] = port
            captured["kwargs"] = kwargs

    monkeypatch.setattr(public_api, "_load_tornado_adapter", lambda: DummyTornadoAdapter)

    configure(
        root_module=root_module,
        server_engine="tornado",
        server_host="127.0.0.1",
        server_port=5091,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        app = run()

    try:
        assert app is not None
        assert app.root_module is root_module
        assert captured["host"] == "127.0.0.1"
        assert captured["port"] == 5091
        assert captured["settings"]["template_path"].endswith("templates")
        assert captured["settings"]["static_path"].endswith("static")
        assert isinstance(captured["global_headers"], list)
        assert not any(isinstance(item.message, PublicAPISemanticWarning) for item in caught)
    finally:
        if app is not None:
            app.uninstall()
        _clear_modules(package_name)


def test_public_run_prefers_neutral_auto_engine_resolution(tmp_path, monkeypatch):
    package_name = "boundary_public_run_auto"
    _write_package(
        tmp_path,
        package_name,
        {
            "__init__.py": "",
            "root.py": """
                from cullinan import controller, get_api, module

                @controller(url="/api")
                class GreetingController:
                    @get_api(url="/ping")
                    def ping(self):
                        return {"message": "hello"}

                @module
                class RootModule:
                    pass
            """,
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _clear_modules(package_name)
    root_module = importlib.import_module(f"{package_name}.root").RootModule

    captured: dict[str, object] = {}

    class DummyASGIAdapter:
        def __init__(self, dispatcher, global_headers=None, runtime=None):
            captured["dispatcher"] = dispatcher
            captured["global_headers"] = global_headers
            captured["runtime"] = runtime

        def run(self, host="0.0.0.0", port=4080, **kwargs):
            captured["host"] = host
            captured["port"] = port
            captured["kwargs"] = kwargs

    monkeypatch.setattr(public_api, "ASGIAdapter", DummyASGIAdapter)
    monkeypatch.setattr(public_api, "resolve_runtime_engine", lambda engine, asgi_server="uvicorn": "asgi")

    configure(
        root_module=root_module,
        server_host="127.0.0.1",
        server_port=5092,
        asgi_server="uvicorn",
    )
    app = run()

    try:
        assert app is not None
        assert app.root_module is root_module
        assert captured["host"] == "127.0.0.1"
        assert captured["port"] == 5092
        assert captured["kwargs"]["server"] == "uvicorn"
        assert isinstance(captured["global_headers"], list)
    finally:
        if app is not None:
            app.uninstall()
        _clear_modules(package_name)


def test_top_level_get_asgi_app_uses_configured_root_module(tmp_path, monkeypatch):
    package_name = "boundary_public_asgi"
    _write_package(
        tmp_path,
        package_name,
        {
            "__init__.py": "",
            "root.py": """
                from cullinan import get_api, module, controller

                @controller(url="/api")
                class GreetingController:
                    @get_api(url="/ping")
                    def ping(self):
                        return {"message": "hello"}

                @module
                class RootModule:
                    pass
            """,
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _clear_modules(package_name)
    root_module = importlib.import_module(f"{package_name}.root").RootModule
    configure(root_module=root_module)

    app = get_asgi_app()

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    sent = []

    async def send(message):
        sent.append(message)

    import asyncio

    try:
        asyncio.run(
            app(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/ping",
                    "headers": [],
                    "query_string": b"",
                    "client": ("127.0.0.1", 9000),
                    "server": ("localhost", 4080),
                    "scheme": "http",
                },
                receive,
                send,
            )
        )
        body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
        assert sent[0]["status"] == 200
        assert json.loads(body) == {"message": "hello"}
    finally:
        current_app = Application.current()
        if current_app is not None:
            current_app.uninstall()
        _clear_modules(package_name)


def test_top_level_get_asgi_app_finalizes_middleware_and_openapi(tmp_path, monkeypatch):
    package_name = "boundary_public_asgi_finalize"
    _write_package(
        tmp_path,
        package_name,
        {
            "__init__.py": "",
            "root.py": """
                from cullinan import Middleware, controller, get_api, middleware, module

                @middleware(priority=50)
                class AddExampleHeader(Middleware):
                    def process_response(self, request, response):
                        response.set_header("X-Boundary-Test", "ready")
                        return response

                @controller(url="/api")
                class GreetingController:
                    @get_api(url="/ping")
                    def ping(self):
                        return {"message": "hello"}

                @module
                class RootModule:
                    pass
            """,
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _clear_modules(package_name)
    root_module = importlib.import_module(f"{package_name}.root").RootModule
    configure(root_module=root_module)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def dispatch(path: str):
        sent = []

        async def send(message):
            sent.append(message)

        await app(
            {
                "type": "http",
                "method": "GET",
                "path": path,
                "headers": [],
                "query_string": b"",
                "client": ("127.0.0.1", 9000),
                "server": ("localhost", 4080),
                "scheme": "http",
            },
            receive,
            send,
        )
        return sent

    app = get_asgi_app()

    import asyncio

    try:
        ping_messages = asyncio.run(dispatch("/api/ping"))
        ping_body = b"".join(
            message.get("body", b"") for message in ping_messages if message["type"] == "http.response.body"
        )
        ping_headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in ping_messages[0].get("headers", [])
        }
        assert ping_messages[0]["status"] == 200
        assert json.loads(ping_body) == {"message": "hello"}
        assert ping_headers["x-boundary-test"] == "ready"

        openapi_messages = asyncio.run(dispatch("/openapi.json"))
        openapi_body = b"".join(
            message.get("body", b"") for message in openapi_messages if message["type"] == "http.response.body"
        )
        assert openapi_messages[0]["status"] == 200
        assert json.loads(openapi_body)["openapi"] == "3.0.3"
    finally:
        current_app = Application.current()
        if current_app is not None:
            current_app.uninstall()
        _clear_modules(package_name)
pytestmark = pytest.mark.filterwarnings(
    "ignore::cullinan.core.semantic_rules.PublicAPISemanticWarning"
)
