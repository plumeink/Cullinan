# -*- coding: utf-8 -*-
"""Tests for Complete Lifecycle System"""

import unittest
import asyncio
from typing import List

from cullinan.core.lifecycle_enhanced import (
    LifecyclePhase, LifecycleAware, SmartLifecycle,
    LifecycleManager, get_lifecycle_manager, reset_lifecycle_manager
)
from cullinan.service import service, Service, get_service_registry, reset_service_registry
from cullinan.core import Inject, get_injection_registry, reset_injection_registry


class TestLifecyclePhases(unittest.TestCase):
    """Test lifecycle phase execution"""

    def setUp(self):
        self.execution_log: List[str] = []

    def test_lifecycle_phases_order(self):
        """Test that lifecycle phases execute in correct order"""

        class TestComponent(LifecycleAware):
            def __init__(self, log):
                self.log = log

            def on_post_construct(self):
                self.log.append('post_construct')

            def on_startup(self):
                self.log.append('startup')

            def on_shutdown(self):
                self.log.append('shutdown')

            def on_pre_destroy(self):
                self.log.append('pre_destroy')

        manager = LifecycleManager()
        component = TestComponent(self.execution_log)
        manager.register(component, name='test')

        # Run lifecycle
        asyncio.run(manager.startup())
        asyncio.run(manager.shutdown())

        # Verify order
        self.assertEqual(
            self.execution_log,
            ['post_construct', 'startup', 'shutdown', 'pre_destroy']
        )
        print("  [OK] Lifecycle phases execute in correct order")

    def test_async_lifecycle_phases(self):
        """Test async lifecycle methods"""

        class AsyncComponent(LifecycleAware):
            def __init__(self, log):
                self.log = log

            async def on_post_construct_async(self):
                await asyncio.sleep(0.01)
                self.log.append('post_construct_async')

            async def on_startup_async(self):
                await asyncio.sleep(0.01)
                self.log.append('startup_async')

        manager = LifecycleManager()
        component = AsyncComponent(self.execution_log)
        manager.register(component, name='async_test')

        asyncio.run(manager.startup())

        self.assertIn('post_construct_async', self.execution_log)
        self.assertIn('startup_async', self.execution_log)
        print("  [OK] Async lifecycle methods work")


class TestDependencyOrdering(unittest.TestCase):
    """Test dependency-based initialization ordering"""

    def setUp(self):
        self.startup_order: List[str] = []
        self.shutdown_order: List[str] = []

    def test_dependency_order(self):
        """Test that components start in dependency order"""

        class ComponentA(LifecycleAware):
            def __init__(self, log):
                self.log = log
            def on_startup(self):
                self.log.append('A')

        class ComponentB(LifecycleAware):
            def __init__(self, log):
                self.log = log
            def on_startup(self):
                self.log.append('B')

        class ComponentC(LifecycleAware):
            def __init__(self, log):
                self.log = log
            def on_startup(self):
                self.log.append('C')

        manager = LifecycleManager()

        # Register with dependencies: C -> B -> A
        a = ComponentA(self.startup_order)
        b = ComponentB(self.startup_order)
        c = ComponentC(self.startup_order)

        manager.register(c, name='C', dependencies=['B'])
        manager.register(b, name='B', dependencies=['A'])
        manager.register(a, name='A', dependencies=[])

        asyncio.run(manager.startup())

        # Verify A starts before B, B starts before C
        self.assertEqual(self.startup_order, ['A', 'B', 'C'])
        print("  [OK] Dependency ordering works")

    def test_shutdown_reverse_order(self):
        """Test that components shutdown in reverse order"""

        class ComponentA(LifecycleAware):
            def __init__(self, log):
                self.log = log
            def on_shutdown(self):
                self.log.append('A')

        class ComponentB(LifecycleAware):
            def __init__(self, log):
                self.log = log
            def on_shutdown(self):
                self.log.append('B')

        manager = LifecycleManager()

        a = ComponentA(self.shutdown_order)
        b = ComponentB(self.shutdown_order)

        manager.register(a, name='A', dependencies=[])
        manager.register(b, name='B', dependencies=['A'])

        asyncio.run(manager.startup())
        asyncio.run(manager.shutdown())

        # B depends on A, so B shuts down first
        self.assertEqual(self.shutdown_order, ['B', 'A'])
        print("  [OK] Shutdown reverse ordering works")


class TestPhaseControl(unittest.TestCase):
    """Test phase-based startup control"""

    def setUp(self):
        self.startup_order: List[str] = []

    def test_phase_ordering(self):
        """Test that lower phases start earlier"""

        class EarlyComponent(SmartLifecycle):
            def __init__(self, log):
                self.log = log
            def get_phase(self):
                return -100
            def on_startup(self):
                self.log.append('Early')

        class LateComponent(SmartLifecycle):
            def __init__(self, log):
                self.log = log
            def get_phase(self):
                return 100
            def on_startup(self):
                self.log.append('Late')

        class MiddleComponent(SmartLifecycle):
            def __init__(self, log):
                self.log = log
            def get_phase(self):
                return 0
            def on_startup(self):
                self.log.append('Middle')

        manager = LifecycleManager()

        late = LateComponent(self.startup_order)
        early = EarlyComponent(self.startup_order)
        middle = MiddleComponent(self.startup_order)

        # Register in random order
        manager.register(late, name='Late')
        manager.register(middle, name='Middle')
        manager.register(early, name='Early')

        asyncio.run(manager.startup())

        # Should start in phase order: Early (-100), Middle (0), Late (100)
        self.assertEqual(self.startup_order, ['Early', 'Middle', 'Late'])
        print("  [OK] Phase-based ordering works")


class TestServiceIntegration(unittest.TestCase):
    """Test integration with Service and dependency injection"""

    def setUp(self):
        reset_injection_registry()
        reset_service_registry()
        reset_lifecycle_manager()

        # Configure injection
        injection_registry = get_injection_registry()
        service_registry = get_service_registry()
        injection_registry.add_provider_registry(service_registry, priority=100)

    def test_service_with_lifecycle(self):
        """Test Service with lifecycle hooks"""
        execution_log = []

        @service
        class TestService(Service):
            def on_post_construct(self):
                execution_log.append('service_init')

            def on_startup(self):
                execution_log.append('service_start')

        # Get lifecycle manager
        manager = get_lifecycle_manager()
        service_registry = get_service_registry()

        # Register service with lifecycle
        svc = service_registry.get_instance('TestService')
        manager.register(svc, name='TestService')

        # Run lifecycle
        asyncio.run(manager.startup())

        self.assertIn('service_init', execution_log)
        self.assertIn('service_start', execution_log)
        print("  [OK] Service lifecycle integration works")

    def test_service_dependency_chain(self):
        """Test lifecycle with service dependency chain"""
        startup_log = []

        @service
        class ServiceA(Service):
            def get_phase(self):
                return -100
            def on_startup(self):
                startup_log.append('A')

        @service
        class ServiceB(Service):
            a: ServiceA = Inject()
            def get_phase(self):
                return -50
            def on_startup(self):
                startup_log.append('B')

        @service
        class ServiceC(Service):
            b: ServiceB = Inject()
            def on_startup(self):
                startup_log.append('C')

        # Setup lifecycle
        manager = get_lifecycle_manager()
        service_registry = get_service_registry()

        for name in ['ServiceA', 'ServiceB', 'ServiceC']:
            svc = service_registry.get_instance(name)
            manager.register(svc, name=name)

        asyncio.run(manager.startup())

        # Should follow phase order: A (-100), B (-50), C (0)
        self.assertEqual(startup_log, ['A', 'B', 'C'])
        print("  [OK] Service dependency chain with phases works")


def run_all_tests():
    """Run all lifecycle tests"""
    print("\n" + "="*70)
    print("Complete Lifecycle System - Tests")
    print("="*70 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestLifecyclePhases))
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyOrdering))
    suite.addTests(loader.loadTestsFromTestCase(TestPhaseControl))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n[OK] All lifecycle tests passed!")
    else:
        print("\n[FAIL] Some tests failed")

    print("="*70 + "\n")

    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)

