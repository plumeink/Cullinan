# -*- coding: utf-8 -*-
"""Lightweight invocation components for the unified Web runtime."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable

from .exception_handler import ExceptionHandler
from .web_core import WebRequest, WebResponse


@dataclass(frozen=True)
class HandlerMethod:
    handler: Callable[..., Any]
    controller: Any = None
    route: Any = None

    @property
    def name(self) -> str:
        return getattr(self.handler, "__name__", self.handler.__class__.__name__)


class ReturnValueHandler:
    """Converts handler results into WebResponse objects."""

    def handle(self, result: Any) -> WebResponse:
        if isinstance(result, WebResponse):
            return result

        if result is None:
            return WebResponse.no_content()

        if isinstance(result, tuple):
            return self._handle_tuple(result)

        if isinstance(result, (dict, list)):
            return WebResponse.json(result)

        if isinstance(result, str):
            return WebResponse.text(result)

        if isinstance(result, bytes):
            return WebResponse(body=result, content_type="application/octet-stream")

        if hasattr(result, "get_status") and hasattr(result, "get_body") and hasattr(result, "get_headers"):
            response = WebResponse(body=result.get_body(), status_code=result.get_status())
            for header in result.get_headers() or []:
                if isinstance(header, (list, tuple)) and len(header) >= 2:
                    response.add_header(str(header[0]), str(header[1]))
            return response

        return WebResponse.json(result)

    def _handle_tuple(self, values: tuple) -> WebResponse:
        if len(values) == 1:
            return self.handle(values[0])
        if len(values) == 2:
            body, status = values
            response = self.handle(body)
            response.status_code = int(status)
            return response
        body, status, headers = values[0], values[1], values[2]
        response = self.handle(body)
        response.status_code = int(status)
        if isinstance(headers, dict):
            for name, value in headers.items():
                response.set_header(name, value)
        elif isinstance(headers, (list, tuple)):
            for item in headers:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    response.add_header(str(item[0]), str(item[1]))
        return response


class ExceptionResolver:
    """Delegates exception resolution to the gateway exception handler."""

    def __init__(self, exception_handler: ExceptionHandler) -> None:
        self.exception_handler = exception_handler

    async def resolve(self, request: WebRequest, exc: Exception) -> WebResponse:
        result = self.exception_handler.handle(request, exc)
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, WebResponse):
            return result
        return WebResponse.json(result)
