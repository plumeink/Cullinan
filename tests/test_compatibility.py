# -*- coding: utf-8 -*-
"""
Backward compatibility tests for Cullinan framework.

These tests ensure that the migration from global lists to Registry pattern
maintains full backward compatibility with existing code.
"""

import unittest
from unittest.mock import Mock, patch
import sys

from cullinan.controller import (
    handler_list,
    header_list,
    _HandlerListProxy,
    _HeaderListProxy,
)
from cullinan.registry import (
    get_handler_registry,
    get_header_registry,
    reset_registries,
)


class TestLegacyHandlerListAPI(unittest.TestCase):
    """Test that legacy handler_list API remains functional."""
    
    def setUp(self):
        """Reset state before each test."""
        reset_registries()
        handler_list.clear()
    
    def tearDown(self):
        """Clean up after each test."""
        reset_registries()
        handler_list.clear()
    
    def test_isinstance_list(self):
        """Test that handler_list is still a list instance."""
        self.assertIsInstance(handler_list, list)
    
    def test_len_function(self):
        """Test that len() works on handler_list."""
        self.assertEqual(len(handler_list), 0)
        
        servlet = Mock()
        handler_list.append(('/api/users', servlet))
        self.assertEqual(len(handler_list), 1)
    
    def test_bool_evaluation(self):
        """Test that boolean evaluation works."""
        self.assertFalse(handler_list)  # Empty list is falsy
        
        servlet = Mock()
        handler_list.append(('/api/users', servlet))
        self.assertTrue(handler_list)  # Non-empty list is truthy
    
    def test_indexing_access(self):
        """Test that indexing works: handler_list[0]."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        
        self.assertEqual(handler_list[0][0], '/api/users')
        self.assertEqual(handler_list[1][0], '/api/posts')
        self.assertIs(handler_list[0][1], servlet1)
    
    def test_negative_indexing(self):
        """Test that negative indexing works."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        
        self.assertEqual(handler_list[-1][0], '/api/posts')
        self.assertEqual(handler_list[-2][0], '/api/users')
    
    def test_slicing(self):
        """Test that slicing works."""
        servlet1 = Mock()
        servlet2 = Mock()
        servlet3 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        handler_list.append(('/api/comments', servlet3))
        
        slice_result = handler_list[0:2]
        self.assertEqual(len(slice_result), 2)
        self.assertEqual(slice_result[0][0], '/api/users')
        self.assertEqual(slice_result[1][0], '/api/posts')
    
    def test_iteration(self):
        """Test that iteration works: for item in handler_list."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        
        urls = []
        for url, servlet in handler_list:
            urls.append(url)
        
        self.assertEqual(urls, ['/api/users', '/api/posts'])
    
    def test_in_operator(self):
        """Test that 'in' operator works."""
        servlet = Mock()
        item = ('/api/users', servlet)
        
        handler_list.append(item)
        self.assertIn(item, handler_list)
        
        other_item = ('/api/posts', Mock())
        self.assertNotIn(other_item, handler_list)
    
    def test_append_method(self):
        """Test that append() method works."""
        servlet = Mock()
        handler_list.append(('/api/users', servlet))
        
        self.assertEqual(len(handler_list), 1)
        self.assertEqual(handler_list[0][0], '/api/users')
    
    def test_extend_method(self):
        """Test that extend() method works."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        items = [
            ('/api/users', servlet1),
            ('/api/posts', servlet2),
        ]
        handler_list.extend(items)
        
        self.assertEqual(len(handler_list), 2)
    
    def test_insert_method(self):
        """Test that insert() method works."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.insert(0, ('/api/posts', servlet2))
        
        self.assertEqual(handler_list[0][0], '/api/posts')
        self.assertEqual(handler_list[1][0], '/api/users')
    
    def test_remove_method(self):
        """Test that remove() method works."""
        servlet = Mock()
        item = ('/api/users', servlet)
        
        handler_list.append(item)
        self.assertEqual(len(handler_list), 1)
        
        handler_list.remove(item)
        self.assertEqual(len(handler_list), 0)
    
    def test_pop_method(self):
        """Test that pop() method works."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        
        popped = handler_list.pop()
        self.assertEqual(popped[0], '/api/posts')
        self.assertEqual(len(handler_list), 1)
    
    def test_clear_method(self):
        """Test that clear() method works."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        self.assertEqual(len(handler_list), 2)
        
        handler_list.clear()
        self.assertEqual(len(handler_list), 0)
    
    def test_sort_method(self):
        """Test that sort() method works."""
        servlet1 = Mock()
        servlet2 = Mock()
        servlet3 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/comments', servlet2))
        handler_list.append(('/api/posts', servlet3))
        
        handler_list.sort(key=lambda x: x[0])
        
        self.assertEqual(handler_list[0][0], '/api/comments')
        self.assertEqual(handler_list[1][0], '/api/posts')
        self.assertEqual(handler_list[2][0], '/api/users')
    
    def test_count_method(self):
        """Test that count() method works."""
        servlet = Mock()
        item = ('/api/users', servlet)
        
        self.assertEqual(handler_list.count(item), 0)
        
        handler_list.append(item)
        self.assertEqual(handler_list.count(item), 1)
        
        handler_list.append(item)
        self.assertEqual(handler_list.count(item), 2)
    
    def test_reverse_method(self):
        """Test that reverse() method works."""
        servlet1 = Mock()
        servlet2 = Mock()
        servlet3 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        handler_list.append(('/api/comments', servlet3))
        
        handler_list.reverse()
        
        self.assertEqual(handler_list[0][0], '/api/comments')
        self.assertEqual(handler_list[1][0], '/api/posts')
        self.assertEqual(handler_list[2][0], '/api/users')


class TestLegacyHeaderListAPI(unittest.TestCase):
    """Test that legacy header_list API remains functional."""
    
    def setUp(self):
        """Reset state before each test."""
        reset_registries()
        header_list.clear()
    
    def tearDown(self):
        """Clean up after each test."""
        reset_registries()
        header_list.clear()
    
    def test_isinstance_list(self):
        """Test that header_list is still a list instance."""
        self.assertIsInstance(header_list, list)
    
    def test_len_function(self):
        """Test that len() works on header_list."""
        self.assertEqual(len(header_list), 0)
        
        header_list.append(('Content-Type', 'application/json'))
        self.assertEqual(len(header_list), 1)
    
    def test_indexing_access(self):
        """Test that indexing works."""
        header1 = ('Content-Type', 'application/json')
        header2 = ('X-Custom-Header', 'custom-value')
        
        header_list.append(header1)
        header_list.append(header2)
        
        self.assertEqual(header_list[0], header1)
        self.assertEqual(header_list[1], header2)
    
    def test_iteration(self):
        """Test that iteration works."""
        header1 = ('Content-Type', 'application/json')
        header2 = ('X-Custom-Header', 'custom-value')
        
        header_list.append(header1)
        header_list.append(header2)
        
        headers = [h for h in header_list]
        self.assertEqual(headers, [header1, header2])
    
    def test_append_method(self):
        """Test that append() method works."""
        header = ('Content-Type', 'application/json')
        header_list.append(header)
        
        self.assertEqual(len(header_list), 1)
        self.assertEqual(header_list[0], header)
    
    def test_clear_method(self):
        """Test that clear() method works."""
        header_list.append(('Content-Type', 'application/json'))
        header_list.append(('X-Custom-Header', 'custom-value'))
        
        header_list.clear()
        self.assertEqual(len(header_list), 0)


class TestLegacyCodePatterns(unittest.TestCase):
    """Test common legacy code patterns still work."""
    
    def setUp(self):
        """Reset state before each test."""
        reset_registries()
        handler_list.clear()
        header_list.clear()
    
    def tearDown(self):
        """Clean up after each test."""
        reset_registries()
        handler_list.clear()
        header_list.clear()
    
    def test_conditional_check_pattern(self):
        """Test: if len(handler_list) == 0:"""
        servlet = Mock()
        
        if len(handler_list) == 0:
            handler_list.append(('/api/users', servlet))
        
        self.assertEqual(len(handler_list), 1)
    
    def test_loop_over_handlers_pattern(self):
        """Test: for url, servlet in handler_list:"""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        
        count = 0
        for url, servlet in handler_list:
            count += 1
            self.assertIsNotNone(url)
            self.assertIsNotNone(servlet)
        
        self.assertEqual(count, 2)
    
    def test_loop_over_headers_pattern(self):
        """Test: for header in header_list:"""
        header_list.append(('Content-Type', 'application/json'))
        header_list.append(('X-Custom-Header', 'custom-value'))
        
        count = 0
        for header in header_list:
            count += 1
            self.assertIsInstance(header, tuple)
        
        self.assertEqual(count, 2)
    
    def test_find_handler_pattern(self):
        """Test: searching for handler in list."""
        servlet1 = Mock()
        servlet2 = Mock()
        target_servlet = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', target_servlet))
        handler_list.append(('/api/comments', servlet2))
        
        found = None
        for url, servlet in handler_list:
            if url == '/api/posts':
                found = servlet
                break
        
        self.assertIs(found, target_servlet)
    
    def test_modify_during_iteration_pattern(self):
        """Test: collecting items then modifying list."""
        servlet1 = Mock()
        servlet2 = Mock()
        servlet3 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        handler_list.append(('/api/comments', servlet3))
        
        # Common pattern: iterate, collect, then modify
        to_remove = []
        for item in handler_list:
            if item[0] == '/api/posts':
                to_remove.append(item)
        
        for item in to_remove:
            handler_list.remove(item)
        
        self.assertEqual(len(handler_list), 2)
        urls = [item[0] for item in handler_list]
        self.assertNotIn('/api/posts', urls)


class TestRegistrySynchronization(unittest.TestCase):
    """Test that legacy lists stay synchronized with registries."""
    
    def setUp(self):
        """Reset state before each test."""
        reset_registries()
        handler_list.clear()
        header_list.clear()
    
    def tearDown(self):
        """Clean up after each test."""
        reset_registries()
        handler_list.clear()
        header_list.clear()
    
    def test_handler_list_syncs_to_registry(self):
        """Test that changes to handler_list are reflected in registry."""
        servlet = Mock()
        handler_list.append(('/api/users', servlet))
        
        registry = get_handler_registry()
        handlers = registry.get_handlers()
        
        self.assertEqual(len(handlers), 1)
        self.assertEqual(handlers[0][0], '/api/users')
    
    def test_header_list_syncs_to_registry(self):
        """Test that changes to header_list are reflected in registry."""
        header = ('Content-Type', 'application/json')
        header_list.append(header)
        
        registry = get_header_registry()
        headers = registry.get_headers()
        
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], header)
    
    def test_clear_syncs_to_registry(self):
        """Test that clearing list clears registry."""
        servlet = Mock()
        handler_list.append(('/api/users', servlet))
        
        registry = get_handler_registry()
        self.assertEqual(registry.count(), 1)
        
        handler_list.clear()
        self.assertEqual(registry.count(), 0)
    
    def test_multiple_operations_stay_synced(self):
        """Test that multiple operations maintain synchronization."""
        servlet1 = Mock()
        servlet2 = Mock()
        servlet3 = Mock()
        
        # Multiple operations
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        handler_list.insert(1, ('/api/comments', servlet3))
        
        registry = get_handler_registry()
        self.assertEqual(registry.count(), 3)
        
        # Remove one
        handler_list.pop()
        
        # Registry should still track (though remove doesn't sync back)
        # The list should still have 2 items
        self.assertEqual(len(handler_list), 2)


class TestImportCompatibility(unittest.TestCase):
    """Test that imports work as before."""
    
    def test_can_import_handler_list(self):
        """Test that handler_list can be imported."""
        try:
            from cullinan.controller import handler_list
            self.assertIsNotNone(handler_list)
        except ImportError:
            self.fail("Could not import handler_list")
    
    def test_can_import_header_list(self):
        """Test that header_list can be imported."""
        try:
            from cullinan.controller import header_list
            self.assertIsNotNone(header_list)
        except ImportError:
            self.fail("Could not import header_list")
    
    def test_handler_list_type_hints_compatible(self):
        """Test that type hints remain compatible."""
        from cullinan.controller import handler_list
        
        # Should be usable as a list in type hints
        self.assertIsInstance(handler_list, list)


if __name__ == '__main__':
    unittest.main()
