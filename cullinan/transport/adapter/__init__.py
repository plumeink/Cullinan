# -*- coding: utf-8 -*-
"""Cullinan Adapter Module

Runtime adapter layer that bridges the transport-agnostic gateway
to concrete HTTP servers.

Supported adapters:
- ``TornadoAdapter`` — Tornado (single-handler mode)
- ``ASGIAdapter``    — ASGI 3.0 (uvicorn / hypercorn)

Author: Plumeink
"""

from .base import WebAdapter
from .driver import DriverCapabilities, DriverRequestAdapter, DriverResponseWriter, WebDriver
from .asgi_adapter import ASGIAdapter

# TornadoAdapter requires tornado — import conditionally
try:
    from .tornado_adapter import TornadoAdapter
except ImportError:
    TornadoAdapter = None  # type: ignore[assignment,misc]

__all__ = [
    'WebAdapter',
    'WebDriver',
    'DriverCapabilities',
    'DriverRequestAdapter',
    'DriverResponseWriter',
    'TornadoAdapter',
    'ASGIAdapter',
]
