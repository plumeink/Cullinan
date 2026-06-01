# -*- coding: utf-8 -*-
"""Transport adapter facade for Cullinan."""

from cullinan.transport.adapter import ASGIAdapter, WebAdapter

try:
    from cullinan.transport.adapter import TornadoAdapter
except (ImportError, TypeError):
    TornadoAdapter = None  # type: ignore[assignment,misc]

__all__ = ["ASGIAdapter", "TornadoAdapter", "WebAdapter"]
