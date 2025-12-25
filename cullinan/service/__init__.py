# -*- coding: utf-8 -*-
"""Service module for Cullinan framework.

v0.90: This module now uses the new IoC/DI 2.0 system from cullinan.core.
The API remains backward compatible.

Usage:
    from cullinan.service import service, Service

    @service
    class UserService(Service):  # Service is the base class
        def get_user(self, id: int):
            return {"id": id}

    # With dependency injection
    from cullinan.service import Inject

    @service
    class OrderService(Service):
        user_service: UserService = Inject()
"""

# Re-export decorators from the new system
from cullinan.core.decorators import (
    service,
    Inject,
    InjectByName,
    Lazy,
)

# Keep base class - this is the Service class users inherit from
from .base import Service

# Keep registry exports for backward compatibility
from .registry import (
    ServiceRegistry,
    get_service_registry,
    reset_service_registry,
)

__all__ = [
    # Decorators (new system)
    'service',
    'Inject',
    'InjectByName',
    'Lazy',
    # Base class (for inheritance)
    'Service',
    # Registry (for advanced use)
    'ServiceRegistry',
    'get_service_registry',
    'reset_service_registry',
]
