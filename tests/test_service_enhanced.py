# -*- coding: utf-8 -*-
"""
Tests for the enhanced service module.

Tests service registration, dependency injection, and lifecycle management.
"""

import unittest
from unittest.mock import Mock, MagicMock, call

from cullinan.service import (
    Service,
    service,
    ServiceRegistry,
    get_service_registry,
    reset_service_registry
)
from cullinan.core.exceptions import DependencyResolutionError


# ============================================================================
# Test Service Base Class
# ============================================================================

class TestServiceBase(unittest.TestCase):
    """Test enhanced Service base class."""
    
    def test_service_initialization(self):
        """Test that Service initializes with empty dependencies."""
        svc = Service()
        self.assertIsInstance(svc.dependencies, dict)
        self.assertEqual(len(svc.dependencies), 0)
    
    def test_lifecycle_methods_exist(self):
        """Test that lifecycle methods exist and are callable."""
        svc = Service()
        self.assertTrue(hasattr(svc, 'on_init'))
        self.assertTrue(callable(svc.on_init))
        self.assertTrue(hasattr(svc, 'on_destroy'))
        self.assertTrue(callable(svc.on_destroy))
    
    def test_lifecycle_methods_default_behavior(self):
        """Test that default lifecycle methods do nothing."""
        svc = Service()
        # Should not raise
        svc.on_init()
        svc.on_destroy()


# ============================================================================
# Test ServiceRegistry
# ============================================================================

class TestServiceRegistry(unittest.TestCase):
    """Test ServiceRegistry functionality."""
    
    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = ServiceRegistry()
    
    def test_register_simple_service(self):
        """Test registering a simple service."""
        class TestService(Service):
            pass
        
        self.registry.register('TestService', TestService)
        
        self.assertTrue(self.registry.has('TestService'))
        retrieved = self.registry.get('TestService')
        self.assertIs(retrieved, TestService)
    
    def test_register_service_with_dependencies(self):
        """Test registering a service with dependencies."""
        class ServiceA(Service):
            pass
        
        class ServiceB(Service):
            pass
        
        self.registry.register('ServiceA', ServiceA)
        self.registry.register('ServiceB', ServiceB, dependencies=['ServiceA'])
        
        self.assertTrue(self.registry.has('ServiceB'))
        metadata = self.registry.get_metadata('ServiceB')
        self.assertIn('dependencies', metadata)
        self.assertEqual(metadata['dependencies'], ['ServiceA'])
    
    def test_get_instance_simple(self):
        """Test getting a service instance."""
        class TestService(Service):
            pass
        
        self.registry.register('TestService', TestService)
        instance = self.registry.get_instance('TestService')
        
        self.assertIsInstance(instance, TestService)
    
    def test_get_instance_singleton(self):
        """Test that get_instance returns same instance (singleton)."""
        class TestService(Service):
            pass
        
        self.registry.register('TestService', TestService)
        
        instance1 = self.registry.get_instance('TestService')
        instance2 = self.registry.get_instance('TestService')
        
        self.assertIs(instance1, instance2)
    
    def test_get_instance_with_dependencies(self):
        """Test getting instance with dependencies injected."""
        class ServiceA(Service):
            pass
        
        class ServiceB(Service):
            pass
        
        self.registry.register('ServiceA', ServiceA)
        self.registry.register('ServiceB', ServiceB, dependencies=['ServiceA'])
        
        instance = self.registry.get_instance('ServiceB')
        
        self.assertIsInstance(instance, ServiceB)
        self.assertIn('ServiceA', instance.dependencies)
        self.assertIsInstance(instance.dependencies['ServiceA'], ServiceA)
    
    def test_initialize_all(self):
        """Test initializing all services."""
        class ServiceA(Service):
            def __init__(self):
                super().__init__()
                self.initialized = False
            
            def on_init(self):
                self.initialized = True
        
        class ServiceB(Service):
            def __init__(self):
                super().__init__()
                self.initialized = False
            
            def on_init(self):
                self.initialized = True
        
        self.registry.register('ServiceA', ServiceA)
        self.registry.register('ServiceB', ServiceB, dependencies=['ServiceA'])
        
        self.registry.initialize_all()
        
        # Both should be initialized
        instance_a = self.registry.get_instance('ServiceA')
        instance_b = self.registry.get_instance('ServiceB')
        
        self.assertTrue(instance_a.initialized)
        self.assertTrue(instance_b.initialized)
    
    def test_destroy_all(self):
        """Test destroying all services."""
        class ServiceA(Service):
            def __init__(self):
                super().__init__()
                self.destroyed = False
            
            def on_destroy(self):
                self.destroyed = True
        
        self.registry.register('ServiceA', ServiceA)
        self.registry.initialize_all()
        
        instance = self.registry.get_instance('ServiceA')
        self.assertFalse(instance.destroyed)
        
        self.registry.destroy_all()
        self.assertTrue(instance.destroyed)
    
    def test_clear(self):
        """Test clearing the registry."""
        class TestService(Service):
            pass
        
        self.registry.register('TestService', TestService)
        self.assertEqual(self.registry.count(), 1)
        
        self.registry.clear()
        self.assertEqual(self.registry.count(), 0)
    
    def test_has_instance(self):
        """Test checking if instance exists."""
        class TestService(Service):
            pass
        
        self.registry.register('TestService', TestService)
        
        self.assertFalse(self.registry.has_instance('TestService'))
        
        self.registry.get_instance('TestService')
        self.assertTrue(self.registry.has_instance('TestService'))
    
    def test_list_instances(self):
        """Test listing all instances."""
        class ServiceA(Service):
            pass
        
        class ServiceB(Service):
            pass
        
        self.registry.register('ServiceA', ServiceA)
        self.registry.register('ServiceB', ServiceB)
        
        self.registry.initialize_all()
        
        instances = self.registry.list_instances()
        self.assertEqual(len(instances), 2)
        self.assertIn('ServiceA', instances)
        self.assertIn('ServiceB', instances)


# ============================================================================
# Test @service Decorator
# ============================================================================

class TestServiceDecorator(unittest.TestCase):
    """Test @service decorator functionality."""
    
    def setUp(self):
        """Reset global registry before each test."""
        reset_service_registry()
    
    def test_decorator_without_args(self):
        """Test @service decorator without arguments."""
        @service
        class TestService(Service):
            pass
        
        registry = get_service_registry()
        self.assertTrue(registry.has('TestService'))
    
    def test_decorator_with_dependencies(self):
        """Test @service decorator with dependencies."""
        @service
        class ServiceA(Service):
            pass
        
        @service(dependencies=['ServiceA'])
        class ServiceB(Service):
            pass
        
        registry = get_service_registry()
        self.assertTrue(registry.has('ServiceA'))
        self.assertTrue(registry.has('ServiceB'))
        
        metadata = registry.get_metadata('ServiceB')
        self.assertEqual(metadata['dependencies'], ['ServiceA'])
    
    def test_decorator_returns_class(self):
        """Test that decorator returns the class unchanged."""
        @service
        class TestService(Service):
            def custom_method(self):
                return "test"
        
        # Class should still be usable
        instance = TestService()
        self.assertEqual(instance.custom_method(), "test")
    
    def test_decorated_service_can_be_instantiated(self):
        """Test that decorated services can be retrieved and used."""
        @service
        class EmailService(Service):
            def send_email(self, to):
                return f"Sent to {to}"
        
        registry = get_service_registry()
        registry.initialize_all()
        
        instance = registry.get_instance('EmailService')
        result = instance.send_email('test@example.com')
        self.assertEqual(result, 'Sent to test@example.com')


# ============================================================================
# Integration Tests
# ============================================================================

class TestServiceIntegration(unittest.TestCase):
    """Integration tests for complete service workflows."""
    
    def setUp(self):
        """Reset global registry before each test."""
        reset_service_registry()
    
    def test_complete_workflow(self):
        """Test complete workflow: register, initialize, use, destroy."""
        @service
        class DatabaseService(Service):
            def __init__(self):
                super().__init__()
                self.connected = False
            
            def on_init(self):
                self.connected = True
            
            def on_destroy(self):
                self.connected = False
            
            def query(self, sql):
                return f"Result: {sql}"
        
        @service(dependencies=['DatabaseService'])
        class UserService(Service):
            def on_init(self):
                self.db = self.dependencies['DatabaseService']
            
            def get_user(self, user_id):
                return self.db.query(f"SELECT * FROM users WHERE id={user_id}")
        
        registry = get_service_registry()
        
        # Initialize
        registry.initialize_all()
        
        # Use services
        user_svc = registry.get_instance('UserService')
        result = user_svc.get_user(123)
        self.assertEqual(result, "Result: SELECT * FROM users WHERE id=123")
        
        # Check database is connected
        db_svc = registry.get_instance('DatabaseService')
        self.assertTrue(db_svc.connected)
        
        # Destroy
        registry.destroy_all()
        self.assertFalse(db_svc.connected)
    
    def test_multiple_dependencies(self):
        """Test service with multiple dependencies."""
        @service
        class LogService(Service):
            def log(self, msg):
                return f"LOG: {msg}"
        
        @service
        class CacheService(Service):
            def get(self, key):
                return None
        
        @service(dependencies=['LogService', 'CacheService'])
        class UserService(Service):
            def on_init(self):
                self.log = self.dependencies['LogService']
                self.cache = self.dependencies['CacheService']
            
            def get_user(self, user_id):
                cached = self.cache.get(user_id)
                self.log.log(f"Getting user {user_id}")
                return cached
        
        registry = get_service_registry()
        registry.initialize_all()
        
        user_svc = registry.get_instance('UserService')
        self.assertIsNotNone(user_svc.log)
        self.assertIsNotNone(user_svc.cache)
    
    def test_backward_compatibility(self):
        """Test backward compatibility with simple service usage."""
        # Old-style service (no lifecycle, no dependencies)
        @service
        class SimpleService(Service):
            def do_something(self):
                return "done"
        
        registry = get_service_registry()
        registry.initialize_all()
        
        instance = registry.get_instance('SimpleService')
        result = instance.do_something()
        self.assertEqual(result, "done")


if __name__ == '__main__':
    unittest.main()
