# -*- coding: utf-8 -*-
"""Internal helpers for public API boundary signaling."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator


_public_api_depth: ContextVar[int] = ContextVar("cullinan_public_api_depth", default=0)


@contextmanager
def public_api_context() -> Iterator[None]:
    token = _public_api_depth.set(_public_api_depth.get() + 1)
    try:
        yield
    finally:
        _public_api_depth.reset(token)


def in_public_api_context() -> bool:
    return _public_api_depth.get() > 0

