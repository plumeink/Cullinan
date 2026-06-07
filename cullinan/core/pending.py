# -*- coding: utf-8 -*-
"""Pending registration queue for two-phase component assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import threading
from typing import Any, Callable, List, Optional, Type

from .semantic_rules import format_semantic_message


class ComponentType(Enum):
    SERVICE = "service"
    CONTROLLER = "controller"
    COMPONENT = "component"
    PROVIDER = "provider"


@dataclass
class PendingRegistration:
    cls: Type
    name: str
    component_type: ComponentType
    scope: str = "singleton"
    url_prefix: Optional[str] = None
    routes: List[Any] = field(default_factory=list)
    dependencies: Optional[List[str]] = None
    conditions: List[Callable] = field(default_factory=list)
    source_module: Optional[str] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    source_qualname: Optional[str] = None
    is_top_level: bool = True

    def get_source_location(self) -> str:
        if self.source_file and self.source_line:
            return f"{self.source_file}:{self.source_line}"
        if self.source_file:
            return self.source_file
        return "<unknown>"


class PendingRegistry:
    _instance: Optional["PendingRegistry"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._registrations: List[PendingRegistration] = []
        self._frozen = False
        self._lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "PendingRegistry":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        with cls._instance_lock:
            if cls._instance is not None:
                cls._instance._registrations.clear()
                cls._instance._frozen = False
            cls._instance = None
        # Invalidate the global type hints cache so that any stale
        # typing.get_type_hints() failures from previous test runs are
        # not reused across ApplicationContext instances.
        try:
            from cullinan.core.application_context import invalidate_type_hints_cache
            invalidate_type_hints_cache()
        except ImportError:
            pass

    def add(self, registration: PendingRegistration) -> None:
        with self._lock:
            if self._frozen:
                problem = (
                    f"Component '{registration.name}' attempted to register after ApplicationContext.refresh()."
                )
                guidance = (
                    "Keep decorator-based components at module top level and ensure their modules are imported "
                    "before refresh(). If you need stronger runtime ownership semantics, declare the boundary "
                    "with @module before refresh()."
                )
                if not registration.is_top_level:
                    problem = (
                        f"Component '{registration.name}' is defined in a local scope "
                        f"({registration.source_qualname}), so its decorator does not run until that block executes."
                    )
                    guidance = (
                        "Move the component to module top level. If you must create it dynamically, do not rely "
                        "on automatic scanning, and complete creation and registration explicitly before refresh(). "
                        "Cullinan's recommended path is to declare business components and boundaries instead of "
                        "falling back to manual app-style registration at runtime."
                    )
                raise RuntimeError(
                    f"{format_semantic_message('refresh-freeze', problem, guidance)} "
                    f"Source: {registration.get_source_location()}"
                )
            self._registrations.append(registration)

    def get_all(self) -> List[PendingRegistration]:
        with self._lock:
            return list(self._registrations)

    def drain(self) -> List[PendingRegistration]:
        with self._lock:
            drained = list(self._registrations)
            self._registrations.clear()
            return drained

    def get_by_type(self, component_type: ComponentType) -> List[PendingRegistration]:
        with self._lock:
            return [reg for reg in self._registrations if reg.component_type == component_type]

    def get_by_name(self, name: str) -> Optional[PendingRegistration]:
        with self._lock:
            for reg in self._registrations:
                if reg.name == name:
                    return reg
            return None

    def contains(self, name: str) -> bool:
        return self.get_by_name(name) is not None

    def clear(self) -> None:
        """Clear all pending registrations.
        
        Raises:
            RuntimeError: If the registry is frozen (after refresh()).
            Use reset() to completely reset the registry including frozen state.
        """
        with self._lock:
            if self._frozen:
                raise RuntimeError(
                    "Cannot clear() a frozen PendingRegistry. "
                    "After refresh() the registry is frozen to prevent accidental modifications. "
                    "Use PendingRegistry.reset() for full cleanup in test teardown."
                )
            self._registrations.clear()

    def freeze(self) -> None:
        with self._lock:
            self._frozen = True

    def unfreeze(self) -> None:
        with self._lock:
            self._frozen = False

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._registrations)

    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        return f"PendingRegistry(count={self.count}, frozen={self._frozen})"


__all__ = ["PendingRegistry", "PendingRegistration", "ComponentType"]
