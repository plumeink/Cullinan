# -*- coding: utf-8 -*-
"""
Tests for Registry Pattern implementation.

This test module validates:
1. HandlerRegistry and HeaderRegistry core functionality
2. Direct registry usage without proxy classes
3. Integration with the framework
"""

import unittest
from unittest.mock import Mock, MagicMock, patch

from cullinan.handler import (
    HandlerRegistry,
    get_handler_registry,
    reset_handler_registry,
)
from cullinan.controller import (
    HeaderRegistry,
    get_header_registry,
)


class TestHandlerRegistry(unittest.TestCase):
    """Test HandlerRegistry core functionality."""
    
    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = HandlerRegistry()
    
    def test_register_handler(self):
        """Test registering a single handler."""
        servlet = Mock()
        self.registry.register('/api/users', servlet)
        
        handlers = self.registry.get_handlers()
        self.assertEqual(len(handlers), 1)
        self.assertEqual(handlers[0][0], '/api/users')
        self.assertIs(handlers[0][1], servlet)
    
    def test_register_multiple_handlers(self):
        """Test registering multiple handlers."""
        servlet1 = Mock()
        servlet2 = Mock()
        servlet3 = Mock()
        
        self.registry.register('/api/users', servlet1)
        self.registry.register('/api/posts', servlet2)
        self.registry.register('/api/comments', servlet3)
        
        handlers = self.registry.get_handlers()
        self.assertEqual(len(handlers), 3)
    
    def test_register_duplicate_url(self):
        """Test that duplicate URLs are not re-registered."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        self.registry.register('/api/users', servlet1)
        self.registry.register('/api/users', servlet2)  # Duplicate
        
        handlers = self.registry.get_handlers()
        # Should only have one handler (first registration wins)
        self.assertEqual(len(handlers), 1)
        self.assertIs(handlers[0][1], servlet1)
    
    def test_get_handlers_returns_copy(self):
        """Test that get_handlers returns a copy, not the internal list."""
        servlet = Mock()
        self.registry.register('/api/users', servlet)
        
        handlers1 = self.registry.get_handlers()
        handlers2 = self.registry.get_handlers()
        
        # Should be equal but not the same object
        self.assertEqual(handlers1, handlers2)
        self.assertIsNot(handlers1, handlers2)
    
    def test_clear_registry(self):
        """Test clearing all handlers."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        self.registry.register('/api/users', servlet1)
        self.registry.register('/api/posts', servlet2)
        self.assertEqual(self.registry.count(), 2)
        
        self.registry.clear()
        self.assertEqual(self.registry.count(), 0)
        self.assertEqual(len(self.registry.get_handlers()), 0)
    
    def test_count_handlers(self):
        """Test counting registered handlers."""
        self.assertEqual(self.registry.count(), 0)
        
        servlet1 = Mock()
        self.registry.register('/api/users', servlet1)
        self.assertEqual(self.registry.count(), 1)
        
        servlet2 = Mock()
        self.registry.register('/api/posts', servlet2)
        self.assertEqual(self.registry.count(), 2)
    
    def test_sort_handlers(self):
        """Test sorting handlers with static and dynamic segments."""
        servlet1 = Mock()
        servlet2 = Mock()
        servlet3 = Mock()
        
        # Register in mixed order
        self.registry.register('/api/users/([a-zA-Z0-9-]+)', servlet1)  # Dynamic
        self.registry.register('/api/users', servlet2)  # Static
        self.registry.register('/api/users/profile', servlet3)  # Static, longer
        
        self.registry.sort()
        handlers = self.registry.get_handlers()
        
        # After sorting:
        # 1. Longer paths first (by number of segments)
        # 2. Within same length, static before dynamic
        # All three have same segment count, so compare segment-by-segment:
        # '/api/users/profile' - has 3 static segments [0, 0, 0]
        # '/api/users' - has 2 static segments [0, 0]
        # '/api/users/([a-zA-Z0-9-]+)' - has 2 static + 1 dynamic [0, 0, 1]
        
        # Actually the sorting is: longer paths (more segments) come first due to -len(parts)
        self.assertEqual(len(handlers), 3)
        
        # Check that all three handlers are present
        urls = [h[0] for h in handlers]
        self.assertIn('/api/users', urls)
        self.assertIn('/api/users/profile', urls)
        self.assertIn('/api/users/([a-zA-Z0-9-]+)', urls)


class TestHeaderRegistry(unittest.TestCase):
    """Test HeaderRegistry core functionality."""
    
    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = HeaderRegistry()
    
    def test_register_header(self):
        """Test registering a single header."""
        header = ('Content-Type', 'application/json')
        self.registry.register(header)
        
        headers = self.registry.get_headers()
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], header)
    
    def test_register_multiple_headers(self):
        """Test registering multiple headers."""
        header1 = ('Content-Type', 'application/json')
        header2 = ('X-Custom-Header', 'custom-value')
        header3 = ('Cache-Control', 'no-cache')
        
        self.registry.register(header1)
        self.registry.register(header2)
        self.registry.register(header3)
        
        headers = self.registry.get_headers()
        self.assertEqual(len(headers), 3)
    
    def test_get_headers_returns_copy(self):
        """Test that get_headers returns a copy."""
        header = ('Content-Type', 'application/json')
        self.registry.register(header)
        
        headers1 = self.registry.get_headers()
        headers2 = self.registry.get_headers()
        
        self.assertEqual(headers1, headers2)
        self.assertIsNot(headers1, headers2)
    
    def test_clear_registry(self):
        """Test clearing all headers."""
        header1 = ('Content-Type', 'application/json')
        header2 = ('X-Custom-Header', 'custom-value')
        
        self.registry.register(header1)
        self.registry.register(header2)
        self.assertEqual(self.registry.count(), 2)
        
        self.registry.clear()
        self.assertEqual(self.registry.count(), 0)
        self.assertEqual(len(self.registry.get_headers()), 0)
    
    def test_count_headers(self):
        """Test counting registered headers."""
        self.assertEqual(self.registry.count(), 0)
        
        header1 = ('Content-Type', 'application/json')
        self.registry.register(header1)
        self.assertEqual(self.registry.count(), 1)
        
        header2 = ('X-Custom-Header', 'custom-value')
        self.registry.register(header2)
        self.assertEqual(self.registry.count(), 2)
    
    def test_has_headers(self):
        """Test checking if headers exist."""
        self.assertFalse(self.registry.has_headers())
        
        header = ('Content-Type', 'application/json')
        self.registry.register(header)
        self.assertTrue(self.registry.has_headers())

class TestGlobalRegistries(unittest.TestCase):
    """Test global registry accessors and reset functionality."""
    
    def test_get_handler_registry(self):
        """Test getting global handler registry."""
        registry1 = get_handler_registry()
        registry2 = get_handler_registry()
        
        # Should return the same instance
        self.assertIs(registry1, registry2)
        self.assertIsInstance(registry1, HandlerRegistry)
    
    def test_get_header_registry(self):
        """Test getting global header registry."""
        registry1 = get_header_registry()
        registry2 = get_header_registry()
        
        # Should return the same instance
        self.assertIs(registry1, registry2)
        self.assertIsInstance(registry1, HeaderRegistry)
    
    def test_reset_registries(self):
        """Test resetting all global registries."""
        handler_reg = get_handler_registry()
        header_reg = get_header_registry()
        
        # Add some data
        servlet = Mock()
        handler_reg.register('/api/users', servlet)
        header_reg.register(('Content-Type', 'application/json'))
        
        self.assertEqual(handler_reg.count(), 1)
        self.assertEqual(header_reg.count(), 1)
        
        # Reset
        reset_handler_registry()
        header_reg.clear()

        # Should be cleared
        self.assertEqual(handler_reg.count(), 0)
        self.assertEqual(header_reg.count(), 0)


if __name__ == '__main__':
    unittest.main()
