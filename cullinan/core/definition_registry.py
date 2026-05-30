# -*- coding: utf-8 -*-
"""统一的组件定义注册表。"""

from __future__ import annotations

import threading
from typing import Dict, Iterable, List, Optional

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
                raise ValueError(f"Definition '{definition.name}' 已存在，禁止重复注册")
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
            raise RegistryFrozenError("Registry 已冻结，禁止修改")


__all__ = ["DefinitionRegistry"]
