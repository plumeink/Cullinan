# -*- coding: utf-8 -*-
"""构建期待注册队列。"""

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

    def add(self, registration: PendingRegistration) -> None:
        with self._lock:
            if self._frozen:
                problem = (
                    f"组件 '{registration.name}' 在 ApplicationContext.refresh() 之后才尝试注册。"
                )
                guidance = (
                    "将所有带装饰器的组件放在模块顶层，并确保其所在模块在 refresh() 之前已完成导入。"
                    "需要更强运行时归属时，请在 refresh() 前通过 @module 明确边界。"
                )
                if not registration.is_top_level:
                    problem = (
                        f"组件 '{registration.name}' 定义在局部作用域 ({registration.source_qualname})，"
                        "直到运行到该代码块时装饰器才会执行。"
                    )
                    guidance = (
                        "把该组件移动到模块顶层；如果必须动态创建，请不要依赖自动扫描，并在 refresh() 前显式完成创建与注册。"
                        "Cullinan 的推荐路径是声明业务组件和边界，而不是在运行中回退到手工 app 注册。"
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
        with self._lock:
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
