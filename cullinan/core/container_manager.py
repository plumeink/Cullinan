# -*- coding: utf-8 -*-
"""Global active root container manager."""

from __future__ import annotations

import threading
from typing import List, Optional

from .application_context import ApplicationContext


class ContainerManager:
    """Manages the single active root container per process."""

    __slots__ = ("_lock", "_active_root", "_building_root", "_draining_roots")

    def __init__(self):
        self._lock = threading.RLock()
        self._active_root: Optional[ApplicationContext] = None
        self._building_root: Optional[ApplicationContext] = None
        self._draining_roots: List[ApplicationContext] = []

    def get_active_root(self) -> Optional[ApplicationContext]:
        with self._lock:
            return self._active_root

    def bind(self, ctx: Optional[ApplicationContext]) -> None:
        with self._lock:
            self._active_root = ctx

    def clear(self) -> None:
        with self._lock:
            self._active_root = None
            self._building_root = None
            self._draining_roots.clear()

    def replace(
        self,
        candidate: ApplicationContext,
        *,
        refresh_if_needed: bool = True,
        shutdown_replaced: bool = True,
        shutdown_timeout: float = 30.0,
    ) -> Optional[ApplicationContext]:
        with self._lock:
            self._building_root = candidate

        if refresh_if_needed and not candidate.is_refreshed:
            candidate.refresh()

        with self._lock:
            previous = self._active_root
            self._active_root = candidate
            self._building_root = None
            if previous is not None and previous is not candidate:
                previous.begin_draining()
                self._draining_roots.append(previous)

        if previous is not None and previous is not candidate and shutdown_replaced:
            previous.shutdown(timeout=shutdown_timeout)
            with self._lock:
                self._draining_roots = [
                    root for root in self._draining_roots if root is not previous
                ]

        return previous

    @property
    def building_root(self) -> Optional[ApplicationContext]:
        with self._lock:
            return self._building_root

    @property
    def draining_roots(self) -> List[ApplicationContext]:
        with self._lock:
            return list(self._draining_roots)


_container_manager = ContainerManager()


def get_container_manager() -> ContainerManager:
    return _container_manager


__all__ = ["ContainerManager", "get_container_manager"]
