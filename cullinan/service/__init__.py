# -*- coding: utf-8 -*-
"""Enhanced service module for Cullinan framework.

This module provides an enhanced service layer with:
- Base Service class with lifecycle hooks (on_init, on_destroy)
- ServiceRegistry for managing services with dependency injection
- @service decorator for easy service registration
- Full backward compatibility with simple service usage

Usage:
    # Simple service (backward compatible)
    from cullinan.service import service, Service

    @service
    class EmailService(Service):
        def send_email(self, to, subject, body):
            print(f"Sending to {to}: {subject}")
    
    # Service with dependencies
    @service(dependencies=['EmailService'])
    class UserService(Service):
        def on_init(self):
            self.email = self.dependencies['EmailService']
        
        def create_user(self, name):
            user = {'name': name}
            self.email.send_email(name, "Welcome", "Welcome!")
            return user
"""

from .base import Service
from .decorators import service
from .registry import (
    ServiceRegistry,
    get_service_registry,
    reset_service_registry
)

__all__ = [
    'Service',
    'service',
    'ServiceRegistry',
    'get_service_registry',
    'reset_service_registry',
]
