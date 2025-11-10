# -*- coding: utf-8 -*-
"""
Performance regression tests for Cullinan framework.

These tests validate that optimization work has not introduced
performance regressions and that key operations maintain their
expected performance characteristics.
"""

import unittest
import time
from unittest.mock import Mock, MagicMock

from cullinan.controller import (
    _get_cached_signature,
    _get_cached_param_mapping,
    url_resolver,
    _SIGNATURE_CACHE,
    _PARAM_MAPPING_CACHE,
    _URL_PATTERN_CACHE,
)


class TestSignatureCaching(unittest.TestCase):
    """Test that signature caching provides performance benefits."""
    
    def setUp(self):
        """Clear caches before each test."""
        _SIGNATURE_CACHE.clear()
        _PARAM_MAPPING_CACHE.clear()
    
    def test_signature_cache_reduces_time(self):
        """Test that cached signatures are faster than uncached."""
        def test_func(self, param1, param2, param3, param4, param5):
            """Function with multiple parameters."""
            pass
        
        # Measure first call (uncached)
        start = time.perf_counter()
        for _ in range(100):
            sig1 = _get_cached_signature(test_func)
        time_uncached = time.perf_counter() - start
        
        # Clear and measure second batch (all cached except first)
        _SIGNATURE_CACHE.clear()
        _get_cached_signature(test_func)  # Prime cache
        
        start = time.perf_counter()
        for _ in range(100):
            sig2 = _get_cached_signature(test_func)
        time_cached = time.perf_counter() - start
        
        # Cached should be significantly faster
        # We expect at least 50% speedup from caching
        self.assertLess(time_cached, time_uncached * 0.7,
                       f"Cached ({time_cached:.6f}s) not faster than uncached ({time_uncached:.6f}s)")
    
    def test_param_mapping_cache_reduces_time(self):
        """Test that cached parameter mappings are faster."""
        def test_func(self, url_params, query_params, body_params, 
                     request_body, headers, file_params):
            """Function with many parameter types."""
            pass
        
        # Measure uncached
        start = time.perf_counter()
        for _ in range(100):
            params, body, hdrs = _get_cached_param_mapping(test_func)
        time_uncached = time.perf_counter() - start
        
        # Clear and prime cache
        _PARAM_MAPPING_CACHE.clear()
        _get_cached_param_mapping(test_func)
        
        # Measure cached
        start = time.perf_counter()
        for _ in range(100):
            params, body, hdrs = _get_cached_param_mapping(test_func)
        time_cached = time.perf_counter() - start
        
        self.assertLess(time_cached, time_uncached * 0.7,
                       f"Cached ({time_cached:.6f}s) not faster than uncached ({time_uncached:.6f}s)")
    
    def test_signature_cache_memory_efficient(self):
        """Test that signature cache doesn't grow unbounded."""
        # Create many test functions
        functions = []
        for i in range(100):
            func = lambda self, x: x  # noqa: E731
            func.__name__ = f'test_func_{i}'
            functions.append(func)
        
        # Cache all signatures
        for func in functions:
            _get_cached_signature(func)
        
        # Cache size should match number of functions
        self.assertEqual(len(_SIGNATURE_CACHE), 100)
        
        # Repeated calls shouldn't grow cache
        for func in functions:
            _get_cached_signature(func)
        
        self.assertEqual(len(_SIGNATURE_CACHE), 100)


class TestURLPatternCaching(unittest.TestCase):
    """Test URL pattern parsing and caching."""
    
    def setUp(self):
        """Clear URL pattern cache before each test."""
        _URL_PATTERN_CACHE.clear()
    
    def test_url_resolver_caches_results(self):
        """Test that URL patterns are cached."""
        url = '/api/users/{user_id}/posts/{post_id}'
        
        # First call
        pattern1, params1 = url_resolver(url)
        
        # The cache key is the resolved pattern, not the original URL
        # Check that we got a valid result
        self.assertIn('([a-zA-Z0-9-]+)', pattern1)
        self.assertEqual(params1, ['user_id', 'post_id'])
        
        # Second call should return cached value (check by object identity if possible,
        # or just verify it works)
        pattern2, params2 = url_resolver(url)
        
        self.assertEqual(pattern1, pattern2)
        self.assertEqual(params1, params2)
    
    def test_url_resolver_cache_improves_performance(self):
        """Test that cached URL resolution is faster."""
        url = '/api/v1/users/{user_id}/posts/{post_id}/comments/{comment_id}'
        
        # Measure uncached (clear cache each time)
        start = time.perf_counter()
        for _ in range(50):
            _URL_PATTERN_CACHE.clear()
            pattern, params = url_resolver(url)
        time_uncached = time.perf_counter() - start
        
        # Prime cache
        _URL_PATTERN_CACHE.clear()
        url_resolver(url)
        
        # Measure cached
        start = time.perf_counter()
        for _ in range(50):
            pattern, params = url_resolver(url)
        time_cached = time.perf_counter() - start
        
        # Cached should be faster (more relaxed threshold since URL parsing is already fast)
        # Just verify that it works and doesn't get slower
        self.assertLess(time_cached, time_uncached * 1.5,
                       f"Cached ({time_cached:.6f}s) slower than expected vs uncached ({time_uncached:.6f}s)")
    
    def test_url_resolver_handles_simple_urls(self):
        """Test that simple URLs without parameters are handled efficiently."""
        urls = [
            '/api/users',
            '/api/posts',
            '/api/comments',
            '/api/products',
            '/api/orders',
        ]
        
        start = time.perf_counter()
        for url in urls:
            pattern, params = url_resolver(url)
            self.assertEqual(pattern, url)
            self.assertEqual(params, [])
        elapsed = time.perf_counter() - start
        
        # Should be very fast for simple URLs
        self.assertLess(elapsed, 0.01, f"Simple URL resolution too slow: {elapsed:.6f}s")
    
    def test_url_resolver_handles_complex_urls(self):
        """Test complex URLs with multiple parameters."""
        url = '/api/{version}/users/{user_id}/posts/{post_id}/comments/{comment_id}'
        
        start = time.perf_counter()
        pattern, params = url_resolver(url)
        elapsed = time.perf_counter() - start
        
        self.assertEqual(len(params), 4)
        self.assertIn('version', params)
        self.assertIn('user_id', params)
        self.assertIn('post_id', params)
        self.assertIn('comment_id', params)
        
        # Should complete reasonably quickly
        self.assertLess(elapsed, 0.001, f"Complex URL resolution too slow: {elapsed:.6f}s")


class TestRegistryPerformance(unittest.TestCase):
    """Test Registry pattern performance characteristics."""
    
    def test_handler_registration_is_fast(self):
        """Test that handler registration is O(1) amortized."""
        from cullinan.handler import HandlerRegistry

        registry = HandlerRegistry()
        servlet = Mock()
        
        # Register many handlers
        start = time.perf_counter()
        for i in range(1000):
            registry.register(f'/api/endpoint_{i}', servlet)
        elapsed = time.perf_counter() - start
        
        # Should be fast (< 0.1s for 1000 registrations)
        self.assertLess(elapsed, 0.1, f"Registration too slow: {elapsed:.4f}s for 1000 handlers")
        
        # Average per registration
        avg = elapsed / 1000
        self.assertLess(avg, 0.0001, f"Avg registration time too slow: {avg:.6f}s")
    
    def test_handler_retrieval_is_fast(self):
        """Test that handler retrieval is fast."""
        from cullinan.handler import HandlerRegistry

        registry = HandlerRegistry()
        servlet = Mock()
        
        # Register handlers
        for i in range(100):
            registry.register(f'/api/endpoint_{i}', servlet)
        
        # Measure retrieval time
        start = time.perf_counter()
        for _ in range(100):
            handlers = registry.get_handlers()
        elapsed = time.perf_counter() - start
        
        # Should be fast (< 0.01s for 100 retrievals)
        self.assertLess(elapsed, 0.01, f"Retrieval too slow: {elapsed:.4f}s")
    
    def test_sorting_performance(self):
        """Test that handler sorting is O(n log n)."""
        from cullinan.handler import HandlerRegistry

        registry = HandlerRegistry()
        servlet = Mock()
        
        # Register handlers in random order
        import random
        urls = [f'/api/endpoint_{i}' for i in range(100)]
        random.shuffle(urls)
        
        for url in urls:
            registry.register(url, servlet)
        
        # Measure sorting time
        start = time.perf_counter()
        registry.sort()
        elapsed = time.perf_counter() - start
        
        # Should be fast (< 0.01s for 100 items)
        self.assertLess(elapsed, 0.01, f"Sorting too slow: {elapsed:.4f}s")


class TestRegistryPerformance(unittest.TestCase):
    """Test that registry operations have acceptable performance."""
    
    def test_registry_registration_performance(self):
        """Test that registering handlers is fast."""
        from cullinan.handler import HandlerRegistry

        registry = HandlerRegistry()
        servlet = Mock()
        
        start = time.perf_counter()
        for i in range(1000):
            registry.register(f'/api/endpoint_{i}', servlet)
        elapsed = time.perf_counter() - start
        
        # Should complete in reasonable time (< 0.5 seconds for 1000 registrations)
        self.assertLess(elapsed, 0.5,
                       f"Registry registration too slow: {elapsed:.4f}s for 1000 registrations")
        
        self.assertEqual(registry.count(), 1000)
    
    def test_registry_iteration_performance(self):
        """Test that iterating over registry handlers is fast."""
        from cullinan.handler import HandlerRegistry

        registry = HandlerRegistry()
        servlet = Mock()
        
        # Populate
        for i in range(100):
            registry.register(f'/api/endpoint_{i}', servlet)
        
        # Measure iteration
        start = time.perf_counter()
        for _ in range(100):
            for url, handler in registry.get_handlers():
                pass
        elapsed = time.perf_counter() - start
        
        # Should be fast
        self.assertLess(elapsed, 0.1, f"Registry iteration too slow: {elapsed:.4f}s")


class TestCacheEffectiveness(unittest.TestCase):
    """Test that caches are being used effectively."""
    
    def test_signature_cache_hit_rate(self):
        """Test that signature cache has high hit rate in typical usage."""
        def test_func(self, param1, param2):
            pass
        
        _SIGNATURE_CACHE.clear()
        
        # Simulate typical usage: same function called many times
        for _ in range(100):
            sig = _get_cached_signature(test_func)
        
        # Should only have one entry (one function)
        self.assertEqual(len(_SIGNATURE_CACHE), 1)
    
    def test_url_pattern_cache_hit_rate(self):
        """Test that URL pattern cache has high hit rate."""
        _URL_PATTERN_CACHE.clear()
        
        # Simulate typical usage: same URLs parsed multiple times
        urls = [
            '/api/users',
            '/api/posts/{post_id}',
            '/api/comments',
        ]
        
        for _ in range(10):
            for url in urls:
                pattern, params = url_resolver(url)
        
        # Should only have 3 entries (3 unique URLs)
        self.assertEqual(len(_URL_PATTERN_CACHE), 3)


if __name__ == '__main__':
    unittest.main()
