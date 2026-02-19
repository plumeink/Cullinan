# -*- coding: utf-8 -*-
"""Testing utilities for Cullinan framework.

This module provides utilities for testing Cullinan applications:
- MockService: Base class for creating mock services
- TestRegistry: Isolated registry for testing
- Test fixtures and base classes

Lifecycle Management:
    All components use Duck Typing for lifecycle - NO base class inheritance required!
    Just define the lifecycle methods you need:
    - on_post_construct(): Called after instance creation
    - on_startup(): Called during application startup
    - on_shutdown(): Called during application shutdown
    - on_pre_destroy(): Called before destruction

Usage:
    from cullinan.testing import MockService, TestRegistry, IsolatedServiceTestCase
    
    class MockEmailService(MockService):
        def send_email(self, to, subject, body):
            self.record_call('send_email', to=to, subject=subject, body=body)
    
    class TestUserService(IsolatedServiceTestCase):
        def test_create_user(self):
            # Use isolated registry
            self.registry.register('EmailService', MockEmailService)
            self.registry.register('UserService', UserService, dependencies=['EmailService'])

            # Get instance - lifecycle hooks called via Duck Typing
            user_service = self.registry.get_instance('UserService')

            # Test...
"""

from .mocks import MockService
from .registry import TestRegistry
from .fixtures import ServiceTestCase, IsolatedServiceTestCase

__all__ = [
    'MockService',
    'TestRegistry',
    'ServiceTestCase',
    'IsolatedServiceTestCase',
]
