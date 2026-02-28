# -*- coding: utf-8 -*-
"""Route data types for the Cullinan gateway layer.

Defines the data structures used by Router and Dispatcher for route
registration and matching.

Author: Plumeink
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Type


@dataclass(frozen=True)
class RouteEntry:
    """A registered route.

    Attributes:
        method: HTTP method (uppercase).  ``'*'`` means all methods.
        path: Original path pattern (e.g. ``/api/users/{id}``).
        path_regex: Compiled path regex (or ``None`` for static routes).
        handler: The callable that handles the request — typically a bound
                 controller method or a plain function.
        controller_cls: The controller class this handler belongs to (if any).
        controller_method_name: Name of the method on the controller class.
        param_names: Ordered list of path parameter names.
        metadata: Arbitrary metadata (e.g. ``tags``, ``summary`` for OpenAPI).
    """
    method: str
    path: str
    path_regex: Optional[Any] = None  # re.Pattern
    handler: Optional[Callable] = None
    controller_cls: Optional[Type] = None
    controller_method_name: str = ''
    param_names: tuple = ()
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteMatch:
    """Result of a successful route match.

    Attributes:
        entry: The matched ``RouteEntry``.
        path_params: Dict of extracted path parameter values.
    """
    entry: RouteEntry
    path_params: Dict[str, str] = field(default_factory=dict)


@dataclass
class RouteGroup:
    """A group of routes sharing a common prefix (used for controller registration).

    Attributes:
        prefix: URL prefix (e.g. ``/api/users``).
        routes: List of ``RouteEntry`` objects under this prefix.
        controller_cls: The controller class that owns the routes.
        middleware_tags: Middleware tags applied to all routes in this group.
    """
    prefix: str
    routes: List[RouteEntry] = field(default_factory=list)
    controller_cls: Optional[Type] = None
    middleware_tags: Set[str] = field(default_factory=set)


# HTTP method constants
HTTP_METHODS: Set[str] = frozenset({
    'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD',
})

