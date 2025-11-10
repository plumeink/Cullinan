# -*- coding: utf-8 -*-
"""
Tests for async support in Cullinan framework.

Tests async lifecycle methods, async service initialization, and async component management.
"""

import unittest
import asyncio

from cullinan import Service, service, ServiceRegistry
from cullinan.core import LifecycleManager, LifecycleState


# ============================================================================
# Test Async Lifecycle Manager
# ============================================================================

class TestAsyncLifecycleManager(unittest.TestCase):
    """Test async lifecycle management."""
    
    def setUp(self):
        """Create a fresh lifecycle manager for each test."""
        self.manager = LifecycleManager()
    
    def test_async_init_component(self):
        """Test async component initialization."""
        
        class AsyncComponent:
            def __init__(self):
                self.initialized = False
            
            async def on_init(self):
                await asyncio.sleep(0.001)  # Simulate async work
                self.initialized = True
        
        component = AsyncComponent()
        self.manager.register_component('async_comp', component)
        
        # Run async initialization
        asyncio.run(self.manager.initialize_all_async())
        
        self.assertTrue(component.initialized)
        self.assertEqual(self.manager.get_state('async_comp'), LifecycleState.INITIALIZED)
    
    def test_async_destroy_component(self):
        """Test async component destruction."""
        
        class AsyncComponent:
            def __init__(self):
                self.destroyed = False
            
            def on_init(self):
                pass
            
            async def on_destroy(self):
                await asyncio.sleep(0.001)  # Simulate async cleanup
                self.destroyed = True
        
        component = AsyncComponent()
        self.manager.register_component('async_comp', component)
        
        # Initialize and then destroy
        asyncio.run(self.manager.initialize_all_async())
        asyncio.run(self.manager.destroy_all_async())
        
        self.assertTrue(component.destroyed)
        self.assertEqual(self.manager.get_state('async_comp'), LifecycleState.DESTROYED)
    
    def test_mixed_sync_async_init(self):
        """Test that both sync and async components can be initialized together."""
        
        class SyncComponent:
            def __init__(self):
                self.initialized = False
            
            def on_init(self):
                self.initialized = True
        
        class AsyncComponent:
            def __init__(self):
                self.initialized = False
            
            async def on_init(self):
                await asyncio.sleep(0.001)
                self.initialized = True
        
        sync_comp = SyncComponent()
        async_comp = AsyncComponent()
        
        self.manager.register_component('sync_comp', sync_comp)
        self.manager.register_component('async_comp', async_comp)
        
        # Initialize all with async version
        asyncio.run(self.manager.initialize_all_async())
        
        self.assertTrue(sync_comp.initialized)
        self.assertTrue(async_comp.initialized)
    
    def test_async_init_with_dependencies(self):
        """Test async initialization respects dependency order."""
        
        init_order = []
        
        class ComponentA:
            async def on_init(self):
                await asyncio.sleep(0.001)
                init_order.append('A')
        
        class ComponentB:
            async def on_init(self):
                await asyncio.sleep(0.001)
                init_order.append('B')
        
        comp_a = ComponentA()
        comp_b = ComponentB()
        
        self.manager.register_component('comp_a', comp_a, dependencies=[])
        self.manager.register_component('comp_b', comp_b, dependencies=['comp_a'])
        
        asyncio.run(self.manager.initialize_all_async())
        
        # B should be initialized after A
        self.assertEqual(init_order, ['A', 'B'])


# ============================================================================
# Test Async Service Layer
# ============================================================================

class TestAsyncServiceLayer(unittest.TestCase):
    """Test async service functionality."""
    
    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = ServiceRegistry()
    
    def test_async_service_init(self):
        """Test service with async on_init."""
        
        class AsyncService(Service):
            def __init__(self):
                super().__init__()
                self.connected = False
            
            async def on_init(self):
                await asyncio.sleep(0.001)  # Simulate async connection
                self.connected = True
        
        self.registry.register('AsyncService', AsyncService)
        asyncio.run(self.registry.initialize_all_async())
        
        instance = self.registry.get_instance('AsyncService')
        self.assertIsNotNone(instance)
        self.assertTrue(instance.connected)
    
    def test_async_service_destroy(self):
        """Test service with async on_destroy."""
        
        class AsyncService(Service):
            def __init__(self):
                super().__init__()
                self.disconnected = False
            
            def on_init(self):
                pass
            
            async def on_destroy(self):
                await asyncio.sleep(0.001)  # Simulate async cleanup
                self.disconnected = True
        
        self.registry.register('AsyncService', AsyncService)
        asyncio.run(self.registry.initialize_all_async())
        
        instance = self.registry.get_instance('AsyncService')
        asyncio.run(self.registry.destroy_all_async())
        
        self.assertTrue(instance.disconnected)
    
    def test_async_service_with_dependencies(self):
        """Test async service with dependencies."""
        
        class DatabaseService(Service):
            def __init__(self):
                super().__init__()
                self.connected = False
            
            async def on_init(self):
                await asyncio.sleep(0.001)
                self.connected = True
        
        class UserService(Service):
            def __init__(self):
                super().__init__()
                self.initialized = False
            
            async def on_init(self):
                db = self.dependencies.get('DatabaseService')
                self.initialized = db.connected
        
        self.registry.register('DatabaseService', DatabaseService)
        self.registry.register('UserService', UserService, dependencies=['DatabaseService'])
        
        asyncio.run(self.registry.initialize_all_async())
        
        user_service = self.registry.get_instance('UserService')
        self.assertTrue(user_service.initialized)
    
    def test_sync_init_with_async_service_warning(self):
        """Test that sync initialization of async service logs warning."""
        
        class AsyncService(Service):
            def __init__(self):
                super().__init__()
                self.initialized = False
            
            async def on_init(self):
                await asyncio.sleep(0.001)
                self.initialized = True
        
        self.registry.register('AsyncService', AsyncService)
        
        # Use sync initialization (should log warning but not crash)
        with self.assertLogs('cullinan.service.registry', level='WARNING') as cm:
            self.registry.initialize_all()
        
        # Should have warning about async method
        self.assertTrue(any('async' in msg.lower() for msg in cm.output))
        
        # Service should still be registered but not properly initialized
        instance = self.registry.get_instance('AsyncService')
        self.assertFalse(instance.initialized)  # Async work didn't complete


# ============================================================================
# Test Real-World Async Scenarios
# ============================================================================

class TestAsyncScenarios(unittest.TestCase):
    """Test realistic async usage scenarios."""
    
    def test_database_connection_pool(self):
        """Test async database connection pool scenario."""
        
        class DatabasePool(Service):
            def __init__(self):
                super().__init__()
                self.pool = None
                self.connections = []
            
            async def on_init(self):
                # Simulate creating connection pool
                await asyncio.sleep(0.002)
                self.connections = ['conn1', 'conn2', 'conn3']
                self.pool = 'initialized'
            
            async def on_destroy(self):
                # Simulate closing connections
                await asyncio.sleep(0.002)
                self.connections = []
                self.pool = None
        
        registry = ServiceRegistry()
        registry.register('DatabasePool', DatabasePool)
        
        asyncio.run(registry.initialize_all_async())
        pool = registry.get_instance('DatabasePool')
        self.assertEqual(pool.pool, 'initialized')
        self.assertEqual(len(pool.connections), 3)
        
        asyncio.run(registry.destroy_all_async())
        self.assertEqual(pool.connections, [])
        self.assertIsNone(pool.pool)
    
    def test_multiple_async_services(self):
        """Test multiple async services initializing concurrently."""
        
        init_times = {}
        
        class CacheService(Service):
            async def on_init(self):
                start = asyncio.get_event_loop().time()
                await asyncio.sleep(0.01)
                init_times['cache'] = asyncio.get_event_loop().time() - start
        
        class QueueService(Service):
            async def on_init(self):
                start = asyncio.get_event_loop().time()
                await asyncio.sleep(0.01)
                init_times['queue'] = asyncio.get_event_loop().time() - start
        
        class MetricsService(Service):
            async def on_init(self):
                start = asyncio.get_event_loop().time()
                await asyncio.sleep(0.01)
                init_times['metrics'] = asyncio.get_event_loop().time() - start
        
        registry = ServiceRegistry()
        registry.register('CacheService', CacheService)
        registry.register('QueueService', QueueService)
        registry.register('MetricsService', MetricsService)
        
        asyncio.run(registry.initialize_all_async())
        
        # All services should be initialized
        self.assertEqual(len(init_times), 3)
        for service_name, time_taken in init_times.items():
            self.assertGreater(time_taken, 0.008)  # Should have taken some time


if __name__ == '__main__':
    unittest.main()
