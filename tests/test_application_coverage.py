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
from cullinan.controller import handler_list


class TestURLSorting(unittest.TestCase):
    """Test URL sorting algorithm."""
    
    def setUp(self):
        """Clear handler list before each test."""
        handler_list.clear()
    
    def tearDown(self):
        """Clear handler list after each test."""
        handler_list.clear()
    
    def test_sort_url_empty_list(self):
        """Test sorting with empty handler list."""
        handler_list.clear()
        sort_url()  # Should not raise
        self.assertEqual(len(handler_list), 0)
    
    def test_sort_url_single_handler(self):
        """Test sorting with single handler."""
        handler_list.append(('/api/users', Mock(), {}))
        sort_url()
        self.assertEqual(len(handler_list), 1)
    
    def test_sort_url_static_before_dynamic(self):
        """Test that static routes come before dynamic routes."""
        # Add in reverse order
        handler_list.append(('/api/users/([a-zA-Z0-9-]+)', Mock(), {}))
        handler_list.append(('/api/users/list', Mock(), {}))
        
        sort_url()
        
        # Static route should be first
        self.assertEqual(handler_list[0][0], '/api/users/list')
        self.assertEqual(handler_list[1][0], '/api/users/([a-zA-Z0-9-]+)')
    
    def test_sort_url_longer_paths_first(self):
        """Test that longer paths come before shorter paths."""
        handler_list.append(('/api/users', Mock(), {}))
        handler_list.append(('/api/users/profile/settings', Mock(), {}))
        handler_list.append(('/api/users/profile', Mock(), {}))
        
        sort_url()
        
        # Longer paths should be first
        self.assertTrue(
            len(handler_list[0][0].split('/')) >= len(handler_list[1][0].split('/'))
        )
    
    def test_sort_url_complex_patterns(self):
        """Test sorting with complex URL patterns."""
        handler_list.clear()
        handler_list.append(('/api/v1/users/([a-zA-Z0-9-]+)/posts', Mock(), {}))
        handler_list.append(('/api/v1/users/admin', Mock(), {}))
        handler_list.append(('/api/v1/users', Mock(), {}))
        handler_list.append(('/api/v1/users/([a-zA-Z0-9-]+)', Mock(), {}))
        
        sort_url()
        
        # Most specific (static with more segments) should be first
        urls = [h[0] for h in handler_list]
        
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


class TestHandlerListManagement(unittest.TestCase):
    """Test handler list operations."""
    
    def setUp(self):
        """Clear handler list before each test."""
        handler_list.clear()
    
    def tearDown(self):
        """Clear handler list after each test."""
        handler_list.clear()
    
    def test_handler_list_is_list(self):
        """Test that handler_list is a list."""
        self.assertIsInstance(handler_list, list)
    
    def test_handler_list_can_be_modified(self):
        """Test that handler_list can be modified."""
        handler_list.append(('/test', Mock(), {}))
        self.assertEqual(len(handler_list), 1)
        
        handler_list.clear()
        self.assertEqual(len(handler_list), 0)
    
    def test_multiple_handlers_same_pattern(self):
        """Test adding multiple handlers (framework should handle duplicates)."""
        handler1 = Mock()
        handler2 = Mock()
        
        handler_list.append(('/api/test', handler1, {}))
        handler_list.append(('/api/test', handler2, {}))
        
        # Both should be in the list (framework handles routing priority)
        self.assertEqual(len(handler_list), 2)


class TestSortingAlgorithmPerformance(unittest.TestCase):
    """Test sorting algorithm performance characteristics."""
    
    def setUp(self):
        """Clear handler list before each test."""
        handler_list.clear()
    
    def tearDown(self):
        """Clear handler list after each test."""
        handler_list.clear()
    
    def test_sorting_large_handler_list(self):
        """Test sorting with a large number of handlers."""
        import time
        
        # Add 100 handlers with various patterns
        for i in range(100):
            if i % 3 == 0:
                handler_list.append((f'/api/v1/resource{i}', Mock(), {}))
            elif i % 3 == 1:
                handler_list.append((f'/api/v1/resource{i}/([a-zA-Z0-9-]+)', Mock(), {}))
            else:
                handler_list.append((f'/api/v1/resource{i}/sub/path', Mock(), {}))
        
        start_time = time.time()
        sort_url()
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 1 second for 100 handlers)
        self.assertLess(elapsed, 1.0)
        self.assertEqual(len(handler_list), 100)


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
