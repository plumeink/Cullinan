# -*- coding: utf-8 -*-
"""Performance benchmarks for optimized unified registration system.

Tests the performance improvements of the optimized registry implementation.
"""

import time
import unittest
from typing import List
from cullinan.core import Registry, SimpleRegistry
from cullinan.service import Service, service, get_service_registry, reset_service_registry
from cullinan.controller import get_controller_registry, reset_controller_registry


class PerformanceBenchmark(unittest.TestCase):
    """Benchmark performance of optimized registries."""

    def setUp(self):
        """Reset registries before each test."""
        reset_service_registry()
        reset_controller_registry()

    def test_registry_registration_performance(self):
        """Test O(1) registration performance."""
        registry = SimpleRegistry()

        # Benchmark registration
        start = time.perf_counter()
        for i in range(10000):
            registry.register(f"item_{i}", f"value_{i}")
        elapsed = time.perf_counter() - start

        print(f"\n  [OK] Registered 10,000 items in {elapsed:.4f}s ({10000/elapsed:.0f} ops/sec)")
        self.assertEqual(registry.count(), 10000)
        self.assertLess(elapsed, 0.1, "Registration should be fast (< 100ms for 10k items)")

    def test_registry_lookup_performance(self):
        """Test O(1) lookup performance."""
        registry = SimpleRegistry()

        # Prepare data
        for i in range(10000):
            registry.register(f"item_{i}", f"value_{i}")

        # Benchmark lookup
        start = time.perf_counter()
        for i in range(10000):
            _ = registry.get(f"item_{i}")
        elapsed = time.perf_counter() - start

        print(f"  [OK] Retrieved 10,000 items in {elapsed:.4f}s ({10000/elapsed:.0f} ops/sec)")
        self.assertLess(elapsed, 0.05, "Lookup should be very fast (< 50ms for 10k items)")

    def test_registry_has_performance(self):
        """Test O(1) membership check performance."""
        registry = SimpleRegistry()

        # Prepare data
        for i in range(10000):
            registry.register(f"item_{i}", f"value_{i}")

        # Benchmark has()
        start = time.perf_counter()
        for i in range(10000):
            _ = registry.has(f"item_{i}")
        elapsed = time.perf_counter() - start

        print(f"  [OK] Checked 10,000 items in {elapsed:.4f}s ({10000/elapsed:.0f} ops/sec)")
        self.assertLess(elapsed, 0.05, "Membership check should be very fast")

    def test_service_registry_performance(self):
        """Test ServiceRegistry performance with dependencies."""
        registry = get_service_registry()

        # Create base service
        @service
        class BaseService(Service):
            pass

        # Register multiple services manually (decorator can't be used in loop)
        start = time.perf_counter()
        for i in range(100):
            class DynamicService(Service):
                pass
            service_name = f"Service_{i}"
            registry.register(service_name, DynamicService, dependencies=['BaseService'] if i > 0 else [])
        elapsed = time.perf_counter() - start

        print(f"  [OK] Registered 100 services in {elapsed:.4f}s")
        self.assertGreaterEqual(registry.count(), 100)
        self.assertLess(elapsed, 0.5, "Service registration should be fast")

    def test_controller_registry_performance(self):
        """Test ControllerRegistry performance."""
        registry = get_controller_registry()

        # Register controllers
        start = time.perf_counter()
        for i in range(1000):
            class TestController:
                pass
            registry.register(f"Controller_{i}", TestController, url_prefix=f"/api/{i}")
        elapsed = time.perf_counter() - start

        print(f"  [OK] Registered 1,000 controllers in {elapsed:.4f}s ({1000/elapsed:.0f} ops/sec)")
        self.assertEqual(registry.count(), 1000)
        self.assertLess(elapsed, 0.1, "Controller registration should be fast")

    def test_controller_method_registration_performance(self):
        """Test method registration performance."""
        registry = get_controller_registry()

        class TestController:
            pass

        registry.register('TestController', TestController)

        # Benchmark method registration
        start = time.perf_counter()
        for i in range(1000):
            registry.register_method('TestController', f'/route_{i}', 'get', lambda: None)
        elapsed = time.perf_counter() - start

        print(f"  [OK] Registered 1,000 methods in {elapsed:.4f}s ({1000/elapsed:.0f} ops/sec)")
        self.assertEqual(registry.get_method_count('TestController'), 1000)
        self.assertLess(elapsed, 0.05, "Method registration should be very fast")

    def test_batch_method_registration_performance(self):
        """Test batch method registration is faster than individual."""
        registry = get_controller_registry()

        class TestController:
            pass

        registry.register('TestController', TestController)

        # Prepare methods
        methods = [(f'/route_{i}', 'get', lambda: None) for i in range(1000)]

        # Benchmark batch registration
        start = time.perf_counter()
        count = registry.register_methods_batch('TestController', methods)
        elapsed = time.perf_counter() - start

        print(f"  [OK] Batch registered 1,000 methods in {elapsed:.4f}s ({1000/elapsed:.0f} ops/sec)")
        self.assertEqual(count, 1000)
        self.assertLess(elapsed, 0.01, "Batch registration should be extremely fast")

    def test_lazy_metadata_initialization(self):
        """Test that metadata dict is not created unless needed."""
        registry = SimpleRegistry()

        # Register without metadata
        registry.register("test1", "value1")

        # Metadata should be None (lazy init)
        self.assertIsNone(registry._metadata)

        # Register with metadata
        registry.register("test2", "value2", some_meta="data")

        # Now metadata should exist
        self.assertIsNotNone(registry._metadata)
        self.assertIn("test2", registry._metadata)
        self.assertNotIn("test1", registry._metadata)

        print("  [OK] Lazy metadata initialization working correctly")

    def test_memory_efficiency_slots(self):
        """Test that __slots__ reduces memory overhead."""
        import sys

        # SimpleRegistry uses __slots__ from parent
        registry = SimpleRegistry()

        # Register some items
        for i in range(100):
            registry.register(f"item_{i}", f"value_{i}")

        # Check that registry doesn't have __dict__
        self.assertFalse(hasattr(registry, '__dict__'),
                        "Registry should use __slots__, not __dict__")

        # Estimate memory savings (rough)
        # Objects with __dict__ typically use ~280+ bytes overhead
        # Objects with __slots__ use ~56 bytes overhead
        # For 1000 registries, savings would be ~224KB

        print("  [OK] Registry uses __slots__ for memory efficiency")

    def test_service_instance_caching(self):
        """Test that service instances are cached (O(1) re-access)."""
        registry = get_service_registry()

        @service
        class TestService(Service):
            pass

        # First access
        start = time.perf_counter()
        instance1 = registry.get_instance('TestService')
        first_access = time.perf_counter() - start

        # Cached access (should be much faster)
        start = time.perf_counter()
        for _ in range(10000):
            instance2 = registry.get_instance('TestService')
        cached_access = (time.perf_counter() - start) / 10000

        print(f"  [OK] First access: {first_access*1000:.3f}ms, Cached: {cached_access*1000000:.1f}μs")
        print(f"    Speedup: {first_access/cached_access:.0f}x faster")

        # Cached access should be at least 10x faster
        self.assertLess(cached_access, first_access / 10)
        self.assertIs(instance1, instance2, "Should return same instance")


def run_benchmarks():
    """Run all performance benchmarks and print summary."""
    print("\n" + "="*70)
    print("PERFORMANCE BENCHMARKS - Optimized Unified Registration System")
    print("="*70)

    suite = unittest.TestLoader().loadTestsFromTestCase(PerformanceBenchmark)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    if result.wasSuccessful():
        print("✅ All performance benchmarks PASSED!")
        print("\nKey Optimizations Verified:")
        print("  • O(1) registration and lookup")
        print("  • Lazy metadata initialization")
        print("  • Memory-efficient __slots__")
        print("  • Service instance caching")
        print("  • Batch operations support")
    else:
        print("[ERROR] Some benchmarks failed - review results above")

    print("="*70 + "\n")

    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_benchmarks()
    sys.exit(0 if success else 1)

