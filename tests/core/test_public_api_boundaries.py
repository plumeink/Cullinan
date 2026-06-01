# -*- coding: utf-8 -*-

import importlib
import json
import sys
import textwrap
import warnings
from pathlib import Path

import pytest

import cullinan
import cullinan.public_api as public_api
from cullinan import configure, get_config, get_asgi_app, run
from cullinan.application_model import Application
from cullinan.controller import reset_controller_registry
from cullinan.core import PendingRegistry, set_application_context
from cullinan.core.semantic_rules import PublicAPISemanticWarning, reset_semantic_warnings
from cullinan.gateway import WebRuntime, reset_gateway


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
    assert "Application" not in public_exports
    assert "ApplicationContext" not in public_exports
    assert "TornadoAdapter" not in public_exports
    assert "reset_controller_registry" not in public_exports


def test_top_level_compat_import_warns_for_application():
    module = importlib.reload(cullinan)
    reset_semantic_warnings()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        application_cls = getattr(module, "Application")

    assert application_cls is Application
    assert any(isinstance(item.message, PublicAPISemanticWarning) for item in caught)
    assert any("configure, run" in str(item.message) for item in caught)


def test_direct_application_run_warns(tmp_path, monkeypatch):
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
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        app = Application.run(root_module)

    try:
        assert any(isinstance(item.message, PublicAPISemanticWarning) for item in caught)
        assert any("Application.run()" in str(item.message) for item in caught)
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
        def __init__(self, dispatcher, runtime):
            captured["dispatcher"] = dispatcher
            captured["runtime"] = runtime

        def run(self, host="0.0.0.0", port=4080, **kwargs):
            captured["host"] = host
            captured["port"] = port
            captured["kwargs"] = kwargs

    monkeypatch.setattr(public_api, "TornadoAdapter", DummyTornadoAdapter)

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
        assert not any(isinstance(item.message, PublicAPISemanticWarning) for item in caught)
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
