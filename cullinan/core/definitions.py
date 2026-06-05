# -*- coding: utf-8 -*-
"""Unified component definition model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional, Sequence, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from .application_context import ApplicationContext


class ScopeType(Enum):
    SINGLETON = auto()
    PROTOTYPE = auto()
    REQUEST = auto()


@dataclass(frozen=True)
class Definition:
    """Unified component definition."""

    name: str
    factory: Callable[["ApplicationContext"], Any]
    scope: ScopeType
    source: str
    type_: Optional[type] = None
    eager: bool = False
    conditions: Sequence[Callable[["ApplicationContext"], bool]] = field(default_factory=tuple)
    dependencies: Sequence[str] = field(default_factory=tuple)
    optional: bool = False
    tags: Dict[str, str] = field(default_factory=dict)
    qualifiers: Tuple[str, ...] = field(default_factory=tuple)
    healthcheck: Optional[Callable[["ApplicationContext", Any], bool]] = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("Definition.name cannot be empty.")
        if not callable(self.factory):
            raise ValueError("Definition.factory must be callable.")
        if not isinstance(self.scope, ScopeType):
            raise ValueError("Definition.scope must be a ScopeType value.")
        if not self.source:
            raise ValueError("Definition.source cannot be empty.")

        object.__setattr__(self, "conditions", tuple(self.conditions or ()))
        object.__setattr__(self, "dependencies", tuple(self.dependencies or ()))
        object.__setattr__(self, "qualifiers", tuple(self.qualifiers or ()))
        object.__setattr__(self, "tags", dict(self.tags or {}))

    def check_conditions(self, ctx: "ApplicationContext") -> bool:
        return all(condition(ctx) for condition in self.conditions)


ComponentDefinition = Definition

__all__ = ["ScopeType", "Definition", "ComponentDefinition"]
