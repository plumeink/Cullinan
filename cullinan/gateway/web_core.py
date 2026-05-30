# -*- coding: utf-8 -*-
"""Unified Web core objects used across all runtime drivers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Any, Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union
from urllib.parse import parse_qs


HeaderInput = Union[
    "WebHeaders",
    Mapping[str, str],
    Sequence[Tuple[str, str]],
]


class WebHeaders:
    """Case-insensitive multi-value HTTP headers preserving insertion order."""

    def __init__(self, initial: Optional[HeaderInput] = None) -> None:
        self._items: List[Tuple[str, str]] = []
        if initial is None:
            return
        if isinstance(initial, WebHeaders):
            self._items = list(initial._items)
        elif isinstance(initial, Mapping):
            for name, value in initial.items():
                self.add(name, value)
        else:
            for name, value in initial:
                self.add(name, value)

    def add(self, name: str, value: Any) -> "WebHeaders":
        self._items.append((str(name), self._stringify(value)))
        return self

    def set(self, name: str, value: Any) -> "WebHeaders":
        lower = name.lower()
        self._items = [(k, v) for k, v in self._items if k.lower() != lower]
        self._items.append((str(name), self._stringify(value)))
        return self

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        lower = name.lower()
        for key, value in reversed(self._items):
            if key.lower() == lower:
                return value
        return default

    def get_all(self, name: str) -> List[str]:
        lower = name.lower()
        return [value for key, value in self._items if key.lower() == lower]

    def remove(self, name: str) -> None:
        lower = name.lower()
        self._items = [(k, v) for k, v in self._items if k.lower() != lower]

    def contains(self, name: str) -> bool:
        lower = name.lower()
        return any(key.lower() == lower for key, _ in self._items)

    def items(self) -> List[Tuple[str, str]]:
        return list(self._items)

    def keys(self) -> List[str]:
        return [name for name, _ in self._items]

    def values(self) -> List[str]:
        return [value for _, value in self._items]

    def as_dict(self, *, multi: bool = False) -> Dict[str, Any]:
        if multi:
            result: Dict[str, List[str]] = {}
            for name, value in self._items:
                result.setdefault(name, []).append(value)
            return result
        return {name: value for name, value in self._items}

    def copy(self) -> "WebHeaders":
        return WebHeaders(self)

    def __iter__(self) -> Iterator[str]:
        for name, _ in self._items:
            yield name

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.contains(name)

    def __getitem__(self, name: str) -> str:
        value = self.get(name)
        if value is None:
            raise KeyError(name)
        return value

    def __setitem__(self, name: str, value: Any) -> None:
        self.set(name, value)

    def __repr__(self) -> str:
        return f"WebHeaders({self._items!r})"

    @staticmethod
    def _stringify(value: Any) -> str:
        if isinstance(value, bytes):
            return value.decode("latin-1")
        return str(value)


@dataclass
class ResponseCookie:
    name: str
    value: str
    path: str = "/"
    domain: Optional[str] = None
    max_age: Optional[int] = None
    expires: Optional[str] = None
    secure: bool = False
    http_only: bool = False
    same_site: Optional[str] = None

    def to_header_value(self) -> str:
        cookie = SimpleCookie()
        cookie[self.name] = self.value
        morsel = cookie[self.name]
        morsel["path"] = self.path
        if self.domain:
            morsel["domain"] = self.domain
        if self.max_age is not None:
            morsel["max-age"] = str(self.max_age)
        if self.expires:
            morsel["expires"] = self.expires
        if self.secure:
            morsel["secure"] = True
        if self.http_only:
            morsel["httponly"] = True
        if self.same_site:
            morsel["samesite"] = self.same_site
        return morsel.OutputString()


class WebCookies:
    """Cookie container for requests and responses."""

    def __init__(self, initial: Optional[Mapping[str, str]] = None) -> None:
        self._values: Dict[str, str] = dict(initial or {})

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self._values.get(name, default)

    def set(self, name: str, value: str) -> None:
        self._values[name] = value

    def items(self) -> List[Tuple[str, str]]:
        return list(self._values.items())

    def as_dict(self) -> Dict[str, str]:
        return dict(self._values)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in self._values

    def __repr__(self) -> str:
        return f"WebCookies({self._values!r})"


class WebRequest:
    """Transport-agnostic HTTP request."""

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        headers: Optional[HeaderInput] = None,
        body: Union[bytes, str, None] = b"",
        query_string: str = "",
        client_ip: str = "127.0.0.1",
        scheme: str = "http",
        server_host: str = "localhost",
        server_port: int = 80,
        full_url: str = "",
        cookies: Optional[Mapping[str, str]] = None,
        raw_path: Optional[str] = None,
        attributes: Optional[MutableMapping[str, Any]] = None,
    ) -> None:
        self.method = method.upper()
        self.path = path
        self.raw_path = raw_path or path
        self.query_string = query_string
        self._headers = WebHeaders(headers)
        self.cookies = WebCookies(cookies or self._parse_cookie_header(self._headers.get("cookie")))
        self.path_params: Dict[str, str] = {}
        self.attributes: MutableMapping[str, Any] = attributes or {}
        self.body = body if isinstance(body, bytes) else body.encode("utf-8") if isinstance(body, str) else b""
        self.client_ip = client_ip
        self.scheme = scheme
        self.server_host = server_host
        self.server_port = server_port
        self.full_url = full_url or f"{scheme}://{server_host}:{server_port}{path}"
        self._query_params: Optional[Dict[str, str]] = None
        self._query_params_multi: Optional[Dict[str, List[str]]] = None
        self._json_cache: Any = _SENTINEL
        self._form_cache: Any = _SENTINEL
        self._text_cache: Any = _SENTINEL

    @property
    def headers(self) -> WebHeaders:
        return self._headers

    @property
    def content_type(self) -> Optional[str]:
        return self.headers.get("Content-Type")

    def header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.headers.get(name, default)

    def header_all(self, name: str) -> List[str]:
        return self.headers.get_all(name)

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.header(name, default)

    def cookie(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.cookies.get(name, default)

    @property
    def authority(self) -> str:
        host = self.header("Host")
        if host:
            return host
        return f"{self.server_host}:{self.server_port}"

    @property
    def query_params(self) -> Dict[str, str]:
        if self._query_params is None:
            self._parse_query_string()
        return self._query_params or {}

    @property
    def query_params_multi(self) -> Dict[str, List[str]]:
        if self._query_params_multi is None:
            self._parse_query_string()
        return self._query_params_multi or {}

    def _parse_query_string(self) -> None:
        raw = parse_qs(self.query_string, keep_blank_values=True)
        self._query_params_multi = {k: list(v) for k, v in raw.items()}
        self._query_params = {k: v[-1] for k, v in raw.items()}

    async def bytes(self) -> bytes:
        return self.body

    async def text(self, encoding: Optional[str] = None) -> str:
        if self._text_cache is _SENTINEL:
            encodings = [encoding] if encoding else []
            encodings.extend(["utf-8", "latin-1"])
            last_error: Optional[Exception] = None
            for candidate in encodings:
                if candidate is None:
                    continue
                try:
                    self._text_cache = self.body.decode(candidate)
                    break
                except UnicodeDecodeError as exc:
                    last_error = exc
            if self._text_cache is _SENTINEL:
                if last_error is not None:
                    raise last_error
                self._text_cache = ""
        return self._text_cache

    async def json(self) -> Any:
        if self._json_cache is _SENTINEL:
            if not self.body:
                self._json_cache = None
            else:
                try:
                    self._json_cache = json.loads(await self.text())
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError(f"Invalid JSON body: {exc}") from exc
        return self._json_cache

    async def form(self) -> Dict[str, str]:
        if self._form_cache is _SENTINEL:
            if not self.body:
                self._form_cache = {}
            else:
                raw = parse_qs(await self.text(), keep_blank_values=True)
                self._form_cache = {k: v[-1] for k, v in raw.items()}
        return self._form_cache

    @property
    def is_json(self) -> bool:
        ct = self.content_type
        return bool(ct and "application/json" in ct.lower())

    @property
    def is_form(self) -> bool:
        ct = self.content_type
        if not ct:
            return False
        lower = ct.lower()
        return "application/x-www-form-urlencoded" in lower or "multipart/form-data" in lower

    @staticmethod
    def _parse_cookie_header(cookie_header: Optional[str]) -> Dict[str, str]:
        if not cookie_header:
            return {}
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        return {name: morsel.value for name, morsel in cookie.items()}

    def __repr__(self) -> str:
        return f"<WebRequest {self.method} {self.path}>"


class WebResponse:
    """Transport-agnostic HTTP response with explicit commit semantics."""

    def __init__(
        self,
        body: Any = None,
        status_code: int = 200,
        headers: Optional[HeaderInput] = None,
        content_type: Optional[str] = None,
    ) -> None:
        self.status_code = int(status_code)
        self._headers = WebHeaders(headers)
        self._body = body
        self._content_type = content_type
        self._committed = False
        self._cookies: List[ResponseCookie] = []

    @property
    def status(self) -> int:
        return self.status_code

    @status.setter
    def status(self, value: int) -> None:
        self._check_mutable()
        self.status_code = int(value)

    @property
    def headers(self) -> List[Tuple[str, str]]:
        return self._headers.items()

    @property
    def header_map(self) -> WebHeaders:
        return self._headers

    def set_header(self, name: str, value: Any) -> "WebResponse":
        self._check_mutable()
        self._headers.set(name, value)
        return self

    def add_header(self, name: str, value: Any) -> "WebResponse":
        self._check_mutable()
        self._headers.add(name, value)
        return self

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        if name.lower() == "content-type" and self._content_type:
            return self._content_type
        return self._headers.get(name, default)

    def get_headers(self) -> List[Tuple[str, str]]:
        return self.iter_headers()

    def headers_dict(self) -> Dict[str, str]:
        return self._headers.as_dict()

    @property
    def body(self) -> Any:
        return self._body

    @body.setter
    def body(self, value: Any) -> None:
        self._check_mutable()
        self._body = value

    def set_body(self, data: Any) -> None:
        self.body = data

    @property
    def content_type(self) -> str:
        if self._content_type:
            return self._content_type
        if self._headers.contains("Content-Type"):
            return self._headers.get("Content-Type") or ""
        if isinstance(self._body, (dict, list)):
            return "application/json"
        if isinstance(self._body, bytes):
            return "application/octet-stream"
        return "text/plain; charset=utf-8"

    @content_type.setter
    def content_type(self, value: str) -> None:
        self._check_mutable()
        self._content_type = value

    def set_cookie(
        self,
        name: str,
        value: str,
        *,
        path: str = "/",
        domain: Optional[str] = None,
        max_age: Optional[int] = None,
        expires: Optional[str] = None,
        secure: bool = False,
        http_only: bool = False,
        same_site: Optional[str] = None,
    ) -> "WebResponse":
        self._check_mutable()
        self._cookies.append(
            ResponseCookie(
                name=name,
                value=value,
                path=path,
                domain=domain,
                max_age=max_age,
                expires=expires,
                secure=secure,
                http_only=http_only,
                same_site=same_site,
            )
        )
        return self

    @property
    def cookies(self) -> List[ResponseCookie]:
        return list(self._cookies)

    def iter_headers(self, *, include_content_type: bool = True) -> List[Tuple[str, str]]:
        headers = self._headers.items()
        if include_content_type and self.content_type and not self._headers.contains("Content-Type"):
            headers.append(("Content-Type", self.content_type))
        for cookie in self._cookies:
            headers.append(("Set-Cookie", cookie.to_header_value()))
        return headers

    def render_body(self) -> bytes:
        if self._body is None:
            return b""
        if isinstance(self._body, bytes):
            return self._body
        if isinstance(self._body, str):
            return self._body.encode("utf-8")
        if isinstance(self._body, (dict, list)):
            return json.dumps(self._body, ensure_ascii=False, default=str).encode("utf-8")
        return str(self._body).encode("utf-8")

    def freeze(self) -> None:
        self._committed = True

    def commit(self) -> None:
        self.freeze()

    @property
    def is_frozen(self) -> bool:
        return self._committed

    @property
    def committed(self) -> bool:
        return self._committed

    def reset(self) -> None:
        self.status_code = 200
        self._headers = WebHeaders()
        self._body = None
        self._content_type = None
        self._committed = False
        self._cookies = []

    def get_status(self) -> int:
        return self.status_code

    def get_body(self) -> Any:
        return self._body

    def set_status(self, status: int, msg: str = "") -> None:
        self.status = int(status)

    def _check_mutable(self) -> None:
        if self._committed:
            raise RuntimeError("Cannot modify a committed WebResponse")

    @staticmethod
    def json(data: Any, status_code: int = 200, headers: Optional[Mapping[str, str]] = None) -> "WebResponse":
        return WebResponse(body=data, status_code=status_code, headers=headers, content_type="application/json")

    @staticmethod
    def text(content: str, status_code: int = 200, headers: Optional[Mapping[str, str]] = None) -> "WebResponse":
        return WebResponse(body=content, status_code=status_code, headers=headers, content_type="text/plain; charset=utf-8")

    @staticmethod
    def html(content: str, status_code: int = 200, headers: Optional[Mapping[str, str]] = None) -> "WebResponse":
        return WebResponse(body=content, status_code=status_code, headers=headers, content_type="text/html; charset=utf-8")

    @staticmethod
    def redirect(url: str, status_code: int = 302) -> "WebResponse":
        response = WebResponse(status_code=status_code)
        response.set_header("Location", url)
        return response

    @staticmethod
    def error(status_code: int, message: str, details: Any = None) -> "WebResponse":
        payload: Dict[str, Any] = {"error": message, "status": status_code}
        if details is not None:
            payload["details"] = details
        return WebResponse(body=payload, status_code=status_code, content_type="application/json")

    @staticmethod
    def no_content() -> "WebResponse":
        return WebResponse(status_code=204)

    def __repr__(self) -> str:
        return f"<WebResponse [{self.status_code}] {self.content_type}>"


@dataclass
class WebExchange:
    request: WebRequest
    response: Optional[WebResponse] = None
    runtime: Any = None
    driver_meta: Optional[Dict[str, Any]] = None


class HeaderPolicy:
    """Applies stable response header defaults."""

    def __init__(
        self,
        *,
        default_security_headers: Optional[Mapping[str, str]] = None,
        allow_origins: Optional[str] = None,
        allow_methods: Optional[str] = None,
        allow_headers: Optional[str] = None,
        allow_credentials: bool = False,
        trust_forwarded_headers: bool = False,
    ) -> None:
        self.default_security_headers = dict(
            default_security_headers
            or {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN",
                "Referrer-Policy": "strict-origin-when-cross-origin",
            }
        )
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.allow_credentials = allow_credentials
        self.trust_forwarded_headers = trust_forwarded_headers

    def apply(self, request: WebRequest, response: WebResponse) -> WebResponse:
        for name, value in self.default_security_headers.items():
            if response.get_header(name) is None:
                response.set_header(name, value)

        if self.allow_origins is not None:
            response.set_header("Access-Control-Allow-Origin", self.allow_origins)
        if self.allow_methods is not None:
            response.set_header("Access-Control-Allow-Methods", self.allow_methods)
        if self.allow_headers is not None:
            response.set_header("Access-Control-Allow-Headers", self.allow_headers)
        if self.allow_credentials:
            response.set_header("Access-Control-Allow-Credentials", "true")

        return response


class _Sentinel:
    pass


_SENTINEL = _Sentinel()
