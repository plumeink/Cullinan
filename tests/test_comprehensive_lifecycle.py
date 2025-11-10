"""Comprehensive test for all lifecycle hooks across components"""
import unittest
from cullinan.service import Service, service, get_service_registry, reset_service_registry
from cullinan.handler import get_handler_registry, reset_handler_registry
from cullinan.handler.base import BaseHandler
from cullinan.middleware.base import Middleware, MiddlewareChain


class TestServiceLifecycle(unittest.TestCase):
    """Test service lifecycle hooks comprehensively."""
    
    def setUp(self):
        reset_service_registry()
    
    def test_lazy_initialization(self):
        """Test that get_instance() calls on_init()."""
        @service
        class TestService(Service):
            def __init__(self):
                super().__init__()
                self.init_called = False
            
            def on_init(self):
                self.init_called = True
        
        registry = get_service_registry()
        instance = registry.get_instance('TestService')
        
        self.assertTrue(instance.init_called)
    
    def test_eager_initialization(self):
        """Test that initialize_all() calls on_init()."""
        @service
        class TestService(Service):
            def __init__(self):
                super().__init__()
                self.init_called = False
            
            def on_init(self):
                self.init_called = True
        
        registry = get_service_registry()
        registry.initialize_all()
        instance = registry.get_instance('TestService')
        
        self.assertTrue(instance.init_called)
    
    def test_no_double_initialization(self):
        """Test that on_init() is only called once."""
        call_count = [0]
        
        @service
        class TestService(Service):
            def on_init(self):
                call_count[0] += 1
        
        registry = get_service_registry()
        registry.initialize_all()
        registry.get_instance('TestService')
        registry.get_instance('TestService')
        
        self.assertEqual(call_count[0], 1)
    
    def test_destroy_calls_on_destroy(self):
        """Test that destroy_all() calls on_destroy()."""
        @service
        class TestService(Service):
            def __init__(self):
                super().__init__()
                self.destroyed = False
            
            def on_destroy(self):
                self.destroyed = True
        
        registry = get_service_registry()
        registry.initialize_all()
        instance = registry.get_instance('TestService')
        
        registry.destroy_all()
        
        self.assertTrue(instance.destroyed)


class TestHandlerLifecycle(unittest.TestCase):
    """Test handler lifecycle hooks."""
    
    def setUp(self):
        reset_handler_registry()
    
    def test_handler_on_init_called(self):
        """Test that handler on_init() is called on registration."""
        class TestHandler(BaseHandler):
            def __init__(self):
                super().__init__()
                self.init_called = False
            
            def on_init(self):
                self.init_called = True
        
        registry = get_handler_registry()
        handler_instance = TestHandler()
        registry.register('/test', handler_instance)
        
        self.assertTrue(handler_instance.init_called)
    
    def test_handler_on_destroy_called(self):
        """Test that handler on_destroy() is called."""
        class TestHandler(BaseHandler):
            def __init__(self):
                super().__init__()
                self.destroyed = False
            
            def on_destroy(self):
                self.destroyed = True
        
        registry = get_handler_registry()
        handler_instance = TestHandler()
        registry.register('/test', handler_instance)
        
        registry.destroy_all()
        
        self.assertTrue(handler_instance.destroyed)


class TestMiddlewareLifecycle(unittest.TestCase):
    """Test middleware lifecycle hooks."""
    
    def test_middleware_on_init_called(self):
        """Test that middleware on_init() is called."""
        class TestMiddleware(Middleware):
            def __init__(self):
                super().__init__()
                self.init_called = False
            
            def on_init(self):
                self.init_called = True
        
        chain = MiddlewareChain()
        middleware = TestMiddleware()
        chain.add(middleware)
        chain.initialize_all()
        
        self.assertTrue(middleware.init_called)
    
    def test_middleware_on_destroy_called(self):
        """Test that middleware on_destroy() is called."""
        class TestMiddleware(Middleware):
            def __init__(self):
                super().__init__()
                self.destroyed = False
            
            def on_destroy(self):
                self.destroyed = True
        
        chain = MiddlewareChain()
        middleware = TestMiddleware()
        chain.add(middleware)
        chain.initialize_all()
        chain.destroy_all()
        
        self.assertTrue(middleware.destroyed)


if __name__ == '__main__':
    unittest.main()
