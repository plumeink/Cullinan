# -*- coding: utf-8 -*-
"""High-availability Web runtime primitives."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional

from .dispatcher import Dispatcher
from .exception_handler import ExceptionHandler
from .invocation import ExceptionResolver, ReturnValueHandler
from .pipeline import MiddlewarePipeline
from .router import Router
from .web_core import HeaderPolicy


class WebRuntimeState:
    CREATED = "CREATED"
    BUILDING = "BUILDING"
    VALIDATING = "VALIDATING"
    WARMING = "WARMING"
    ACTIVE = "ACTIVE"
    DRAINING = "DRAINING"
    CLOSED = "CLOSED"


@dataclass
class WebRuntimeConfig:
    warmup_checks: Iterable[Callable[["WebRuntime"], None]] = field(default_factory=tuple)
    health_checks: Iterable[Callable[["WebRuntime"], None]] = field(default_factory=tuple)
    drain_timeout: float = 30.0
    trust_forwarded_headers: bool = False


class WebRuntime:
    """Carries the active Web stack and supports atomic runtime switching."""

    _active_runtime: Optional["WebRuntime"] = None
    _active_lock = threading.RLock()

    def __init__(
        self,
        *,
        router: Optional[Router] = None,
        pipeline: Optional[MiddlewarePipeline] = None,
        exception_handler: Optional[ExceptionHandler] = None,
        header_policy: Optional[HeaderPolicy] = None,
        return_value_handler: Optional[ReturnValueHandler] = None,
        exception_resolver: Optional[ExceptionResolver] = None,
        config: Optional[WebRuntimeConfig] = None,
    ) -> None:
        self.router = router or Router()
        self.pipeline = pipeline or MiddlewarePipeline()
        self.exception_handler = exception_handler or ExceptionHandler()
        self.header_policy = header_policy or HeaderPolicy()
        self.return_value_handler = return_value_handler or ReturnValueHandler()
        self.exception_resolver = exception_resolver or ExceptionResolver(self.exception_handler)
        self.config = config or WebRuntimeConfig()
        self.dispatcher = Dispatcher(
            router=self.router,
            pipeline=self.pipeline,
            exception_handler=self.exception_handler,
            header_policy=self.header_policy,
            return_value_handler=self.return_value_handler,
            exception_resolver=self.exception_resolver,
        )
        self.state = WebRuntimeState.CREATED
        self._request_count = 0
        self._request_lock = threading.RLock()

    def validate(self) -> None:
        self.state = WebRuntimeState.VALIDATING
        for check in self.config.health_checks:
            check(self)

    def warmup(self) -> None:
        self.state = WebRuntimeState.WARMING
        for check in self.config.warmup_checks:
            check(self)

    def prepare(self) -> None:
        self.state = WebRuntimeState.BUILDING
        self.validate()
        self.warmup()

    def activate(self) -> Optional["WebRuntime"]:
        self.prepare()
        with self._active_lock:
            previous = self.__class__._active_runtime
            if previous is not None and previous is not self and previous.state != WebRuntimeState.CLOSED:
                previous.state = WebRuntimeState.DRAINING
            self.__class__._active_runtime = self
            self.state = WebRuntimeState.ACTIVE
        return previous

    def begin_request(self) -> None:
        with self._request_lock:
            self._request_count += 1

    def end_request(self) -> None:
        with self._request_lock:
            self._request_count = max(0, self._request_count - 1)
            if self.state == WebRuntimeState.DRAINING and self._request_count == 0:
                self.state = WebRuntimeState.CLOSED

    @property
    def request_count(self) -> int:
        with self._request_lock:
            return self._request_count

    @classmethod
    def current(cls) -> Optional["WebRuntime"]:
        with cls._active_lock:
            return cls._active_runtime

    @classmethod
    def activate_runtime(cls, runtime: "WebRuntime") -> Optional["WebRuntime"]:
        return runtime.activate()

    @classmethod
    def clear_active(cls) -> None:
        with cls._active_lock:
            cls._active_runtime = None
