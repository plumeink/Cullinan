# -*- coding: utf-8 -*-
"""DI typing helpers."""

from __future__ import annotations

from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Provider(Generic[T]):
    """Typed provider wrapper for deferred dependency access."""

    __slots__ = ("_resolver",)

    def __init__(self, resolver: Callable[[], T]):
        self._resolver = resolver

    def get(self) -> T:
        return self._resolver()

    def __call__(self) -> T:
        return self.get()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(<resolver>)"


__all__ = ["Provider"]
