# -*- coding: utf-8 -*-
"""Cullinan Unified Request Object

Transport-agnostic request representation. All adapters (Tornado, ASGI)
convert their native request objects into CullinanRequest before dispatching.


Author: Plumeink
"""

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class CullinanRequest:
    """Unified HTTP request object for the Cullinan framework.

    This object is **transport-agnostic** — it does not depend on Tornado,
    ASGI, or any other HTTP library.  Adapter layers are responsible for
    constructing a ``CullinanRequest`` from the underlying server's native
    request representation.

    Attributes:
        method: HTTP method (uppercase: GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD).
        path: URL path *without* query string (e.g. ``/api/users/123``).
        full_url: Complete URL including scheme, host, path and query string.
        query_string: Raw query string (e.g. ``page=1&size=10``).
        headers: Case-insensitive header mapping.
        cookies: Parsed cookies.
        path_params: Route parameters extracted by the router (e.g. ``{"id": "123"}``).
        query_params: Parsed query parameters (single-value by default).
        content_type: Value of the ``Content-Type`` header (or ``None``).
        body: Raw request body as ``bytes``.
        client_ip: Client IP address.
        scheme: URL scheme (``http`` or ``https``).
        server_host: Server hostname.
        server_port: Server port.
    """

    __slots__ = (
        'method', 'path', 'full_url', 'query_string',
        '_headers', 'cookies', 'path_params', '_query_params',
        'content_type', 'body', 'client_ip',
        'scheme', 'server_host', 'server_port',
        '_json_cache', '_form_cache', '_text_cache',
        '_raw_query_params',
    )

    def __init__(
        self,
        method: str = 'GET',
        path: str = '/',
        headers: Optional[Dict[str, str]] = None,
        body: bytes = b'',
        query_string: str = '',
        client_ip: str = '127.0.0.1',
        scheme: str = 'http',
        server_host: str = 'localhost',
        server_port: int = 80,
        full_url: str = '',
        cookies: Optional[Dict[str, str]] = None,
    ) -> None:
        self.method: str = method.upper()
        self.path: str = path
        self.full_url: str = full_url or f'{scheme}://{server_host}:{server_port}{path}'
        self.query_string: str = query_string
        self._headers: _CaseInsensitiveDict = _CaseInsensitiveDict(headers or {})
        self.cookies: Dict[str, str] = cookies or {}
        self.path_params: Dict[str, str] = {}
        self._query_params: Optional[Dict[str, str]] = None
        self._raw_query_params: Optional[Dict[str, List[str]]] = None
        self.content_type: Optional[str] = self._headers.get('content-type')
        self.body: bytes = body if isinstance(body, bytes) else body.encode('utf-8') if isinstance(body, str) else b''
        self.client_ip: str = client_ip
        self.scheme: str = scheme
        self.server_host: str = server_host
        self.server_port: int = server_port

        # Lazy-parsed caches
        self._json_cache: Any = _SENTINEL
        self._form_cache: Any = _SENTINEL
        self._text_cache: Any = _SENTINEL

    # ------------------------------------------------------------------
    # Headers
    # ------------------------------------------------------------------

    @property
    def headers(self) -> '_CaseInsensitiveDict':
        """Case-insensitive header dict."""
        return self._headers

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a single header value (case-insensitive)."""
        return self._headers.get(name, default)

    # ------------------------------------------------------------------
    # Query parameters
    # ------------------------------------------------------------------

    @property
    def query_params(self) -> Dict[str, str]:
        """Parsed query parameters (single value per key; last wins)."""
        if self._query_params is None:
            self._parse_query_string()
        return self._query_params  # type: ignore[return-value]

    @property
    def query_params_multi(self) -> Dict[str, List[str]]:
        """Parsed query parameters with all values per key."""
        if self._raw_query_params is None:
            self._parse_query_string()
        return self._raw_query_params  # type: ignore[return-value]

    def _parse_query_string(self) -> None:
        raw = parse_qs(self.query_string, keep_blank_values=True)
        self._raw_query_params = {k: v for k, v in raw.items()}
        self._query_params = {k: v[-1] for k, v in raw.items()}

    def get_query_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a single query parameter value."""
        return self.query_params.get(name, default)

    # ------------------------------------------------------------------
    # Body parsing (lazy)
    # ------------------------------------------------------------------

    async def json(self) -> Any:
        """Parse body as JSON.

        Returns:
            Parsed JSON value (dict / list / scalar).

        Raises:
            ValueError: If body is not valid JSON.
        """
        if self._json_cache is _SENTINEL:
            if not self.body:
                self._json_cache = None
            else:
                try:
                    text = self.body.decode('utf-8')
                    self._json_cache = json.loads(text)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError(f'Invalid JSON body: {exc}') from exc
        return self._json_cache

    async def form(self) -> Dict[str, str]:
        """Parse body as URL-encoded form data.

        Returns:
            Dict of form field values (single value per key).
        """
        if self._form_cache is _SENTINEL:
            if not self.body:
                self._form_cache = {}
            else:
                try:
                    text = self.body.decode('utf-8')
                    raw = parse_qs(text, keep_blank_values=True)
                    self._form_cache = {k: v[-1] for k, v in raw.items()}
                except Exception:
                    self._form_cache = {}
        return self._form_cache

    async def text(self) -> str:
        """Return body as UTF-8 string."""
        if self._text_cache is _SENTINEL:
            try:
                self._text_cache = self.body.decode('utf-8')
            except UnicodeDecodeError:
                self._text_cache = self.body.decode('latin-1')
        return self._text_cache

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def is_json(self) -> bool:
        """Return True if the Content-Type indicates JSON."""
        ct = self.content_type
        if not ct:
            return False
        return 'application/json' in ct.lower()

    @property
    def is_form(self) -> bool:
        """Return True if the Content-Type indicates form data."""
        ct = self.content_type
        if not ct:
            return False
        lower = ct.lower()
        return 'application/x-www-form-urlencoded' in lower or 'multipart/form-data' in lower

    def __repr__(self) -> str:
        return f'<CullinanRequest {self.method} {self.path}>'


# ======================================================================
# Internal helpers
# ======================================================================

class _SENTINEL_TYPE:
    """Sentinel for lazy cache slots."""
    __slots__ = ()
    def __repr__(self) -> str:
        return '<SENTINEL>'
    def __bool__(self) -> bool:
        return False

_SENTINEL = _SENTINEL_TYPE()


class _CaseInsensitiveDict:
    """Minimal case-insensitive dict for HTTP headers.

    Stores keys in lower-case internally.  Iteration yields original-cased keys.
    """

    __slots__ = ('_store',)

    def __init__(self, data: Optional[Dict[str, str]] = None) -> None:
        # _store: { lower_key: (original_key, value) }
        self._store: Dict[str, tuple] = {}
        if data:
            for k, v in data.items():
                self._store[k.lower()] = (k, v)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        entry = self._store.get(key.lower())
        return entry[1] if entry else default

    def __getitem__(self, key: str) -> str:
        entry = self._store.get(key.lower())
        if entry is None:
            raise KeyError(key)
        return entry[1]

    def __contains__(self, key: str) -> bool:
        return key.lower() in self._store

    def __setitem__(self, key: str, value: str) -> None:
        self._store[key.lower()] = (key, value)

    def update(self, data: Dict[str, str]) -> None:
        """Merge another dict into this header map."""
        for k, v in data.items():
            self._store[k.lower()] = (k, v)

    def __iter__(self):
        for original_key, _ in self._store.values():
            yield original_key

    def __len__(self) -> int:
        return len(self._store)

    def items(self):
        for original_key, value in self._store.values():
            yield original_key, value

    def keys(self):
        for original_key, _ in self._store.values():
            yield original_key

    def values(self):
        for _, value in self._store.values():
            yield value

    def __repr__(self) -> str:
        inner = ', '.join(f'{k!r}: {v!r}' for k, v in self.items())
        return f'{{{inner}}}'

    def to_dict(self) -> Dict[str, str]:
        """Export as a plain dict (original-cased keys)."""
        return {k: v for k, v in self.items()}

