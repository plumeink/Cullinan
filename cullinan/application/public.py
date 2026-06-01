# -*- coding: utf-8 -*-
"""Recommended high-level API for regular Cullinan applications."""

from __future__ import annotations

import os
from typing import Any, Optional

from cullinan._api_boundary import public_api_context
from cullinan.application.legacy import _build_tornado_settings, _collect_global_headers, _finalize_runtime_setup
from cullinan.application.model import Application
from cullinan.support.config import get_config
from cullinan.transport import ASGIAdapter

try:
    from cullinan.transport.adapter import TornadoAdapter
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
        raise RuntimeError(
            "cullinan.run() 需要显式提供 root_module，或先调用 configure(root_module=RootModule)。"
        )

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
        raise RuntimeError(
            "cullinan.get_asgi_app() 需要显式提供 root_module，或先调用 configure(root_module=RootModule)。"
        )

    with public_api_context():
        app = Application.run(resolved_root_module, runtime_config=runtime_config)
        global_headers, _ = _finalize_public_runtime()
        adapter = ASGIAdapter(
            dispatcher=app.web_runtime.dispatcher,
            global_headers=global_headers,
            runtime=app.web_runtime,
        )
        return adapter.create_app()
