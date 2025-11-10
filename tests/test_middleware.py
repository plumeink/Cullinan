# -*- coding: utf-8 -*-
"""
Tests for the middleware module.

This test suite validates the middleware base classes and chain management.
"""

import unittest
from unittest.mock import Mock, MagicMock

from cullinan.middleware import Middleware, MiddlewareChain


class ConcreteMiddleware(Middleware):
    """Concrete middleware for testing."""
    
    def __init__(self):
        super().__init__()
        self.process_request_called = False
        self.process_response_called = False
        self.init_called = False
        self.destroy_called = False
    
    def process_request(self, request):
        self.process_request_called = True
        return request
    
    def process_response(self, request, response):
        self.process_response_called = True
        return response
    
    def on_init(self):
        self.init_called = True
    
    def on_destroy(self):
        self.destroy_called = True


class TestMiddleware(unittest.TestCase):
    """Test Middleware base class."""
    
    def test_instantiation(self):
        """Test that concrete middleware can be instantiated."""
        middleware = ConcreteMiddleware()
        self.assertIsNotNone(middleware)
    
    def test_lifecycle_methods_exist(self):
        """Test that lifecycle methods exist."""
        middleware = ConcreteMiddleware()
        self.assertTrue(hasattr(middleware, 'on_init'))
        self.assertTrue(hasattr(middleware, 'on_destroy'))
        self.assertTrue(callable(middleware.on_init))
        self.assertTrue(callable(middleware.on_destroy))
    
    def test_process_methods_exist(self):
        """Test that process methods exist."""
        middleware = ConcreteMiddleware()
        self.assertTrue(hasattr(middleware, 'process_request'))
        self.assertTrue(hasattr(middleware, 'process_response'))
        self.assertTrue(callable(middleware.process_request))
        self.assertTrue(callable(middleware.process_response))
    
    def test_process_request(self):
        """Test process_request method."""
        middleware = ConcreteMiddleware()
        request = Mock()
        
        result = middleware.process_request(request)
        
        self.assertTrue(middleware.process_request_called)
        self.assertIs(result, request)
    
    def test_process_response(self):
        """Test process_response method."""
        middleware = ConcreteMiddleware()
        request = Mock()
        response = Mock()
        
        result = middleware.process_response(request, response)
        
        self.assertTrue(middleware.process_response_called)
        self.assertIs(result, response)
    
    def test_on_init(self):
        """Test on_init lifecycle hook."""
        middleware = ConcreteMiddleware()
        middleware.on_init()
        
        self.assertTrue(middleware.init_called)
    
    def test_on_destroy(self):
        """Test on_destroy lifecycle hook."""
        middleware = ConcreteMiddleware()
        middleware.on_destroy()
        
        self.assertTrue(middleware.destroy_called)


class TestMiddlewareChain(unittest.TestCase):
    """Test MiddlewareChain implementation."""
    
    def setUp(self):
        """Create a fresh chain for each test."""
        self.chain = MiddlewareChain()
    
    def test_instantiation(self):
        """Test that chain can be instantiated."""
        self.assertIsNotNone(self.chain)
        self.assertEqual(self.chain.count(), 0)
    
    def test_add_middleware(self):
        """Test adding middleware to chain."""
        middleware = ConcreteMiddleware()
        self.chain.add(middleware)
        
        self.assertEqual(self.chain.count(), 1)
    
    def test_add_multiple_middleware(self):
        """Test adding multiple middleware."""
        middleware1 = ConcreteMiddleware()
        middleware2 = ConcreteMiddleware()
        
        self.chain.add(middleware1)
        self.chain.add(middleware2)
        
        self.assertEqual(self.chain.count(), 2)
    
    def test_add_invalid_middleware(self):
        """Test that adding non-middleware raises TypeError."""
        with self.assertRaises(TypeError):
            self.chain.add("not a middleware")
        
        with self.assertRaises(TypeError):
            self.chain.add(Mock())
    
    def test_process_request_single_middleware(self):
        """Test processing request through single middleware."""
        middleware = ConcreteMiddleware()
        self.chain.add(middleware)
        
        request = Mock()
        result = self.chain.process_request(request)
        
        self.assertTrue(middleware.process_request_called)
        self.assertIs(result, request)
    
    def test_process_request_multiple_middleware(self):
        """Test processing request through multiple middleware in order."""
        order = []
        
        class OrderedMiddleware(Middleware):
            def __init__(self, name):
                super().__init__()
                self.name = name
            
            def process_request(self, request):
                order.append(f"request_{self.name}")
                return request
        
        m1 = OrderedMiddleware("first")
        m2 = OrderedMiddleware("second")
        m3 = OrderedMiddleware("third")
        
        self.chain.add(m1)
        self.chain.add(m2)
        self.chain.add(m3)
        
        self.chain.process_request(Mock())
        
        self.assertEqual(order, ["request_first", "request_second", "request_third"])
    
    def test_process_request_short_circuit(self):
        """Test that returning None short-circuits the chain."""
        order = []
        
        class ShortCircuitMiddleware(Middleware):
            def process_request(self, request):
                order.append("shortcircuit")
                return None
        
        class AfterMiddleware(Middleware):
            def process_request(self, request):
                order.append("after")
                return request
        
        self.chain.add(ShortCircuitMiddleware())
        self.chain.add(AfterMiddleware())
        
        result = self.chain.process_request(Mock())
        
        self.assertIsNone(result)
        self.assertEqual(order, ["shortcircuit"])  # "after" should not be called
    
    def test_process_response_single_middleware(self):
        """Test processing response through single middleware."""
        middleware = ConcreteMiddleware()
        self.chain.add(middleware)
        
        request = Mock()
        response = Mock()
        result = self.chain.process_response(request, response)
        
        self.assertTrue(middleware.process_response_called)
        self.assertIs(result, response)
    
    def test_process_response_reverse_order(self):
        """Test processing response through middleware in reverse order."""
        order = []
        
        class OrderedMiddleware(Middleware):
            def __init__(self, name):
                super().__init__()
                self.name = name
            
            def process_response(self, request, response):
                order.append(f"response_{self.name}")
                return response
        
        m1 = OrderedMiddleware("first")
        m2 = OrderedMiddleware("second")
        m3 = OrderedMiddleware("third")
        
        self.chain.add(m1)
        self.chain.add(m2)
        self.chain.add(m3)
        
        self.chain.process_response(Mock(), Mock())
        
        # Should be in reverse order
        self.assertEqual(order, ["response_third", "response_second", "response_first"])
    
    def test_initialize_all(self):
        """Test initializing all middleware."""
        m1 = ConcreteMiddleware()
        m2 = ConcreteMiddleware()
        
        self.chain.add(m1)
        self.chain.add(m2)
        
        self.chain.initialize_all()
        
        self.assertTrue(m1.init_called)
        self.assertTrue(m2.init_called)
    
    def test_destroy_all(self):
        """Test destroying all middleware."""
        m1 = ConcreteMiddleware()
        m2 = ConcreteMiddleware()
        
        self.chain.add(m1)
        self.chain.add(m2)
        
        self.chain.destroy_all()
        
        self.assertTrue(m1.destroy_called)
        self.assertTrue(m2.destroy_called)
    
    def test_destroy_all_reverse_order(self):
        """Test that destroy is called in reverse order."""
        order = []
        
        class OrderedMiddleware(Middleware):
            def __init__(self, name):
                super().__init__()
                self.name = name
            
            def on_destroy(self):
                order.append(self.name)
        
        m1 = OrderedMiddleware("first")
        m2 = OrderedMiddleware("second")
        m3 = OrderedMiddleware("third")
        
        self.chain.add(m1)
        self.chain.add(m2)
        self.chain.add(m3)
        
        self.chain.destroy_all()
        
        # Should be destroyed in reverse order
        self.assertEqual(order, ["third", "second", "first"])
    
    def test_destroy_all_continues_on_error(self):
        """Test that destroy continues even if one middleware fails."""
        destroyed = []
        
        class FailingMiddleware(Middleware):
            def on_destroy(self):
                raise RuntimeError("Destroy failed")
        
        class TrackingMiddleware(Middleware):
            def __init__(self, name):
                super().__init__()
                self.name = name
            
            def on_destroy(self):
                destroyed.append(self.name)
        
        m1 = TrackingMiddleware("first")
        m2 = FailingMiddleware()
        m3 = TrackingMiddleware("third")
        
        self.chain.add(m1)
        self.chain.add(m2)
        self.chain.add(m3)
        
        self.chain.destroy_all()  # Should not raise
        
        # Both tracking middleware should be destroyed despite failure
        self.assertIn("first", destroyed)
        self.assertIn("third", destroyed)
    
    def test_clear(self):
        """Test clearing the middleware chain."""
        self.chain.add(ConcreteMiddleware())
        self.chain.add(ConcreteMiddleware())
        self.assertEqual(self.chain.count(), 2)
        
        self.chain.clear()
        self.assertEqual(self.chain.count(), 0)
    
    def test_count(self):
        """Test counting middleware in chain."""
        self.assertEqual(self.chain.count(), 0)
        
        self.chain.add(ConcreteMiddleware())
        self.assertEqual(self.chain.count(), 1)
        
        self.chain.add(ConcreteMiddleware())
        self.assertEqual(self.chain.count(), 2)


class TestMiddlewareIntegration(unittest.TestCase):
    """Test middleware integration scenarios."""
    
    def test_complete_request_response_cycle(self):
        """Test complete request/response processing cycle."""
        events = []
        
        class LoggingMiddleware(Middleware):
            def process_request(self, request):
                events.append(f"request_log: {request.path}")
                return request
            
            def process_response(self, request, response):
                events.append(f"response_log: {response.status}")
                return response
        
        class AuthMiddleware(Middleware):
            def process_request(self, request):
                events.append("auth_check")
                request.authenticated = True
                return request
            
            def process_response(self, request, response):
                events.append("auth_cleanup")
                return response
        
        chain = MiddlewareChain()
        chain.add(LoggingMiddleware())
        chain.add(AuthMiddleware())
        
        # Create mock objects
        request = Mock()
        request.path = "/api/test"
        response = Mock()
        response.status = 200
        
        # Process request
        processed_request = chain.process_request(request)
        self.assertIsNotNone(processed_request)
        self.assertTrue(hasattr(processed_request, 'authenticated'))
        
        # Process response
        processed_response = chain.process_response(request, response)
        self.assertIsNotNone(processed_response)
        
        # Verify order of operations
        self.assertEqual(events, [
            "request_log: /api/test",
            "auth_check",
            "auth_cleanup",  # Response in reverse order
            "response_log: 200"
        ])


if __name__ == '__main__':
    unittest.main()
