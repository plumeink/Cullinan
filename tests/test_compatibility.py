# -*- coding: utf-8 -*-
"""
Registry pattern integration tests for Cullinan framework.

These tests ensure that the Registry pattern works correctly
throughout the framework after removing the global list proxies.
"""

import unittest
from unittest.mock import Mock, patch
import sys

from cullinan.handler import (
    get_handler_registry,
    reset_handler_registry,
)
from cullinan.controller import (
    get_header_registry,
)


class TestHandlerRegistryAPI(unittest.TestCase):
    """Test that handler registry API works correctly."""
    
    def setUp(self):
        """Reset state before each test."""
        reset_handler_registry()
        get_header_registry().clear()

    def tearDown(self):
        """Clean up after each test."""
        reset_handler_registry()
        get_header_registry().clear()

    def test_handler_registration(self):
        """Test handler registration."""
        registry = get_handler_registry()
        servlet = Mock()
        registry.register('/api/users', servlet)
        
        handlers = registry.get_handlers()
        self.assertEqual(len(handlers), 1)
        self.assertEqual(handlers[0][0], '/api/users')
        self.assertIs(handlers[0][1], servlet)
    
    def test_multiple_handler_registration(self):
        """Test registering multiple handlers."""
        registry = get_handler_registry()
        servlet1 = Mock()
        servlet2 = Mock()
        servlet3 = Mock()
        
        registry.register('/api/users', servlet1)
        registry.register('/api/posts', servlet2)
        registry.register('/api/comments', servlet3)
        
        handlers = registry.get_handlers()
        self.assertEqual(len(handlers), 3)
    
    def test_handler_deduplication(self):
        """Test that duplicate URLs are not re-registered."""
        registry = get_handler_registry()
        servlet1 = Mock()
        servlet2 = Mock()
        
        registry.register('/api/users', servlet1)
        registry.register('/api/users', servlet2)  # Duplicate
        
        handlers = registry.get_handlers()
        # Should only have one handler (first registration wins)
        self.assertEqual(len(handlers), 1)
        self.assertIs(handlers[0][1], servlet1)
    
    def test_handler_clearing(self):
        """Test clearing handlers."""
        registry = get_handler_registry()
        servlet1 = Mock()
        servlet2 = Mock()
        
        registry.register('/api/users', servlet1)
        registry.register('/api/posts', servlet2)
        self.assertEqual(registry.count(), 2)
        
        registry.clear()
        self.assertEqual(registry.count(), 0)
        self.assertEqual(len(registry.get_handlers()), 0)


class TestHeaderRegistryAPI(unittest.TestCase):
    """Test that header registry API works correctly."""
    
    def setUp(self):
        """Reset state before each test."""
        get_header_registry().clear()

    def tearDown(self):
        """Clean up after each test."""
        get_header_registry().clear()

    def test_header_registration(self):
        """Test header registration."""
        registry = get_header_registry()
        header = ('Content-Type', 'application/json')
        registry.register(header)
        
        headers = registry.get_headers()
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], header)
    
    def test_multiple_header_registration(self):
        """Test registering multiple headers."""
        registry = get_header_registry()
        header1 = ('Content-Type', 'application/json')
        header2 = ('X-Custom-Header', 'custom-value')
        header3 = ('Cache-Control', 'no-cache')
        
        registry.register(header1)
        registry.register(header2)
        registry.register(header3)
        
        headers = registry.get_headers()
        self.assertEqual(len(headers), 3)
    
    def test_header_clearing(self):
        """Test clearing headers."""
        registry = get_header_registry()
        header1 = ('Content-Type', 'application/json')
        header2 = ('X-Custom-Header', 'custom-value')
        
        registry.register(header1)
        registry.register(header2)
        self.assertEqual(registry.count(), 2)
        
        registry.clear()
        self.assertEqual(registry.count(), 0)
        self.assertEqual(len(registry.get_headers()), 0)
    
    def test_has_headers(self):
        """Test checking if headers exist."""
        registry = get_header_registry()
        self.assertFalse(registry.has_headers())
        
        header = ('Content-Type', 'application/json')
        registry.register(header)
        self.assertTrue(registry.has_headers())


if __name__ == '__main__':
    unittest.main()
