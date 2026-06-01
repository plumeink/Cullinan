# -*- coding: utf-8 -*-
"""Runtime backend selection helpers for transport adapters."""

from __future__ import annotations

import importlib.util


def _is_module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def is_runtime_engine_available(engine: str, *, asgi_server: str = "uvicorn") -> bool:
    normalized = (engine or "").strip().lower()
    if normalized == "asgi":
        return _is_module_available(asgi_server)
    if normalized == "tornado":
        return _is_module_available("tornado")
    return False


def get_available_runtime_engines(*, asgi_server: str = "uvicorn") -> list[str]:
    engines: list[str] = []
    if is_runtime_engine_available("asgi", asgi_server=asgi_server):
        engines.append("asgi")
    if is_runtime_engine_available("tornado", asgi_server=asgi_server):
        engines.append("tornado")
    return engines


def resolve_runtime_engine(engine: str | None, *, asgi_server: str = "uvicorn") -> str:
    normalized = (engine or "auto").strip().lower() or "auto"
    if normalized == "auto":
        available = get_available_runtime_engines(asgi_server=asgi_server)
        if available:
            return available[0]
        raise ImportError(
            "未发现可用 Web 后端。请安装 cullinan[asgi] 或 cullinan[tornado]，"
            "或显式配置可用的 server_engine。"
        )

    if normalized == "asgi":
        if not is_runtime_engine_available("asgi", asgi_server=asgi_server):
            raise ImportError(
                f"ASGI 后端不可用：未找到 {asgi_server}。"
                "请安装 cullinan[asgi] 或切换到 server_engine='tornado'。"
            )
        return "asgi"

    if normalized == "tornado":
        if not is_runtime_engine_available("tornado", asgi_server=asgi_server):
            raise ImportError(
                "Tornado 后端不可用。请安装 cullinan[tornado] 或切换到 server_engine='asgi'。"
            )
        return "tornado"

    raise ValueError(f"Unsupported runtime engine: {engine!r}. Use 'auto', 'asgi', or 'tornado'.")
