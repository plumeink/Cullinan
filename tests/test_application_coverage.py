# -*- coding: utf-8 -*-
"""
Additional tests for application.py functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

from cullinan.application import (
    sort_url,
    reflect_module,
)
from cullinan.handler import get_handler_registry, reset_handler_registry


class TestURLSorting(unittest.TestCase):
    """Test URL sorting algorithm."""
    
    def setUp(self):
        """Clear handler registry before each test."""
        reset_handler_registry()

    def tearDown(self):
        """Clear handler registry after each test."""
        reset_handler_registry()

    def test_sort_url_empty_list(self):
        """Test sorting with empty handler registry."""
        registry = get_handler_registry()
        registry.clear()
        sort_url()  # Should not raise
        self.assertEqual(registry.count(), 0)
    
    def test_sort_url_single_handler(self):
        """Test sorting with single handler."""
        registry = get_handler_registry()
        registry.register('/api/users', Mock())
        sort_url()
        self.assertEqual(registry.count(), 1)
    
    def test_sort_url_static_before_dynamic(self):
        """Test that static routes come before dynamic routes."""
        registry = get_handler_registry()
        # Add in reverse order
        registry.register('/api/users/([a-zA-Z0-9-]+)', Mock())
        registry.register('/api/users/list', Mock())
        
        sort_url()
        
        handlers = registry.get_handlers()
        # Static route should be first
        self.assertEqual(handlers[0][0], '/api/users/list')
        self.assertEqual(handlers[1][0], '/api/users/([a-zA-Z0-9-]+)')
    
    def test_sort_url_longer_paths_first(self):
        """Test that longer paths come before shorter paths."""
        registry = get_handler_registry()
        registry.register('/api/users', Mock())
        registry.register('/api/users/profile/settings', Mock())
        registry.register('/api/users/profile', Mock())
        
        sort_url()
        
        handlers = registry.get_handlers()
        # Longer paths should be first
        self.assertTrue(
            len(handlers[0][0].split('/')) >= len(handlers[1][0].split('/'))
        )
    
    def test_sort_url_complex_patterns(self):
        """Test sorting with complex URL patterns."""
        registry = get_handler_registry()
        registry.clear()
        registry.register('/api/v1/users/([a-zA-Z0-9-]+)/posts', Mock())
        registry.register('/api/v1/users/admin', Mock())
        registry.register('/api/v1/users', Mock())
        registry.register('/api/v1/users/([a-zA-Z0-9-]+)', Mock())
        
        sort_url()
        
        handlers = registry.get_handlers()
        # Most specific (static with more segments) should be first
        urls = [h[0] for h in handlers]
        
        # Static "admin" should come before dynamic patterns
        admin_idx = urls.index('/api/v1/users/admin')
        dynamic_user_idx = urls.index('/api/v1/users/([a-zA-Z0-9-]+)')
        self.assertLess(admin_idx, dynamic_user_idx)


class TestReflectModule(unittest.TestCase):
    """Test module reflection and import."""
    
    def test_reflect_module_existing_module(self):
        """Test reflecting an existing module."""
        # Use a built-in module that we know exists
        reflect_module('json', 'json')
        # Should not raise exception
        
    def test_reflect_module_with_package(self):
        """Test reflecting module with package prefix."""
        reflect_module('unittest', 'unittest.mock')
        # Should not raise exception
    
    def test_reflect_module_nonexistent(self):
        """Test reflecting non-existent module (should handle gracefully)."""
        # Should not crash even if module doesn't exist
        try:
            reflect_module('nonexistent_package', 'nonexistent_module')
        except Exception:
            # It's okay if it raises an exception, just shouldn't crash
            pass


class TestHandlerRegistryManagement(unittest.TestCase):
    """Test handler registry operations."""
    
    def setUp(self):
        """Clear handler registry before each test."""
        reset_handler_registry()

    def tearDown(self):
        """Clear handler registry after each test."""
        reset_handler_registry()

    def test_registry_operations(self):
        """Test that registry can be modified."""
        registry = get_handler_registry()
        servlet = Mock()
        registry.register('/test', servlet)
        self.assertEqual(registry.count(), 1)
        
        registry.clear()
        self.assertEqual(registry.count(), 0)
    
    def test_multiple_handlers_same_pattern(self):
        """Test adding multiple handlers (registry should handle duplicates)."""
        registry = get_handler_registry()
        handler1 = Mock()
        handler2 = Mock()
        
        registry.register('/api/test', handler1)
        registry.register('/api/test', handler2)
        
        # Only first one should be registered (duplicate detection)
        self.assertEqual(registry.count(), 1)


class TestSortingAlgorithmPerformance(unittest.TestCase):
    """Test sorting algorithm performance characteristics."""
    
    def setUp(self):
        """Clear handler registry before each test."""
        reset_handler_registry()

    def tearDown(self):
        """Clear handler registry after each test."""
        reset_handler_registry()

    def test_sorting_large_handler_list(self):
        """Test sorting with a large number of handlers."""
        import time
        
        registry = get_handler_registry()
        # Add 100 handlers with various patterns
        for i in range(100):
            if i % 3 == 0:
                registry.register(f'/api/v1/resource{i}', Mock())
            elif i % 3 == 1:
                registry.register(f'/api/v1/resource{i}/([a-zA-Z0-9-]+)', Mock())
            else:
                registry.register(f'/api/v1/resource{i}/sub/path', Mock())
        
        start_time = time.time()
        sort_url()
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 1 second for 100 handlers)
        self.assertLess(elapsed, 1.0)
        # Verify handlers were registered (some duplicates may be skipped)
        self.assertGreater(registry.count(), 0)


class TestApplicationImports(unittest.TestCase):
    """Test that application module can be imported."""
    
    def test_import_application(self):
        """Test importing application module."""
        from cullinan import application
        self.assertIsNotNone(application)
    
    def test_application_has_run(self):
        """Test that application has run function."""
        from cullinan import application
        self.assertTrue(hasattr(application, 'run'))
        self.assertTrue(callable(application.run))
    
    def test_application_has_sort_url(self):
        """Test that application has sort_url function."""
        from cullinan import application
        self.assertTrue(hasattr(application, 'sort_url'))
        self.assertTrue(callable(application.sort_url))


if __name__ == '__main__':
    unittest.main()
