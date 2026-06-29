# -*- coding: utf-8 -*-
"""Cullinan static files facade.

This package exposes a business-facing way to declare static assets and optional
SPA fallback routes. The runtime registers them through the gateway ``Router``
so the feature stays engine-neutral and is served identically under Tornado and
ASGI backends.

Public symbols
--------------

* :class:`StaticFiles` — declarative spec for a mount point.
* :func:`build_static_handler` — produces an async handler for advanced use.
* :func:`install_static_files` — registers a sequence of specs on a router.
"""

from cullinan.web.static.spec import StaticFiles
from cullinan.web.static.handler import build_static_handler
from cullinan.web.static.registry import install_static_files

__all__ = [
    "StaticFiles",
    "build_static_handler",
    "install_static_files",
]
