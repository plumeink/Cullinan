# -*- coding: utf-8 -*-
"""Test fixtures for Cullinan testing.

Provides reusable test fixtures and utilities.
"""

import unittest
from typing import Optional

from cullinan.service import reset_service_registry
from .registry import TestRegistry


class ServiceTestCase(unittest.TestCase):
    """Base test case for service testing.
    
    Provides automatic registry cleanup between tests.
    
    Usage:
        class TestMyService(ServiceTestCase):
            def test_something(self):
                # Registry is automatically clean
                pass
    """
    
    def setUp(self):
        """Reset global registry before each test."""
        reset_service_registry()
    
    def tearDown(self):
        """Reset global registry after each test."""
        reset_service_registry()


class IsolatedServiceTestCase(unittest.TestCase):
    """Base test case with isolated registry.
    
    Provides an isolated TestRegistry that doesn't affect the global registry.
    
    Usage:
        class TestMyService(IsolatedServiceTestCase):
            def test_something(self):
                # Use self.registry for all service operations
                self.registry.register('MyService', MyService)
                self.registry.initialize_all()
                instance = self.registry.get_instance('MyService')
    """
    
    def setUp(self):
        """Create isolated registry before each test."""
        self.registry = TestRegistry()
    
    def tearDown(self):
        """Cleanup registry after each test."""
        try:
            self.registry.destroy_all()
        except Exception:
            pass
        self.registry.clear()
