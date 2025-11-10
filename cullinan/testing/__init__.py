# -*- coding: utf-8 -*-
"""Testing utilities for Cullinan framework.

This module provides utilities for testing Cullinan applications:
- MockService: Base class for creating mock services
- TestRegistry: Isolated registry for testing
- Test fixtures and base classes

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
            self.registry.initialize_all()
            
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
