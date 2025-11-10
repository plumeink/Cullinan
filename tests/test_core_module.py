# -*- coding: utf-8 -*-
"""
Tests for the core module (Registry, DependencyInjector, LifecycleManager).

This test suite validates the foundational components of the Cullinan core module.
"""

import unittest
from unittest.mock import Mock, MagicMock, call

from cullinan.core import (
    Registry,
    SimpleRegistry,
    DependencyInjector,
    LifecycleManager,
    LifecycleState,
    RegistryError,
    DependencyResolutionError,
    CircularDependencyError,
    LifecycleError
)


# ============================================================================
# Test Registry
# ============================================================================

class TestSimpleRegistry(unittest.TestCase):
    """Test SimpleRegistry implementation."""
    
    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = SimpleRegistry()
    
    def test_register_and_get(self):
        """Test basic registration and retrieval."""
        item = Mock()
        self.registry.register('test_item', item)
        
        retrieved = self.registry.get('test_item')
        self.assertIs(retrieved, item)
    
    def test_register_with_metadata(self):
        """Test registration with metadata."""
        item = Mock()
        self.registry.register('test_item', item, priority=10, category='test')
        
        metadata = self.registry.get_metadata('test_item')
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['priority'], 10)
        self.assertEqual(metadata['category'], 'test')
    
    def test_register_duplicate(self):
        """Test that duplicate registrations are ignored."""
        item1 = Mock()
        item2 = Mock()
        
        self.registry.register('test_item', item1)
        self.registry.register('test_item', item2)  # Should be ignored
        
        retrieved = self.registry.get('test_item')
        self.assertIs(retrieved, item1)  # First registration wins
    
    def test_has(self):
        """Test checking if item exists."""
        self.assertFalse(self.registry.has('test_item'))
        
        self.registry.register('test_item', Mock())
        self.assertTrue(self.registry.has('test_item'))
    
    def test_list_all(self):
        """Test listing all registered items."""
        item1 = Mock()
        item2 = Mock()
        
        self.registry.register('item1', item1)
        self.registry.register('item2', item2)
        
        all_items = self.registry.list_all()
        self.assertEqual(len(all_items), 2)
        self.assertIn('item1', all_items)
        self.assertIn('item2', all_items)
    
    def test_clear(self):
        """Test clearing all items."""
        self.registry.register('item1', Mock())
        self.registry.register('item2', Mock())
        self.assertEqual(self.registry.count(), 2)
        
        self.registry.clear()
        self.assertEqual(self.registry.count(), 0)
    
    def test_count(self):
        """Test counting registered items."""
        self.assertEqual(self.registry.count(), 0)
        
        self.registry.register('item1', Mock())
        self.assertEqual(self.registry.count(), 1)
        
        self.registry.register('item2', Mock())
        self.assertEqual(self.registry.count(), 2)
    
    def test_unregister(self):
        """Test unregistering items."""
        item = Mock()
        self.registry.register('test_item', item)
        self.assertTrue(self.registry.has('test_item'))
        
        result = self.registry.unregister('test_item')
        self.assertTrue(result)
        self.assertFalse(self.registry.has('test_item'))
    
    def test_unregister_nonexistent(self):
        """Test unregistering item that doesn't exist."""
        result = self.registry.unregister('nonexistent')
        self.assertFalse(result)
    
    def test_validate_name_empty(self):
        """Test that empty names are rejected."""
        with self.assertRaises(RegistryError):
            self.registry.register('', Mock())
    
    def test_validate_name_whitespace(self):
        """Test that whitespace-only names are rejected."""
        with self.assertRaises(RegistryError):
            self.registry.register('   ', Mock())
    
    def test_validate_name_none(self):
        """Test that None names are rejected."""
        with self.assertRaises(RegistryError):
            self.registry.register(None, Mock())


# ============================================================================
# Test DependencyInjector
# ============================================================================

class TestDependencyInjector(unittest.TestCase):
    """Test DependencyInjector implementation."""
    
    def setUp(self):
        """Create a fresh injector for each test."""
        self.injector = DependencyInjector()
    
    def test_register_and_resolve_simple(self):
        """Test basic provider registration and resolution."""
        class ServiceA:
            pass
        
        self.injector.register_provider('service_a', ServiceA)
        instance = self.injector.resolve('service_a')
        
        self.assertIsInstance(instance, ServiceA)
    
    def test_singleton_behavior(self):
        """Test that singletons return the same instance."""
        class ServiceA:
            pass
        
        self.injector.register_provider('service_a', ServiceA, singleton=True)
        
        instance1 = self.injector.resolve('service_a')
        instance2 = self.injector.resolve('service_a')
        
        self.assertIs(instance1, instance2)
    
    def test_non_singleton_behavior(self):
        """Test that non-singletons return different instances."""
        class ServiceA:
            pass
        
        self.injector.register_provider('service_a', ServiceA, singleton=False)
        
        instance1 = self.injector.resolve('service_a')
        instance2 = self.injector.resolve('service_a')
        
        self.assertIsNot(instance1, instance2)
    
    def test_dependency_injection(self):
        """Test dependency injection between services."""
        class ServiceA:
            pass
        
        class ServiceB:
            def __init__(self):
                self.dependencies = {}
        
        self.injector.register_provider('service_a', ServiceA)
        self.injector.register_provider('service_b', ServiceB, dependencies=['service_a'])
        
        instance = self.injector.resolve('service_b')
        
        self.assertIsInstance(instance, ServiceB)
        self.assertIn('service_a', instance.dependencies)
        self.assertIsInstance(instance.dependencies['service_a'], ServiceA)
    
    def test_nested_dependencies(self):
        """Test resolution of nested dependencies."""
        class ServiceA:
            pass
        
        class ServiceB:
            def __init__(self):
                self.dependencies = {}
        
        class ServiceC:
            def __init__(self):
                self.dependencies = {}
        
        self.injector.register_provider('service_a', ServiceA)
        self.injector.register_provider('service_b', ServiceB, dependencies=['service_a'])
        self.injector.register_provider('service_c', ServiceC, dependencies=['service_b'])
        
        instance = self.injector.resolve('service_c')
        
        self.assertIsInstance(instance, ServiceC)
        self.assertIn('service_b', instance.dependencies)
        self.assertIsInstance(instance.dependencies['service_b'], ServiceB)
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        class ServiceA:
            def __init__(self):
                self.dependencies = {}
        
        class ServiceB:
            def __init__(self):
                self.dependencies = {}
        
        self.injector.register_provider('service_a', ServiceA, dependencies=['service_b'])
        self.injector.register_provider('service_b', ServiceB, dependencies=['service_a'])
        
        with self.assertRaises(CircularDependencyError):
            self.injector.resolve('service_a')
    
    def test_missing_dependency(self):
        """Test error when dependency not found."""
        with self.assertRaises(DependencyResolutionError):
            self.injector.resolve('nonexistent')
    
    def test_resolve_all(self):
        """Test resolving multiple dependencies at once."""
        class ServiceA:
            pass
        
        class ServiceB:
            pass
        
        self.injector.register_provider('service_a', ServiceA)
        self.injector.register_provider('service_b', ServiceB)
        
        instances = self.injector.resolve_all(['service_a', 'service_b'])
        
        self.assertEqual(len(instances), 2)
        self.assertIsInstance(instances['service_a'], ServiceA)
        self.assertIsInstance(instances['service_b'], ServiceB)
    
    def test_get_dependency_order(self):
        """Test topological sort for dependency order."""
        self.injector.register_provider('service_a', Mock)
        self.injector.register_provider('service_b', Mock, dependencies=['service_a'])
        self.injector.register_provider('service_c', Mock, dependencies=['service_b'])
        
        order = self.injector.get_dependency_order(['service_a', 'service_b', 'service_c'])
        
        # service_a should come before service_b, service_b before service_c
        self.assertEqual(order.index('service_a'), 0)
        self.assertTrue(order.index('service_b') > order.index('service_a'))
        self.assertTrue(order.index('service_c') > order.index('service_b'))
    
    def test_get_dependency_order_circular(self):
        """Test circular dependency detection in get_dependency_order."""
        self.injector.register_provider('service_a', Mock, dependencies=['service_b'])
        self.injector.register_provider('service_b', Mock, dependencies=['service_a'])
        
        with self.assertRaises(CircularDependencyError):
            self.injector.get_dependency_order(['service_a', 'service_b'])
    
    def test_clear_singletons(self):
        """Test clearing singleton cache."""
        class ServiceA:
            pass
        
        self.injector.register_provider('service_a', ServiceA, singleton=True)
        
        instance1 = self.injector.resolve('service_a')
        self.injector.clear_singletons()
        instance2 = self.injector.resolve('service_a')
        
        self.assertIsNot(instance1, instance2)
    
    def test_has_provider(self):
        """Test checking if provider exists."""
        self.assertFalse(self.injector.has_provider('service_a'))
        
        self.injector.register_provider('service_a', Mock)
        self.assertTrue(self.injector.has_provider('service_a'))
    
    def test_get_dependencies(self):
        """Test getting dependencies for a provider."""
        self.injector.register_provider('service_a', Mock, dependencies=['dep1', 'dep2'])
        
        deps = self.injector.get_dependencies('service_a')
        self.assertEqual(deps, ['dep1', 'dep2'])


# ============================================================================
# Test LifecycleManager
# ============================================================================

class TestLifecycleManager(unittest.TestCase):
    """Test LifecycleManager implementation."""
    
    def setUp(self):
        """Create a fresh lifecycle manager for each test."""
        self.manager = LifecycleManager()
    
    def test_register_component(self):
        """Test component registration."""
        component = Mock()
        self.manager.register_component('comp_a', component)
        
        state = self.manager.get_state('comp_a')
        self.assertEqual(state, LifecycleState.CREATED)
    
    def test_initialize_simple(self):
        """Test simple component initialization."""
        component = Mock()
        component.on_init = Mock()
        
        self.manager.register_component('comp_a', component)
        self.manager.initialize_all()
        
        component.on_init.assert_called_once()
        self.assertEqual(self.manager.get_state('comp_a'), LifecycleState.INITIALIZED)
    
    def test_initialize_with_dependencies(self):
        """Test initialization with dependencies."""
        comp_a = Mock()
        comp_a.on_init = Mock()
        
        comp_b = Mock()
        comp_b.on_init = Mock()
        
        self.manager.register_component('comp_a', comp_a)
        self.manager.register_component('comp_b', comp_b, dependencies=['comp_a'])
        
        self.manager.initialize_all()
        
        # comp_a should be initialized before comp_b
        comp_a.on_init.assert_called_once()
        comp_b.on_init.assert_called_once()
    
    def test_destroy_simple(self):
        """Test simple component destruction."""
        component = Mock()
        component.on_init = Mock()
        component.on_destroy = Mock()
        
        self.manager.register_component('comp_a', component)
        self.manager.initialize_all()
        self.manager.destroy_all()
        
        component.on_destroy.assert_called_once()
        self.assertEqual(self.manager.get_state('comp_a'), LifecycleState.DESTROYED)
    
    def test_destroy_reverse_order(self):
        """Test destruction in reverse order."""
        comp_a = Mock()
        comp_a.on_init = Mock()
        comp_a.on_destroy = Mock()
        
        comp_b = Mock()
        comp_b.on_init = Mock()
        comp_b.on_destroy = Mock()
        
        self.manager.register_component('comp_a', comp_a)
        self.manager.register_component('comp_b', comp_b, dependencies=['comp_a'])
        
        self.manager.initialize_all()
        self.manager.destroy_all()
        
        # comp_b should be destroyed before comp_a
        comp_a.on_destroy.assert_called_once()
        comp_b.on_destroy.assert_called_once()
    
    def test_component_without_lifecycle_methods(self):
        """Test component without on_init/on_destroy methods."""
        component = object()
        
        self.manager.register_component('comp_a', component)
        self.manager.initialize_all()  # Should not raise
        self.manager.destroy_all()  # Should not raise
        
        self.assertEqual(self.manager.get_state('comp_a'), LifecycleState.DESTROYED)
    
    def test_initialization_failure(self):
        """Test handling of initialization failure."""
        component = Mock()
        component.on_init = Mock(side_effect=RuntimeError("Init failed"))
        
        self.manager.register_component('comp_a', component)
        
        with self.assertRaises(LifecycleError):
            self.manager.initialize_all()
        
        # State should be rolled back
        self.assertEqual(self.manager.get_state('comp_a'), LifecycleState.CREATED)
    
    def test_destruction_continues_on_error(self):
        """Test that destruction continues even if one component fails."""
        comp_a = Mock()
        comp_a.on_init = Mock()
        comp_a.on_destroy = Mock(side_effect=RuntimeError("Destroy failed"))
        
        comp_b = Mock()
        comp_b.on_init = Mock()
        comp_b.on_destroy = Mock()
        
        self.manager.register_component('comp_a', comp_a)
        self.manager.register_component('comp_b', comp_b, dependencies=['comp_a'])
        
        self.manager.initialize_all()
        self.manager.destroy_all()  # Should not raise, just log errors
        
        # Both should be called despite comp_b failure
        comp_a.on_destroy.assert_called_once()
        comp_b.on_destroy.assert_called_once()
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        self.manager.register_component('comp_a', Mock(), dependencies=['comp_b'])
        self.manager.register_component('comp_b', Mock(), dependencies=['comp_a'])
        
        with self.assertRaises(LifecycleError):
            self.manager.initialize_all()
    
    def test_clear(self):
        """Test clearing lifecycle manager."""
        self.manager.register_component('comp_a', Mock())
        self.manager.clear()
        
        state = self.manager.get_state('comp_a')
        self.assertIsNone(state)


if __name__ == '__main__':
    unittest.main()
