# -*- coding: utf-8 -*-
"""Cullinan Unified Response Object

Transport-agnostic response representation.  Controller methods return a
``CullinanResponse`` and the active adapter serialises it onto the wire.


Author: Plumeink
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CullinanResponse:
    """Unified HTTP response object.

    This object is **transport-agnostic**.  Adapter layers read its
    attributes and write them to the underlying server's response API.

    Attributes:
        status_code: HTTP status code (default ``200``).
        headers: Response headers as a dict (may contain duplicate keys via list).
        body: Response body — can be ``str``, ``bytes``, ``dict`` (auto-JSON),
              ``list`` (auto-JSON), or ``None``.
        content_type: Shortcut for the ``Content-Type`` header.
    """

    __slots__ = (
        'status_code', '_headers', '_body', '_content_type', '_frozen',
    )

    def __init__(
        self,
        body: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> None:
        self.status_code: int = status_code
        self._headers: List[Tuple[str, str]] = []
        self._body: Any = body
        self._content_type: Optional[str] = content_type
        self._frozen: bool = False

        if headers:
            for k, v in headers.items():
                self._headers.append((k, v))

    # ------------------------------------------------------------------
    # Headers
    # ------------------------------------------------------------------

    def set_header(self, name: str, value: str) -> 'CullinanResponse':
        """Set (replace) a header value.  Returns self for chaining."""
        self._check_frozen()
        lower = name.lower()
        self._headers = [(k, v) for k, v in self._headers if k.lower() != lower]
        self._headers.append((name, value))
        return self

    def add_header(self, name: str, value: str) -> 'CullinanResponse':
        """Append a header (allows duplicate keys).  Returns self for chaining."""
        self._check_frozen()
        self._headers.append((name, value))
        return self

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get first matching header value (case-insensitive)."""
        lower = name.lower()
        for k, v in self._headers:
            if k.lower() == lower:
                return v
        return default

    @property
    def headers(self) -> List[Tuple[str, str]]:
        """All response headers as a list of ``(name, value)`` tuples."""
        return list(self._headers)

    def headers_dict(self) -> Dict[str, str]:
        """Headers as a plain dict (last value wins for duplicates)."""
        return {k: v for k, v in self._headers}

    # ------------------------------------------------------------------
    # Body
    # ------------------------------------------------------------------

    @property
    def body(self) -> Any:
        return self._body

    @body.setter
    def body(self, value: Any) -> None:
        self._check_frozen()
        self._body = value

    @property
    def content_type(self) -> str:
        if self._content_type:
            return self._content_type
        # infer from body
        if isinstance(self._body, (dict, list)):
            return 'application/json'
        if isinstance(self._body, bytes):
            return 'application/octet-stream'
        return 'text/plain; charset=utf-8'

    @content_type.setter
    def content_type(self, value: str) -> None:
        self._check_frozen()
        self._content_type = value

    def render_body(self) -> bytes:
        """Serialize ``body`` to ``bytes`` ready for transmission.

        - ``dict`` / ``list``  → JSON bytes
        - ``str``              → UTF-8 bytes
        - ``bytes``            → as-is
        - ``None``             → empty bytes
        """
        b = self._body
        if b is None:
            return b''
        if isinstance(b, bytes):
            return b
        if isinstance(b, str):
            return b.encode('utf-8')
        if isinstance(b, (dict, list)):
            return json.dumps(b, ensure_ascii=False, default=str).encode('utf-8')
        # fallback: try str()
        return str(b).encode('utf-8')

    # ------------------------------------------------------------------
    # Freeze (immutability after pipeline)
    # ------------------------------------------------------------------

    def freeze(self) -> None:
        """Mark the response as frozen — no further modifications allowed."""
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def _check_frozen(self) -> None:
        if self._frozen:
            raise RuntimeError('Cannot modify a frozen CullinanResponse')

    # ------------------------------------------------------------------
    # Convenience factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def json(
        data: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> 'CullinanResponse':
        """Create a JSON response.

        Args:
            data: JSON-serialisable payload.
            status_code: HTTP status code.
            headers: Extra headers.
        """
        return CullinanResponse(
            body=data,
            status_code=status_code,
            headers=headers,
            content_type='application/json',
        )

    @staticmethod
    def text(
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> 'CullinanResponse':
        """Create a plain-text response."""
        return CullinanResponse(
            body=content,
            status_code=status_code,
            headers=headers,
            content_type='text/plain; charset=utf-8',
        )

    @staticmethod
    def html(
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> 'CullinanResponse':
        """Create an HTML response."""
        return CullinanResponse(
            body=content,
            status_code=status_code,
            headers=headers,
            content_type='text/html; charset=utf-8',
        )

    @staticmethod
    def redirect(
        url: str,
        status_code: int = 302,
    ) -> 'CullinanResponse':
        """Create a redirect response."""
        resp = CullinanResponse(status_code=status_code)
        resp.set_header('Location', url)
        return resp

    @staticmethod
    def error(
        status_code: int,
        message: str,
        details: Any = None,
    ) -> 'CullinanResponse':
        """Create a structured error response (JSON)."""
        payload: Dict[str, Any] = {'error': message, 'status': status_code}
        if details is not None:
            payload['details'] = details
        return CullinanResponse(
            body=payload,
            status_code=status_code,
            content_type='application/json',
        )

    @staticmethod
    def no_content() -> 'CullinanResponse':
        """Create a 204 No Content response."""
        return CullinanResponse(status_code=204)

    # ------------------------------------------------------------------
    # Reset / pool support
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset to default state (for object-pool reuse)."""
        self.status_code = 200
        self._headers.clear()
        self._body = None
        self._content_type = None
        self._frozen = False

    # ------------------------------------------------------------------
    # Compatibility bridge with legacy HttpResponse
    # ------------------------------------------------------------------

    def get_status(self) -> int:
        """Legacy compat: return status code."""
        return self.status_code

    def get_body(self) -> Any:
        """Legacy compat: return raw body."""
        return self._body

    def get_headers(self) -> List[Tuple[str, str]]:
        """Legacy compat: return header list."""
        return list(self._headers)

    def set_body(self, data: Any) -> None:
        """Legacy compat: set body."""
        self._body = data

    def set_status(self, status: int, msg: str = '') -> None:
        """Legacy compat: set status code."""
        self.status_code = status

    def __repr__(self) -> str:
        return f'<CullinanResponse [{self.status_code}] {self.content_type}>'

