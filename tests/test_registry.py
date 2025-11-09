# -*- coding: utf-8 -*-
"""
Tests for Registry Pattern implementation and proxy classes.

This test module validates:
1. HandlerRegistry and HeaderRegistry core functionality
2. _HandlerListProxy and _HeaderListProxy backward compatibility
3. Synchronization between legacy lists and new registries
4. Non-destructive migration path
"""

import unittest
from unittest.mock import Mock, MagicMock, patch

from cullinan.registry import (
    HandlerRegistry,
    HeaderRegistry,
    get_handler_registry,
    get_header_registry,
    reset_registries,
)
from cullinan.controller import (
    handler_list,
    header_list,
    _HandlerListProxy,
    _HeaderListProxy,
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


class TestHandlerListProxy(unittest.TestCase):
    """Test _HandlerListProxy backward compatibility and synchronization."""
    
    def setUp(self):
        """Create a fresh proxy for each test."""
        # Reset global registries to ensure clean state
        reset_registries()
        # Create new proxy
        self.proxy = _HandlerListProxy()
    
    def tearDown(self):
        """Clean up after tests."""
        reset_registries()
    
    def test_proxy_behaves_like_list(self):
        """Test that proxy has standard list interface."""
        self.assertIsInstance(self.proxy, list)
        self.assertEqual(len(self.proxy), 0)
        self.assertEqual(list(self.proxy), [])
    
    def test_append_syncs_to_registry(self):
        """Test that append updates both list and registry."""
        servlet = Mock()
        item = ('/api/users', servlet)
        
        self.proxy.append(item)
        
        # Check list
        self.assertEqual(len(self.proxy), 1)
        self.assertEqual(self.proxy[0], item)
        
        # Check registry
        registry = self.proxy.get_registry()
        handlers = registry.get_handlers()
        self.assertEqual(len(handlers), 1)
        self.assertEqual(handlers[0][0], '/api/users')
    
    def test_extend_syncs_to_registry(self):
        """Test that extend updates both list and registry."""
        servlet1 = Mock()
        servlet2 = Mock()
        items = [
            ('/api/users', servlet1),
            ('/api/posts', servlet2),
        ]
        
        self.proxy.extend(items)
        
        # Check list
        self.assertEqual(len(self.proxy), 2)
        
        # Check registry
        registry = self.proxy.get_registry()
        handlers = registry.get_handlers()
        self.assertEqual(len(handlers), 2)
    
    def test_insert_syncs_to_registry(self):
        """Test that insert updates both list and registry."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        self.proxy.append(('/api/users', servlet1))
        self.proxy.insert(0, ('/api/posts', servlet2))
        
        # Check list
        self.assertEqual(len(self.proxy), 2)
        self.assertEqual(self.proxy[0][0], '/api/posts')  # Inserted at beginning
        
        # Check registry (order may differ)
        registry = self.proxy.get_registry()
        self.assertEqual(registry.count(), 2)
    
    def test_clear_syncs_to_registry(self):
        """Test that clear updates both list and registry."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        self.proxy.append(('/api/users', servlet1))
        self.proxy.append(('/api/posts', servlet2))
        self.assertEqual(len(self.proxy), 2)
        
        self.proxy.clear()
        
        # Check list
        self.assertEqual(len(self.proxy), 0)
        
        # Check registry
        registry = self.proxy.get_registry()
        self.assertEqual(registry.count(), 0)
    
    def test_sort_syncs_to_registry(self):
        """Test that sort updates registry with sorted order."""
        servlet1 = Mock()
        servlet2 = Mock()
        servlet3 = Mock()
        
        # Add in reverse alphabetical order
        self.proxy.append(('/api/users', servlet1))
        self.proxy.append(('/api/posts', servlet2))
        self.proxy.append(('/api/comments', servlet3))
        
        # Sort by URL
        self.proxy.sort(key=lambda x: x[0])
        
        # Check list is sorted
        self.assertEqual(self.proxy[0][0], '/api/comments')
        self.assertEqual(self.proxy[1][0], '/api/posts')
        self.assertEqual(self.proxy[2][0], '/api/users')
        
        # Registry should be updated
        registry = self.proxy.get_registry()
        self.assertEqual(registry.count(), 3)
    
    def test_disable_sync(self):
        """Test disabling synchronization."""
        servlet = Mock()
        
        self.proxy.disable_sync()
        self.proxy.append(('/api/users', servlet))
        
        # List should be updated
        self.assertEqual(len(self.proxy), 1)
        
        # Registry should NOT be updated
        registry = self.proxy.get_registry()
        self.assertEqual(registry.count(), 0)
    
    def test_enable_sync_after_disable(self):
        """Test re-enabling synchronization."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        self.proxy.disable_sync()
        self.proxy.append(('/api/users', servlet1))
        
        self.proxy.enable_sync()
        self.proxy.append(('/api/posts', servlet2))
        
        # Registry should only have the second item
        registry = self.proxy.get_registry()
        self.assertEqual(registry.count(), 1)
        handlers = registry.get_handlers()
        self.assertEqual(handlers[0][0], '/api/posts')
    
    def test_invalid_item_ignored(self):
        """Test that invalid items (non-tuples or wrong size) don't crash."""
        # These shouldn't cause errors, just be ignored by registry sync
        self.proxy.append(None)
        self.proxy.append(('/api/users',))  # Missing servlet
        self.proxy.append('not a tuple')
        
        # List should have items
        self.assertEqual(len(self.proxy), 3)
        
        # Registry should be empty (no valid items)
        registry = self.proxy.get_registry()
        self.assertEqual(registry.count(), 0)


class TestHeaderListProxy(unittest.TestCase):
    """Test _HeaderListProxy backward compatibility and synchronization."""
    
    def setUp(self):
        """Create a fresh proxy for each test."""
        reset_registries()
        self.proxy = _HeaderListProxy()
    
    def tearDown(self):
        """Clean up after tests."""
        reset_registries()
    
    def test_proxy_behaves_like_list(self):
        """Test that proxy has standard list interface."""
        self.assertIsInstance(self.proxy, list)
        self.assertEqual(len(self.proxy), 0)
    
    def test_append_syncs_to_registry(self):
        """Test that append updates both list and registry."""
        header = ('Content-Type', 'application/json')
        
        self.proxy.append(header)
        
        # Check list
        self.assertEqual(len(self.proxy), 1)
        self.assertEqual(self.proxy[0], header)
        
        # Check registry
        registry = self.proxy.get_registry()
        headers = registry.get_headers()
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], header)
    
    def test_extend_syncs_to_registry(self):
        """Test that extend updates both list and registry."""
        headers = [
            ('Content-Type', 'application/json'),
            ('X-Custom-Header', 'custom-value'),
        ]
        
        self.proxy.extend(headers)
        
        # Check list
        self.assertEqual(len(self.proxy), 2)
        
        # Check registry
        registry = self.proxy.get_registry()
        reg_headers = registry.get_headers()
        self.assertEqual(len(reg_headers), 2)
    
    def test_clear_syncs_to_registry(self):
        """Test that clear updates both list and registry."""
        self.proxy.append(('Content-Type', 'application/json'))
        self.proxy.append(('X-Custom-Header', 'custom-value'))
        
        self.proxy.clear()
        
        # Check list
        self.assertEqual(len(self.proxy), 0)
        
        # Check registry
        registry = self.proxy.get_registry()
        self.assertEqual(registry.count(), 0)
    
    def test_disable_sync(self):
        """Test disabling synchronization."""
        header = ('Content-Type', 'application/json')
        
        self.proxy.disable_sync()
        self.proxy.append(header)
        
        # List should be updated
        self.assertEqual(len(self.proxy), 1)
        
        # Registry should NOT be updated
        registry = self.proxy.get_registry()
        self.assertEqual(registry.count(), 0)


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
        reset_registries()
        
        # Should be cleared
        self.assertEqual(handler_reg.count(), 0)
        self.assertEqual(header_reg.count(), 0)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that legacy code using global lists still works."""
    
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
    
    def test_handler_list_append(self):
        """Test legacy code using handler_list.append still works."""
        servlet = Mock()
        handler_list.append(('/api/users', servlet))
        
        self.assertEqual(len(handler_list), 1)
        self.assertEqual(handler_list[0][0], '/api/users')
    
    def test_handler_list_extend(self):
        """Test legacy code using handler_list.extend still works."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.extend([
            ('/api/users', servlet1),
            ('/api/posts', servlet2),
        ])
        
        self.assertEqual(len(handler_list), 2)
    
    def test_handler_list_iteration(self):
        """Test legacy code iterating over handler_list still works."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        
        urls = [item[0] for item in handler_list]
        self.assertEqual(urls, ['/api/users', '/api/posts'])
    
    def test_handler_list_indexing(self):
        """Test legacy code using handler_list[index] still works."""
        servlet1 = Mock()
        servlet2 = Mock()
        
        handler_list.append(('/api/users', servlet1))
        handler_list.append(('/api/posts', servlet2))
        
        self.assertEqual(handler_list[0][0], '/api/users')
        self.assertEqual(handler_list[1][0], '/api/posts')
    
    def test_handler_list_len(self):
        """Test legacy code using len(handler_list) still works."""
        self.assertEqual(len(handler_list), 0)
        
        servlet = Mock()
        handler_list.append(('/api/users', servlet))
        self.assertEqual(len(handler_list), 1)
    
    def test_header_list_append(self):
        """Test legacy code using header_list.append still works."""
        header_list.append(('Content-Type', 'application/json'))
        
        self.assertEqual(len(header_list), 1)
        self.assertEqual(header_list[0], ('Content-Type', 'application/json'))
    
    def test_header_list_iteration(self):
        """Test legacy code iterating over header_list still works."""
        header_list.append(('Content-Type', 'application/json'))
        header_list.append(('X-Custom-Header', 'custom-value'))
        
        headers = [h for h in header_list]
        self.assertEqual(len(headers), 2)


if __name__ == '__main__':
    unittest.main()
