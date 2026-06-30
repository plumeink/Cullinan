# -*- coding: utf-8 -*-

import asyncio
import importlib
import json
import sys
import textwrap
from pathlib import Path

import pytest

from cullinan.transport.adapter import ASGIAdapter
from cullinan.application import (
    Application,
    _collect_module_specs,
    _resolve_component_owners,
    bind_runtime_request_context,
    release_runtime_request_context,
)
from cullinan.web.controller import reset_controller_registry
from cullinan.core import PendingRegistry, set_application_context
from cullinan.web.gateway import WebRuntime, reset_gateway


@pytest.fixture(autouse=True)
def _reset_application_state():
    set_application_context(None)
    PendingRegistry.reset()
    WebRuntime.clear_active()
    reset_gateway()
    reset_controller_registry()
    yield
    set_application_context(None)
    PendingRegistry.reset()
    WebRuntime.clear_active()
    reset_gateway()
    reset_controller_registry()


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


def _import(module_name: str):
    importlib.invalidate_caches()
    return importlib.import_module(module_name)


def _dispatch_asgi(app, path: str) -> tuple[list[dict], bytes]:
    sent = []
    messages = [{"type": "http.request", "body": b"", "more_body": False}]

    async def receive():
        if messages:
            return messages.pop(0)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 9000),
        "server": ("localhost", 4080),
        "scheme": "http",
    }
    asyncio.run(app(scope, receive, send))
    body = b"".join(
        message.get("body", b"")
        for message in sent
        if message.get("type") == "http.response.body"
    )
    return sent, body


def test_application_run_discovers_root_module_and_binds_active_application(tmp_path, monkeypatch):
    package_name = "sample_app_model"
    _write_package(
        tmp_path,
        package_name,
        {
            "__init__.py": "",
            "root.py": """
                from cullinan import Inject, controller, get_api, module, service
                from cullinan.application import Application

                @service
                class GreetingService:
                    def greet(self):
                        return "hello"

                @controller(url="/api")
                class GreetingController:
                    greeting_service: GreetingService = Inject()

                    @get_api(url="/whoami")
                    def whoami(self):
                        app = Application.current()
                        return {
                            "root": app.root_module.__name__,
                        }

                @module
                class RootModule:
                    pass
            """,
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _clear_modules(package_name)

    root_pkg = _import(f"{package_name}.root")
    root_module = root_pkg.RootModule

    app = Application.run(root_module)
    try:
        assert Application.current() is app

        adapter = ASGIAdapter(dispatcher=app.web_runtime.dispatcher, runtime=app.web_runtime)
        sent, body = _dispatch_asgi(adapter.create_app(), "/api/whoami")

        assert sent[0]["status"] == 200
        assert json.loads(body) == {"root": "RootModule"}
    finally:
        app.uninstall()
        _clear_modules(package_name)


def test_module_conflict_requires_explicit_ownership_override(tmp_path, monkeypatch):
    package_name = "conflict_app_model"
    _write_package(
        tmp_path,
        package_name,
        {
            "__init__.py": "",
            "shared/__init__.py": "",
            "shared/components.py": """
                from cullinan import service

                @service
                class SharedService:
                    pass
            """,
            "alpha/__init__.py": "",
            "alpha/module.py": """
                from cullinan import module

                @module(packages=["conflict_app_model.shared"])
                class AlphaModule:
                    pass
            """,
            "beta/__init__.py": "",
            "beta/module.py": """
                from cullinan import module

                @module(packages=["conflict_app_model.shared"])
                class BetaModule:
                    pass
            """,
            "root.py": """
                from cullinan import module
                from cullinan.application import Application
                from conflict_app_model.alpha.module import AlphaModule
                from conflict_app_model.beta.module import BetaModule

                @module(imports=[AlphaModule, BetaModule])
                class RootModule:
                    pass
            """,
            "root_resolved.py": """
                from cullinan import module
                from cullinan.application import Application
                from conflict_app_model.alpha.module import AlphaModule
                from conflict_app_model.beta.module import BetaModule

                @module(
                    imports=[AlphaModule, BetaModule],
                    ownership_overrides={"conflict_app_model.shared": AlphaModule},
                )
                class RootResolvedModule:
                    pass
            """,
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _clear_modules(package_name)

    root_module = _import(f"{package_name}.root").RootModule
    with pytest.raises(RuntimeError, match="ownership_overrides"):
        Application.run(root_module)

    resolved_module_pkg = _import(f"{package_name}.root_resolved")
    app = Application.run(resolved_module_pkg.RootResolvedModule)
    try:
        shared_service = _import(f"{package_name}.shared.components").SharedService
        alpha_module = _import(f"{package_name}.alpha.module").AlphaModule
        assert app.get_component_owner(shared_service) is alpha_module
        svc = app.context.get("SharedService")
        assert isinstance(svc, shared_service)
        assert svc.__class__.__name__ == shared_service.__name__
    finally:
        app.uninstall()
        _clear_modules(package_name)


def test_component_outside_module_packages_gets_boundary_guidance(tmp_path, monkeypatch):
    package_name = "orphan_app_model"
    _write_package(
        tmp_path,
        package_name,
        {
            "__init__.py": "",
            "root_only/__init__.py": "",
            "feature/__init__.py": "",
            "feature/services.py": """
                from cullinan import service

                @service
                class OrphanService:
                    pass
            """,
            "root.py": """
                from cullinan import module
                from cullinan.application import Application
                import orphan_app_model.feature.services

                @module(packages=["orphan_app_model.root_only"])
                class RootModule:
                    pass
            """,
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _clear_modules(package_name)

    root_module = _import(f"{package_name}.root").RootModule
    with pytest.raises(RuntimeError) as error:
        _resolve_component_owners(
            _collect_module_specs(root_module),
            PendingRegistry.get_instance().get_all(),
        )

    message = str(error.value)
    assert "@module" in message
    assert "runtime ownership" in message
    assert "not explicit app registration" in message
    _clear_modules(package_name)


def test_current_app_prefers_request_snapshot_while_runtime_switches(tmp_path, monkeypatch):
    package_name = "switch_app_model"
    _write_package(
        tmp_path,
        package_name,
        {
            "__init__.py": "",
            "v1/__init__.py": """
                from cullinan import module, service

                @service
                class VersionService:
                    def value(self):
                        return "v1"

                @module
                class RootModuleV1:
                    pass
            """,
            "v2/__init__.py": """
                from cullinan import module, service

                @service
                class VersionService:
                    def value(self):
                        return "v2"

                @module
                class RootModuleV2:
                    pass
            """,
        },
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _clear_modules(package_name)

    v1_pkg = _import(f"{package_name}.v1")
    v2_pkg = _import(f"{package_name}.v2")

    app_v1 = Application.run(v1_pkg.RootModuleV1)
    app_v1.web_runtime.begin_request()
    binding = bind_runtime_request_context(app_v1.web_runtime)

    try:
        app_v2 = Application.run(v2_pkg.RootModuleV2)
        try:
            assert Application.current() is app_v1
            assert app_v2.context.get("VersionService").value() == "v2"
        finally:
            release_runtime_request_context(app_v1.web_runtime, binding)
            app_v1.web_runtime.end_request()
            assert Application.current() is app_v2
            assert app_v1.phase == "closed"
            app_v2.uninstall()
    finally:
        _clear_modules(package_name)
pytestmark = pytest.mark.filterwarnings(
    "ignore::cullinan.core.semantic_rules.PublicAPISemanticWarning"
)
