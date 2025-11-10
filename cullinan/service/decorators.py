# -*- coding: utf-8 -*-
"""Service decorators for Cullinan framework.

Provides the @service decorator for registering services with optional
dependency injection support.
"""

from typing import Optional, List, Type
import logging

from .registry import get_service_registry
from .base import Service

logger = logging.getLogger(__name__)


def service(cls: Optional[Type[Service]] = None, *, 
            dependencies: Optional[List[str]] = None):
    """Decorator for registering service classes.
    
    Can be used with or without dependencies:
    
    Simple usage (no dependencies):
        @service
        class EmailService(Service):
            pass
    
    With dependencies:
        @service(dependencies=['EmailService'])
        class UserService(Service):
            def on_init(self):
                self.email = self.dependencies['EmailService']
    
    Args:
        cls: Service class (when used without arguments)
        dependencies: List of service names this service depends on
    
    Returns:
        Decorated class (registered with global service registry)
    """
    def decorator(service_class: Type[Service]) -> Type[Service]:
        """Inner decorator that performs the registration."""
        # Register with global registry
        registry = get_service_registry()
        registry.register(
            service_class.__name__,
            service_class,
            dependencies=dependencies
        )
        
        logger.debug(f"Decorated service: {service_class.__name__}")
        return service_class
    
    # Support both @service and @service(dependencies=[...])
    if cls is None:
        # Called with arguments: @service(dependencies=[...])
        return decorator
    else:
        # Called without arguments: @service
        return decorator(cls)
