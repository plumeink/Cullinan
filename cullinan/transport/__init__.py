# -*- coding: utf-8 -*-
"""Transport adapter facade for Cullinan."""

from cullinan.transport.adapter.base import WebAdapter

__all__ = ["ASGIAdapter", "TornadoAdapter", "WebAdapter"]


def __getattr__(name):
    if name == "ASGIAdapter":
        from cullinan.transport.adapter.asgi_adapter import ASGIAdapter

        return ASGIAdapter
    if name == "TornadoAdapter":
        try:
            from cullinan.transport.adapter.tornado_adapter import TornadoAdapter
        except ImportError:
            return None
        return TornadoAdapter
    if name == "WebAdapter":
        return WebAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
