# -*- coding: utf-8 -*-
"""Unified registry for component definitions."""

from __future__ import annotations

import threading
import typing
from typing import Dict, Iterable, List, Optional

from cullinan.support.diagnostics import duplicate_definition

from .definitions import Definition
from .exceptions import RegistryFrozenError


class DefinitionRegistry:
    __slots__ = ("_definitions", "_lock", "_frozen")

    def __init__(self):
        self._definitions: Dict[str, Definition] = {}
        self._lock = threading.RLock()
        self._frozen = False

    def register(self, definition: Definition) -> None:
        with self._lock:
            self._ensure_mutable()
            if definition.name in self._definitions:
                raise ValueError(duplicate_definition(definition.name))
            self._definitions[definition.name] = definition

    def register_all(self, definitions: Iterable[Definition]) -> None:
        for definition in definitions:
            self.register(definition)

    def get(self, name: str) -> Optional[Definition]:
        return self._definitions.get(name)

    def has(self, name: str) -> bool:
        return name in self._definitions

    def list_names(self) -> List[str]:
        return list(self._definitions.keys())

    def values(self):
        return list(self._definitions.values())

    def items(self):
        return list(self._definitions.items())

    @property
    def count(self) -> int:
        return len(self._definitions)

    def freeze(self) -> None:
        with self._lock:
            self._frozen = True

    def unfreeze(self) -> None:
        with self._lock:
            self._frozen = False

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def clear(self) -> None:
        with self._lock:
            self._ensure_mutable()
            self._definitions.clear()

    def _ensure_mutable(self) -> None:
        if self._frozen:
            raise RegistryFrozenError()

    # ------------------------------------------------------------------
    #  Construct-injection type lookup
    # ------------------------------------------------------------------

    def find_by_type(self, type_hint) -> List[Definition]:
        """Return all definitions whose ``type_`` is a subtype of *type_hint*.

        Handles ``Optional[X]`` (and ``X | None`` on Python 3.10+) by
        unwrapping the inner type before matching.
        """
        target = _unwrap_optional(type_hint)
        if target is None or isinstance(target, str):
            return []
        result: List[Definition] = []
        for definition in self._definitions.values():
            dfn_type = definition.type_
            if dfn_type is not None and issubclass(dfn_type, target):
                result.append(definition)
        return result


def _unwrap_optional(tp):
    """If *tp* is ``Optional[X]``, return ``X``; otherwise return *tp* unchanged."""
    if tp is None:
        return None
    origin = typing.get_origin(tp)
    if origin is typing.Union:
        args = typing.get_args(tp)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return tp


__all__ = ["DefinitionRegistry"]
