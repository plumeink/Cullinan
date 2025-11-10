# -*- coding: utf-8 -*-
"""
Test to ensure service lifecycle hooks (on_init and on_destroy) are properly called.

This test specifically validates the fix for the issue where lifecycle hooks
were not being invoked when services were accessed.
"""

import unittest
from cullinan.service import Service, service, ServiceRegistry, get_service_registry, reset_service_registry


class TestServiceLifecycleHooksCalled(unittest.TestCase):
    """Test that service lifecycle hooks are properly called."""
    
    def setUp(self):
        """Reset global registry before each test."""
        reset_service_registry()
    
    def test_on_init_called_on_get_instance(self):
        """Test that on_init() is called when using get_instance()."""
        init_called = []
        
        @service
        class TestService(Service):
            def on_init(self):
                init_called.append(True)
        
        registry = get_service_registry()
        instance = registry.get_instance('TestService')
        
        self.assertEqual(len(init_called), 1, "on_init should be called exactly once")
        self.assertIsInstance(instance, TestService)
    
    def test_on_init_called_on_initialize_all(self):
        """Test that on_init() is called when using initialize_all()."""
        init_called = []
        
        @service
        class TestService(Service):
            def on_init(self):
                init_called.append(True)
        
        registry = get_service_registry()
        registry.initialize_all()
        
        self.assertEqual(len(init_called), 1, "on_init should be called exactly once")
    
    def test_on_init_receives_dependencies(self):
        """Test that dependencies are available in on_init()."""
        @service
        class ServiceA(Service):
            def __init__(self):
                super().__init__()
                self.value = 'A'
        
        @service(dependencies=['ServiceA'])
        class ServiceB(Service):
            def __init__(self):
                super().__init__()
                self.dependency_value = None
            
            def on_init(self):
                # Dependencies should be available in on_init
                self.dependency_value = self.dependencies['ServiceA'].value
        
        registry = get_service_registry()
        registry.initialize_all()
        
        instance_b = registry.get_instance('ServiceB')
        self.assertEqual(instance_b.dependency_value, 'A', 
                        "Dependencies should be accessible in on_init()")
    
    def test_on_init_not_called_twice(self):
        """Test that on_init() is only called once, even with multiple get_instance() calls."""
        init_count = []
        
        @service
        class TestService(Service):
            def on_init(self):
                init_count.append(1)
        
        registry = get_service_registry()
        
        # Call get_instance multiple times
        registry.get_instance('TestService')
        registry.get_instance('TestService')
        registry.get_instance('TestService')
        
        self.assertEqual(len(init_count), 1, "on_init should only be called once")
    
    def test_on_destroy_called_on_destroy_all(self):
        """Test that on_destroy() is called when using destroy_all()."""
        destroy_called = []
        
        @service
        class TestService(Service):
            def on_destroy(self):
                destroy_called.append(True)
        
        registry = get_service_registry()
        registry.initialize_all()
        registry.destroy_all()
        
        self.assertEqual(len(destroy_called), 1, "on_destroy should be called exactly once")
    
    def test_on_destroy_called_in_reverse_order(self):
        """Test that on_destroy() is called in reverse dependency order."""
        destroy_order = []
        
        @service
        class ServiceA(Service):
            def on_destroy(self):
                destroy_order.append('A')
        
        @service(dependencies=['ServiceA'])
        class ServiceB(Service):
            def on_destroy(self):
                destroy_order.append('B')
        
        registry = get_service_registry()
        registry.initialize_all()
        registry.destroy_all()
        
        # B depends on A, so B should be destroyed first
        self.assertEqual(destroy_order, ['B', 'A'], 
                        "Services should be destroyed in reverse dependency order")
    
    def test_lifecycle_hooks_with_state_changes(self):
        """Test that lifecycle hooks properly manage state."""
        @service
        class DatabaseService(Service):
            def __init__(self):
                super().__init__()
                self.connected = False
                self.connection = None
            
            def on_init(self):
                self.connected = True
                self.connection = "DB_CONNECTION"
            
            def on_destroy(self):
                self.connected = False
                self.connection = None
        
        registry = get_service_registry()
        registry.initialize_all()
        
        db_service = registry.get_instance('DatabaseService')
        self.assertTrue(db_service.connected, "Service should be connected after on_init")
        self.assertEqual(db_service.connection, "DB_CONNECTION")
        
        registry.destroy_all()
        self.assertFalse(db_service.connected, "Service should be disconnected after on_destroy")
        self.assertIsNone(db_service.connection)
    
    def test_get_returns_class_not_instance(self):
        """Test that get() returns the class, not an instance (for clarity)."""
        @service
        class TestService(Service):
            pass
        
        registry = get_service_registry()
        
        # get() should return the class
        service_class = registry.get('TestService')
        self.assertEqual(service_class, TestService, "get() should return the class")
        self.assertIsNot(service_class, TestService(), "get() should not return an instance")
    
    def test_manual_instantiation_does_not_call_on_init(self):
        """Test that manually instantiating a service class doesn't call on_init()."""
        init_called = []
        
        @service
        class TestService(Service):
            def on_init(self):
                init_called.append(True)
        
        registry = get_service_registry()
        
        # Get the class and manually instantiate
        service_class = registry.get('TestService')
        manual_instance = service_class()
        
        # on_init should NOT have been called
        self.assertEqual(len(init_called), 0, 
                        "on_init should not be called for manual instantiation")
        
        # Now get the proper instance through the registry
        registry_instance = registry.get_instance('TestService')
        
        # on_init should have been called exactly once
        self.assertEqual(len(init_called), 1, 
                        "on_init should be called when using get_instance()")


class TestServiceRegistryInstance(unittest.TestCase):
    """Test ServiceRegistry with isolated instances."""
    
    def test_isolated_registry_lifecycle(self):
        """Test lifecycle hooks in an isolated registry."""
        init_called = []
        destroy_called = []
        
        class TestService(Service):
            def on_init(self):
                init_called.append(True)
            
            def on_destroy(self):
                destroy_called.append(True)
        
        # Create isolated registry
        registry = ServiceRegistry()
        registry.register('TestService', TestService)
        
        # Initialize
        registry.initialize_all()
        self.assertEqual(len(init_called), 1)
        
        # Destroy
        registry.destroy_all()
        self.assertEqual(len(destroy_called), 1)


if __name__ == '__main__':
    unittest.main()
