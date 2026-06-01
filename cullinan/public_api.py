# -*- coding: utf-8 -*-
"""Recommended high-level API for regular Cullinan applications."""

from __future__ import annotations

import os
from typing import Any, Optional

from cullinan._api_boundary import public_api_context
from cullinan.adapter import ASGIAdapter
from cullinan.application_model import Application
from cullinan.config import get_config
from cullinan.core.semantic_rules import CompatibilitySemanticWarning, warn_semantic_once

try:
    from cullinan.adapter import TornadoAdapter
except (ImportError, TypeError):
    TornadoAdapter = None  # type: ignore[assignment,misc]


def _resolve_root_module(root_module: Optional[type[Any]]) -> Optional[type[Any]]:
    return root_module or getattr(get_config(), "root_module", None)


def _resolve_engine(engine: Optional[str]) -> str:
    if engine:
        return engine
    env_engine = os.getenv("CULLINAN_ENGINE", "").strip().lower()
    if env_engine:
        return env_engine
    return getattr(get_config(), "server_engine", "tornado")


def _resolve_host_port(host: Optional[str], port: Optional[int]) -> tuple[str, int]:
    cfg = get_config()
    resolved_host = host or os.getenv("SERVER_HOST") or getattr(cfg, "server_host", "0.0.0.0")
    resolved_port = int(port or os.getenv("SERVER_PORT") or getattr(cfg, "server_port", 4080))
    return resolved_host, resolved_port


def _finalize_public_runtime() -> tuple[list, dict[str, Any]]:
    from cullinan.application import (
        _build_tornado_settings,
        _collect_global_headers,
        _finalize_runtime_setup,
    )

    _finalize_runtime_setup()
    return _collect_global_headers(), _build_tornado_settings()


def run(
    root_module: Optional[type[Any]] = None,
    *,
    engine: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    runtime_config: Optional[Any] = None,
    **adapter_kwargs: Any,
) -> Optional[Application]:
    """Run a regular Cullinan application through the recommended top-level API."""

    resolved_root_module = _resolve_root_module(root_module)
    if resolved_root_module is None:
        warn_semantic_once(
            key="public-api:run-fallback-compatibility",
            rule_key="compatibility-api",
            problem="cullinan.run() 在未声明 root_module 时会退回兼容扫描启动路径。",
            guidance="常规业务应用请使用 configure(root_module=RootModule) 或 run(RootModule) 走高层入口。",
            category=CompatibilitySemanticWarning,
            stacklevel=2,
        )
        from cullinan.application import run as compatibility_run

        handlers = adapter_kwargs.pop("handlers", None)
        if adapter_kwargs:
            raise TypeError(
                "兼容扫描启动路径只接受 handlers / engine 参数；"
                f"收到额外参数: {', '.join(sorted(adapter_kwargs))}"
            )
        compatibility_run(handlers=handlers, engine=engine)
        return None

    actual_engine = _resolve_engine(engine)
    resolved_host, resolved_port = _resolve_host_port(host, port)

    with public_api_context():
        app = Application.run(resolved_root_module, runtime_config=runtime_config)
        global_headers, tornado_settings = _finalize_public_runtime()
        if actual_engine == "asgi":
            adapter = ASGIAdapter(
                dispatcher=app.web_runtime.dispatcher,
                global_headers=global_headers,
                runtime=app.web_runtime,
            )
            adapter_kwargs.setdefault("server", getattr(get_config(), "asgi_server", "uvicorn"))
        else:
            if TornadoAdapter is None:
                raise ImportError("TornadoAdapter 不可用，请安装 tornado 或改用 engine='asgi'。")
            adapter = TornadoAdapter(
                dispatcher=app.web_runtime.dispatcher,
                settings=tornado_settings,
                global_headers=global_headers,
                runtime=app.web_runtime,
            )

        adapter.run(host=resolved_host, port=resolved_port, **adapter_kwargs)
        return app


def get_asgi_app(
    root_module: Optional[type[Any]] = None,
    *,
    runtime_config: Optional[Any] = None,
):
    """Create an ASGI app through the recommended top-level API."""

    resolved_root_module = _resolve_root_module(root_module)
    if resolved_root_module is None:
        warn_semantic_once(
            key="public-api:get-asgi-app-fallback-compatibility",
            rule_key="compatibility-api",
            problem="顶层 get_asgi_app() 在未声明 root_module 时会退回兼容扫描启动路径。",
            guidance="常规业务应用请使用 configure(root_module=RootModule) 或 get_asgi_app(RootModule)。",
            category=CompatibilitySemanticWarning,
            stacklevel=2,
        )
        from cullinan.application import get_asgi_app as compatibility_get_asgi_app

        return compatibility_get_asgi_app()

    with public_api_context():
        app = Application.run(resolved_root_module, runtime_config=runtime_config)
        global_headers, _ = _finalize_public_runtime()
        adapter = ASGIAdapter(
            dispatcher=app.web_runtime.dispatcher,
            global_headers=global_headers,
            runtime=app.web_runtime,
        )
        return adapter.create_app()
