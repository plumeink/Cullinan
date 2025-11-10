# -*- coding: utf-8 -*-
"""
Tests for the handler module (Registry pattern integration).

This test suite validates the new handler module structure and ensures
backward compatibility with existing tests.
"""

import unittest
from unittest.mock import Mock

from cullinan.handler import (
    HandlerRegistry,
    get_handler_registry,
    reset_handler_registry,
    BaseHandler
)
from cullinan.core import Registry
from cullinan.core.exceptions import RegistryError


class TestHandlerRegistry(unittest.TestCase):
    """Test HandlerRegistry implementation with core.Registry base."""
    
    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = HandlerRegistry()
    
    def test_inherits_from_core_registry(self):
        """Test that HandlerRegistry properly inherits from core.Registry."""
        self.assertIsInstance(self.registry, Registry)
    
    def test_register_handler(self):
        """Test registering a simple handler."""
        handler_class = Mock()
        self.registry.register('/api/users', handler_class)
        
        # Should be retrievable
        result = self.registry.get('/api/users')
        self.assertIsNotNone(result)
        self.assertEqual(result[0], '/api/users')
        self.assertEqual(result[1], handler_class)
    
    def test_register_with_dynamic_segment(self):
        """Test registering handler with dynamic URL segment."""
        handler_class = Mock()
        self.registry.register('/api/posts/([a-zA-Z0-9-]+)', handler_class)
        
        handlers = self.registry.get_handlers()
        self.assertEqual(len(handlers), 1)
        self.assertEqual(handlers[0][0], '/api/posts/([a-zA-Z0-9-]+)')
    
    def test_register_duplicate_url(self):
        """Test that duplicate URLs are handled gracefully."""
        handler1 = Mock()
        handler2 = Mock()
        
        self.registry.register('/api/users', handler1)
        self.registry.register('/api/users', handler2)
        
        # Should only have one registration (first one wins)
        handlers = self.registry.get_handlers()
        self.assertEqual(len(handlers), 1)
        self.assertEqual(handlers[0][1], handler1)
    
    def test_register_invalid_url(self):
        """Test that invalid URLs raise RegistryError."""
        with self.assertRaises(RegistryError):
            self.registry.register('', Mock())
        
        with self.assertRaises(RegistryError):
            self.registry.register(None, Mock())
    
    def test_get_handlers_returns_copy(self):
        """Test that get_handlers returns a copy, not the original list."""
        handler1 = Mock()
        handler2 = Mock()
        
        self.registry.register('/api/users', handler1)
        self.registry.register('/api/posts', handler2)
        
        handlers1 = self.registry.get_handlers()
        handlers2 = self.registry.get_handlers()
        
        # Should be equal but not the same object
        self.assertEqual(handlers1, handlers2)
        self.assertIsNot(handlers1, handlers2)
        
        # Modifying one should not affect the other
        handlers1.append(('/test', Mock()))
        self.assertNotEqual(len(handlers1), len(handlers2))
    
    def test_clear(self):
        """Test clearing all handlers."""
        self.registry.register('/api/users', Mock())
        self.registry.register('/api/posts', Mock())
        self.assertEqual(self.registry.count(), 2)
        
        self.registry.clear()
        self.assertEqual(self.registry.count(), 0)
        self.assertEqual(len(self.registry.get_handlers()), 0)
    
    def test_count(self):
        """Test counting registered handlers."""
        self.assertEqual(self.registry.count(), 0)
        
        self.registry.register('/api/users', Mock())
        self.assertEqual(self.registry.count(), 1)
        
        self.registry.register('/api/posts', Mock())
        self.assertEqual(self.registry.count(), 2)
    
    def test_has(self):
        """Test checking if a URL is registered."""
        self.assertFalse(self.registry.has('/api/users'))
        
        self.registry.register('/api/users', Mock())
        self.assertTrue(self.registry.has('/api/users'))
    
    def test_sort_empty_registry(self):
        """Test sorting an empty registry doesn't raise errors."""
        self.registry.sort()  # Should not raise
        self.assertEqual(self.registry.count(), 0)
    
    def test_sort_static_before_dynamic(self):
        """Test that static routes are prioritized over dynamic routes."""
        self.registry.register('/api/posts/([a-zA-Z0-9-]+)', Mock())
        self.registry.register('/api/posts/latest', Mock())
        self.registry.register('/api/users', Mock())
        
        self.registry.sort()
        handlers = self.registry.get_handlers()
        
        # Static segments should come before dynamic
        urls = [h[0] for h in handlers]
        static_index = urls.index('/api/posts/latest')
        dynamic_index = urls.index('/api/posts/([a-zA-Z0-9-]+)')
        
        self.assertLess(static_index, dynamic_index)
    
    def test_sort_longer_paths_first(self):
        """Test that longer paths are prioritized."""
        self.registry.register('/api', Mock())
        self.registry.register('/api/users', Mock())
        self.registry.register('/api/users/profile', Mock())
        
        self.registry.sort()
        handlers = self.registry.get_handlers()
        
        # Longer paths should come first
        urls = [h[0] for h in handlers]
        self.assertEqual(urls[0], '/api/users/profile')
        self.assertTrue(urls.index('/api/users') < urls.index('/api'))


class TestGlobalHandlerRegistry(unittest.TestCase):
    """Test global handler registry functions."""
    
    def setUp(self):
        """Reset the global registry before each test."""
        reset_handler_registry()
    
    def tearDown(self):
        """Clean up after each test."""
        reset_handler_registry()
    
    def test_get_handler_registry(self):
        """Test getting the global handler registry."""
        registry = get_handler_registry()
        self.assertIsInstance(registry, HandlerRegistry)
    
    def test_global_registry_singleton(self):
        """Test that global registry is a singleton."""
        registry1 = get_handler_registry()
        registry2 = get_handler_registry()
        self.assertIs(registry1, registry2)
    
    def test_reset_handler_registry(self):
        """Test resetting the global handler registry."""
        registry = get_handler_registry()
        registry.register('/api/test', Mock())
        self.assertEqual(registry.count(), 1)
        
        reset_handler_registry()
        self.assertEqual(registry.count(), 0)


class TestBaseHandler(unittest.TestCase):
    """Test BaseHandler class."""
    
    def test_instantiation(self):
        """Test that BaseHandler can be instantiated."""
        handler = BaseHandler()
        self.assertIsNotNone(handler)
    
    def test_lifecycle_methods_exist(self):
        """Test that lifecycle methods exist."""
        handler = BaseHandler()
        self.assertTrue(hasattr(handler, 'on_init'))
        self.assertTrue(hasattr(handler, 'on_destroy'))
        self.assertTrue(callable(handler.on_init))
        self.assertTrue(callable(handler.on_destroy))
    
    def test_lifecycle_methods_default_behavior(self):
        """Test that lifecycle methods don't raise errors by default."""
        handler = BaseHandler()
        handler.on_init()  # Should not raise
        handler.on_destroy()  # Should not raise


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code."""
    
    def setUp(self):
        """Reset registry before each test."""
        reset_handler_registry()
    
    def tearDown(self):
        """Clean up after each test."""
        reset_handler_registry()
    
    def test_handler_registry_exported_from_main(self):
        """Test that handler registry is exported from main cullinan package."""
        # Should be able to import from main package
        from cullinan import HandlerRegistry, get_handler_registry

        # Should be the same class
        from cullinan.handler import HandlerRegistry as DirectImport
        self.assertIs(HandlerRegistry, DirectImport)

        # Should return a valid instance
        registry = get_handler_registry()
        self.assertIsNotNone(registry)
        self.assertIsInstance(registry, HandlerRegistry)


if __name__ == '__main__':
    unittest.main()
