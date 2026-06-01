# -*- coding: utf-8 -*-
"""Unified Web driver SPI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class DriverCapabilities:
    supports_http: bool = True
    supports_websocket: bool = False
    supports_lifespan: bool = False
    supports_streaming_request: bool = False
    supports_streaming_response: bool = False
    supports_multipart: bool = True
    supports_http2: bool = False


class DriverRequestAdapter(ABC):
    @abstractmethod
    async def build_request(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class DriverResponseWriter(ABC):
    @abstractmethod
    async def write_response(self, response: Any, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class WebDriver(ABC):
    """Driver SPI shared by ASGI, Tornado and future runtimes."""

    def __init__(self, runtime: Optional[Any] = None) -> None:
        self._runtime = runtime

    @property
    def runtime(self) -> Optional[Any]:
        return self._runtime

    def bind_runtime(self, runtime: Any) -> None:
        self._runtime = runtime

    @abstractmethod
    def capabilities(self) -> DriverCapabilities:
        raise NotImplementedError

    @abstractmethod
    def create_request_adapter(self) -> DriverRequestAdapter:
        raise NotImplementedError

    @abstractmethod
    def create_response_writer(self) -> DriverResponseWriter:
        raise NotImplementedError

    @abstractmethod
    def build_app(self) -> Any:
        raise NotImplementedError
