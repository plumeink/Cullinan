# -*- coding: utf-8 -*-
"""
Additional tests for controller functionality and edge cases.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import json

from cullinan.controller import (
    _get_cached_signature,
    _get_cached_param_mapping,
    url_resolver,
    HttpResponse,
    StatusResponse,
    ResponsePool,
    enable_response_pooling,
    disable_response_pooling,
    get_pooled_response,
    return_pooled_response,
    get_response_pool_stats,
)
from cullinan.exceptions import HandlerError


class TestCachingFunctions(unittest.TestCase):
    """Test function signature and parameter caching."""
    
    def test_signature_cache(self):
        """Test that signatures are cached."""
        def test_func(a, b, c):
            pass
        
        # First call should cache
        sig1 = _get_cached_signature(test_func)
        # Second call should return cached version
        sig2 = _get_cached_signature(test_func)
        
        self.assertIs(sig1, sig2)  # Same object
        self.assertEqual(len(sig1.parameters), 3)
    
    def test_param_mapping_cache(self):
        """Test that parameter mappings are cached."""
        def test_func(self, url_params, query_params, request_body):
            pass
        
        # First call should cache
        params1, needs_body1, needs_headers1 = _get_cached_param_mapping(test_func)
        # Second call should return cached version
        params2, needs_body2, needs_headers2 = _get_cached_param_mapping(test_func)
        
        self.assertEqual(params1, params2)
        self.assertTrue(needs_body1)
        self.assertFalse(needs_headers1)
    
    def test_param_mapping_with_headers(self):
        """Test parameter mapping detection for headers."""
        def test_func(self, headers, url_params):
            pass
        
        params, needs_body, needs_headers = _get_cached_param_mapping(test_func)
        
        self.assertIn('headers', params)
        self.assertFalse(needs_body)
        self.assertTrue(needs_headers)


class TestURLResolver(unittest.TestCase):
    """Test URL pattern resolution."""
    
    def test_simple_url(self):
        """Test simple URL without parameters."""
        url_pattern, param_list = url_resolver('/api/users')
        
        self.assertEqual(url_pattern, '/api/users')
        self.assertEqual(param_list, [])
    
    def test_url_with_parameters(self):
        """Test URL with path parameters."""
        url_pattern, param_list = url_resolver('/api/users/{user_id}/posts/{post_id}')
        
        self.assertIn('([a-zA-Z0-9-]+)', url_pattern)
        self.assertEqual(len(param_list), 2)
        self.assertEqual(param_list[0], 'user_id')
        self.assertEqual(param_list[1], 'post_id')
    
    def test_url_with_trailing_slash(self):
        """Test URL with trailing slash."""
        url_pattern, param_list = url_resolver('/api/users/')
        
        self.assertTrue(url_pattern.endswith('/'))
    
    def test_url_with_mixed_segments(self):
        """Test URL with both static and dynamic segments."""
        url_pattern, param_list = url_resolver('/api/{version}/users/{id}/profile')
        
        self.assertEqual(len(param_list), 2)
        self.assertIn('version', param_list)
        self.assertIn('id', param_list)
    
    def test_url_caching(self):
        """Test that URL patterns are cached."""
        url = '/api/test/{id}/items/{item_id}'
        
        # First call should cache
        result1 = url_resolver(url)
        # Second call should return cached version
        result2 = url_resolver(url)
        
        # Results should be identical (same tuple object due to caching)
        self.assertEqual(result1, result2)
        self.assertEqual(result1[0], result2[0])
        self.assertEqual(result1[1], result2[1])


class TestHttpResponse(unittest.TestCase):
    """Test HttpResponse class."""
    
    def test_default_response(self):
        """Test default response creation."""
        response = HttpResponse()
        
        self.assertEqual(response.get_status(), 200)
        self.assertEqual(response.get_body(), '')
        self.assertEqual(response.get_headers(), [])
    
    def test_set_body_string(self):
        """Test setting body as string."""
        response = HttpResponse()
        response.set_body("Hello, World!")
        
        self.assertEqual(response.get_body(), "Hello, World!")
    
    def test_set_body_dict(self):
        """Test setting body as dictionary (stored as-is)."""
        response = HttpResponse()
        data = {"message": "success", "data": [1, 2, 3]}
        response.set_body(data)
        
        body = response.get_body()
        # HttpResponse stores the body as-is, doesn't auto-serialize
        self.assertIsInstance(body, dict)
        self.assertEqual(body["message"], "success")
    
    def test_set_body_bytes(self):
        """Test setting body as bytes."""
        response = HttpResponse()
        response.set_body(b"Binary data")
        
        self.assertEqual(response.get_body(), b"Binary data")
    
    def test_set_headers(self):
        """Test setting response headers."""
        response = HttpResponse()
        response.add_header("Content-Type", "application/json")
        response.add_header("X-Custom-Header", "value")
        
        headers = response.get_headers()
        self.assertEqual(len(headers), 2)
        self.assertIn(["Content-Type", "application/json"], headers)
    
    def test_set_status(self):
        """Test setting response status."""
        response = HttpResponse()
        response.set_status(404, "Not Found")
        
        self.assertEqual(response.get_status(), 404)
    
    def test_response_slots(self):
        """Test that __slots__ prevents arbitrary attributes."""
        response = HttpResponse()
        
        # Should be able to set defined slots
        response.set_body("test")
        
        # Should not be able to set arbitrary attributes
        with self.assertRaises(AttributeError):
            response.arbitrary_attribute = "value"
    
    def test_response_reset(self):
        """Test that reset() method properly resets response state."""
        response = HttpResponse()
        
        # Modify the response
        response.set_body("Test body")
        response.add_header("Content-Type", "application/json")
        response.add_header("X-Custom", "value")
        response.set_status(404, "Not Found")
        response.set_is_static(True)
        
        # Verify modifications
        self.assertEqual(response.get_body(), "Test body")
        self.assertEqual(len(response.get_headers()), 2)
        self.assertEqual(response.get_status(), 404)
        self.assertTrue(response.get_is_static())
        
        # Reset
        response.reset()
        
        # Verify reset to defaults
        self.assertEqual(response.get_body(), '')
        self.assertEqual(response.get_headers(), [])
        self.assertEqual(response.get_status(), 200)
        self.assertFalse(response.get_is_static())


class TestStatusResponse(unittest.TestCase):
    """Test StatusResponse class."""
    
    def test_status_response_creation(self):
        """Test creating StatusResponse with kwargs."""
        response = StatusResponse(
            body="Error occurred",
            status=400,
            status_msg="Bad Request"
        )
        
        self.assertEqual(response.get_status(), 400)
        self.assertEqual(response.get_body(), "Error occurred")
    
    def test_status_response_with_headers(self):
        """Test StatusResponse with headers."""
        response = StatusResponse(
            body='{"error": "invalid"}',
            headers=[["Content-Type", "application/json"]]
        )
        
        headers = response.get_headers()
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], ["Content-Type", "application/json"])


class TestRequestHandlerErrors(unittest.TestCase):
    """Test error handling in request processing."""
    
    def test_invalid_request_type_error(self):
        """Test that invalid request type raises HandlerError."""
        from cullinan.controller import request_handler
        
        mock_self = Mock()
        mock_func = Mock()
        
        with self.assertRaises(HandlerError) as context:
            request_handler(mock_self, mock_func, (), None, 'invalid_type')
        
        error = context.exception
        self.assertEqual(error.error_code, "INVALID_REQUEST_TYPE")
        self.assertIn("invalid_type", error.details.get("type", ""))


class TestRequestResolver(unittest.TestCase):
    """Test request parameter resolution."""
    
    def test_empty_resolver(self):
        """Test resolver with no parameters."""
        from cullinan.controller import request_resolver
        
        mock_self = Mock()
        url_dict, query_dict, body_dict, file_dict = request_resolver(mock_self)
        
        self.assertIsNone(url_dict)
        self.assertIsNone(query_dict)
        self.assertIsNone(body_dict)
        self.assertIsNone(file_dict)
    
    def test_url_params_resolution(self):
        """Test URL parameter resolution."""
        from cullinan.controller import request_resolver
        
        mock_self = Mock()
        url_dict, _, _, _ = request_resolver(
            mock_self,
            url_param_key_list=['id', 'slug'],
            url_param_value_list=['123', 'test-post']
        )
        
        self.assertIsNotNone(url_dict)
        self.assertEqual(url_dict['id'], '123')
        self.assertEqual(url_dict['slug'], 'test-post')
    
    def test_url_params_with_missing_values(self):
        """Test URL params when values are missing."""
        from cullinan.controller import request_resolver
        
        mock_self = Mock()
        url_dict, _, _, _ = request_resolver(
            mock_self,
            url_param_key_list=['id', 'missing'],
            url_param_value_list=['123']
        )
        
        self.assertEqual(url_dict['id'], '123')
        self.assertIsNone(url_dict['missing'])


class TestHeaderResolver(unittest.TestCase):
    """Test header resolution."""
    
    def test_header_resolution(self):
        """Test resolving required headers."""
        from cullinan.controller import header_resolver
        
        mock_self = Mock()
        mock_self.request.headers.get = Mock(side_effect=lambda x: {
            'Authorization': 'Bearer token123',
            'Content-Type': 'application/json'
        }.get(x))
        
        headers = header_resolver(
            mock_self,
            header_names=['Authorization', 'Content-Type']
        )
        
        self.assertIsNotNone(headers)
        self.assertEqual(headers['Authorization'], 'Bearer token123')
        self.assertEqual(headers['Content-Type'], 'application/json')
    
    def test_empty_header_list(self):
        """Test with no required headers."""
        from cullinan.controller import header_resolver
        
        mock_self = Mock()
        headers = header_resolver(mock_self, header_names=[])
        
        self.assertIsNone(headers)


class TestAccessLogging(unittest.TestCase):
    """Test access log emission."""
    
    @patch.dict('os.environ', {'CULLINAN_ACCESS_LOG_FORMAT': 'json'})
    def test_json_access_log_format(self):
        """Test JSON format access logging."""
        from cullinan.controller import emit_access_log
        
        mock_request = Mock()
        mock_request.method = 'GET'
        mock_request.uri = '/api/users'
        mock_request.remote_ip = '127.0.0.1'
        mock_request.headers = {
            'User-Agent': 'TestClient/1.0',
            'Referer': 'http://example.com'
        }
        
        mock_response = Mock()
        mock_response.get_body.return_value = b'{"status": "ok"}'
        
        # Should not raise exception
        emit_access_log(mock_request, mock_response, 200, 0.123)
    
    @patch.dict('os.environ', {'CULLINAN_ACCESS_LOG_FORMAT': 'combined'})
    def test_combined_access_log_format(self):
        """Test combined (Apache-like) format access logging."""
        from cullinan.controller import emit_access_log
        
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.uri = '/api/data'
        mock_request.remote_ip = '192.168.1.100'
        mock_request.headers = {}
        
        mock_response = Mock()
        mock_response.get_body.return_value = "Response body"
        
        # Should not raise exception
        emit_access_log(mock_request, mock_response, 201, 0.456)


class TestResponsePooling(unittest.TestCase):
    """Test response object pooling functionality."""
    
    def setUp(self):
        """Ensure pooling is disabled before each test."""
        disable_response_pooling()
    
    def tearDown(self):
        """Clean up after tests."""
        disable_response_pooling()
    
    def test_response_pool_creation(self):
        """Test creating a response pool."""
        pool = ResponsePool(size=5)
        stats = pool.get_stats()
        
        self.assertEqual(stats['size'], 5)
        self.assertEqual(stats['available'], 5)
        self.assertEqual(stats['in_use'], 0)
    
    def test_response_pool_acquire_release(self):
        """Test acquiring and releasing responses from pool."""
        pool = ResponsePool(size=3)
        
        # Acquire responses
        resp1 = pool.acquire()
        resp2 = pool.acquire()
        
        self.assertIsInstance(resp1, HttpResponse)
        self.assertIsInstance(resp2, HttpResponse)
        
        stats = pool.get_stats()
        self.assertEqual(stats['available'], 1)
        self.assertEqual(stats['in_use'], 2)
        
        # Release one back
        pool.release(resp1)
        
        stats = pool.get_stats()
        self.assertEqual(stats['available'], 2)
        self.assertEqual(stats['in_use'], 1)
    
    def test_response_pool_overflow(self):
        """Test that pool creates new responses when empty."""
        pool = ResponsePool(size=2)
        
        # Acquire more than pool size
        resp1 = pool.acquire()
        resp2 = pool.acquire()
        resp3 = pool.acquire()  # Should create new instance
        
        self.assertIsInstance(resp1, HttpResponse)
        self.assertIsInstance(resp2, HttpResponse)
        self.assertIsInstance(resp3, HttpResponse)
        
        stats = pool.get_stats()
        self.assertEqual(stats['available'], 0)
    
    def test_response_pool_reset_on_acquire(self):
        """Test that acquired responses are reset."""
        pool = ResponsePool(size=2)
        
        # Get a response, modify it, and return it
        resp = pool.acquire()
        resp.set_body("Test")
        resp.set_status(404)
        pool.release(resp)
        
        # Acquire again - should be reset
        resp2 = pool.acquire()
        self.assertEqual(resp2.get_body(), '')
        self.assertEqual(resp2.get_status(), 200)
    
    def test_enable_disable_pooling(self):
        """Test enabling and disabling pooling."""
        # Initially disabled
        self.assertIsNone(get_response_pool_stats())
        
        # Enable pooling
        enable_response_pooling(pool_size=10)
        stats = get_response_pool_stats()
        self.assertIsNotNone(stats)
        self.assertEqual(stats['size'], 10)
        
        # Disable pooling
        disable_response_pooling()
        self.assertIsNone(get_response_pool_stats())
    
    def test_get_pooled_response_when_disabled(self):
        """Test that get_pooled_response creates new instances when pooling is disabled."""
        disable_response_pooling()
        
        resp1 = get_pooled_response()
        resp2 = get_pooled_response()
        
        self.assertIsInstance(resp1, HttpResponse)
        self.assertIsInstance(resp2, HttpResponse)
        # Should be different instances since pooling is disabled
        self.assertIsNot(resp1, resp2)
    
    def test_get_pooled_response_when_enabled(self):
        """Test that get_pooled_response uses pool when enabled."""
        enable_response_pooling(pool_size=5)
        
        resp = get_pooled_response()
        self.assertIsInstance(resp, HttpResponse)
        
        stats = get_response_pool_stats()
        self.assertEqual(stats['in_use'], 1)
        
        # Return it
        return_pooled_response(resp)
        
        stats = get_response_pool_stats()
        self.assertEqual(stats['in_use'], 0)


if __name__ == '__main__':
    unittest.main()
