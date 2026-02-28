# -*- coding: utf-8 -*-
"""Cullinan Server Adapter — Abstract Base Class

Defines the contract that all runtime adapters must implement.

Author: Plumeink
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from cullinan.gateway.dispatcher import Dispatcher

logger = logging.getLogger(__name__)


class ServerAdapter(ABC):
    """Abstract base class for server runtime adapters.

    Adapters are responsible for:
    1. Creating a native server application that routes **all** requests
       through the shared ``Dispatcher``.
    2. Converting native request objects into ``CullinanRequest``.
    3. Converting ``CullinanResponse`` back into the native response format.
    4. Starting / stopping the server.

    Concrete implementations:
    - ``TornadoAdapter``  — uses a single ``tornado.web.RequestHandler``
    - ``ASGIAdapter``     — produces a standard ASGI 3.0 application callable
    """

    def __init__(self, dispatcher: Dispatcher) -> None:
        self._dispatcher = dispatcher

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    @abstractmethod
    def create_app(self) -> Any:
        """Create the native application object.

        Returns:
            The native application (e.g. ``tornado.web.Application`` or an ASGI callable).
        """
        ...

    @abstractmethod
    def run(self, host: str = '0.0.0.0', port: int = 4080, **kwargs: Any) -> None:
        """Start the server (blocking).

        Args:
            host: Bind address.
            port: Bind port.
            **kwargs: Engine-specific options.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shut down the server."""
        ...

    def get_engine_name(self) -> str:
        """Return a human-readable name for this adapter."""
        return self.__class__.__name__

