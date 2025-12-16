# -*- coding: utf-8 -*-
"""Test script for Task-1.2: Unified IoC/DI Dependency Resolution Interface

Tests the new IoC Facade that provides a simplified API for dependency resolution.

Author: Plumeink
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_resolution():
    """Test basic dependency resolution by type."""
    from cullinan.service import service, Service
    from cullinan.core.facade import get_ioc_facade, resolve_dependency

    print("\n=== Test 1: Basic Dependency Resolution ===")

    # Define test services
    @service
    class EmailService(Service):
        def send_email(self, to: str, subject: str):
            return f"Email sent to {to}: {subject}"

    @service
    class UserService(Service):
        def create_user(self, name: str):
            return f"User created: {name}"

    # Initialize services (normally done by application)
    from cullinan.service import get_service_registry
    registry = get_service_registry()
    registry.initialize_all()

    # Test facade resolution
    facade = get_ioc_facade()

    # Resolve by type
    email_service = facade.resolve(EmailService)
    assert email_service is not None, "EmailService should be resolved"
    assert isinstance(email_service, EmailService)

    user_service = facade.resolve(UserService)
    assert user_service is not None, "UserService should be resolved"
    assert isinstance(user_service, UserService)

    # Test service functionality
    result = email_service.send_email("test@example.com", "Hello")
    assert "Email sent" in result

    result = user_service.create_user("Alice")
    assert "User created: Alice" in result

    print(f"✓ Resolved EmailService: {email_service.__class__.__name__}")
    print(f"✓ Resolved UserService: {user_service.__class__.__name__}")
    print(f"✓ Services are functional")

    # Test convenience function
    email_service2 = resolve_dependency(EmailService)
    assert email_service2 is email_service, "Should return cached instance"

    print("✓ Convenience function works")
    print("✓ Test 1 passed: Basic resolution works\n")
    return True


def test_resolution_by_name():
    """Test dependency resolution by name."""
    from cullinan.service import service, Service
    from cullinan.core.facade import get_ioc_facade, resolve_dependency_by_name

    print("=== Test 2: Resolution by Name ===")

    @service
    class CacheService(Service):
        def get(self, key: str):
            return f"Value for {key}"

    # Initialize
    from cullinan.service import get_service_registry
    registry = get_service_registry()
    registry.initialize_all()

    # Resolve by name
    facade = get_ioc_facade()
    cache = facade.resolve_by_name('CacheService')

    assert cache is not None, "CacheService should be resolved"
    assert isinstance(cache, CacheService)

    result = cache.get("test_key")
    assert "Value for test_key" in result

    print(f"✓ Resolved by name: CacheService")
    print(f"✓ Service is functional")

    # Test convenience function
    cache2 = resolve_dependency_by_name('CacheService')
    assert cache2 is cache, "Should return cached instance"

    print("✓ Convenience function works")
    print("✓ Test 2 passed: Name-based resolution works\n")
    return True


def test_optional_dependencies():
    """Test optional dependency resolution."""
    from cullinan.core.facade import get_ioc_facade, has_dependency

    print("=== Test 3: Optional Dependencies ===")

    facade = get_ioc_facade()

    # Test non-existent dependency
    class NonExistentService:
        pass

    # Should not raise error with required=False
    result = facade.resolve(NonExistentService, required=False)
    assert result is None, "Non-existent service should return None"

    print("✓ Optional resolution returns None for missing dependency")

    # Test has_dependency
    assert not has_dependency(NonExistentService)
    print("✓ has_dependency returns False for missing dependency")

    # Test with existing service
    from cullinan.service import service, Service, get_service_registry

    @service
    class ExistingService(Service):
        pass

    registry = get_service_registry()
    registry.initialize_all()

    assert has_dependency(ExistingService)
    print("✓ has_dependency returns True for existing dependency")

    existing = facade.resolve(ExistingService, required=False)
    assert existing is not None
    print("✓ Optional resolution returns instance for existing dependency")

    print("✓ Test 3 passed: Optional dependencies work\n")
    return True


def test_error_handling():
    """Test error handling for missing dependencies."""
    from cullinan.core.facade import get_ioc_facade, DependencyResolutionError

    print("=== Test 4: Error Handling ===")

    facade = get_ioc_facade()

    class MissingService:
        pass

    # Should raise error with required=True (default)
    try:
        facade.resolve(MissingService)
        assert False, "Should have raised DependencyResolutionError"
    except DependencyResolutionError as e:
        assert "Cannot resolve dependency" in str(e)
        assert "MissingService" in str(e)
        print(f"✓ Proper error raised: {e}")

    # Test by name
    try:
        facade.resolve_by_name('NonExistentService')
        assert False, "Should have raised DependencyResolutionError"
    except DependencyResolutionError as e:
        assert "Cannot resolve dependency by name" in str(e)
        print(f"✓ Proper error raised for name resolution: {e}")

    print("✓ Test 4 passed: Error handling works\n")
    return True


def test_caching():
    """Test instance caching."""
    from cullinan.service import service, Service, get_service_registry
    from cullinan.core.facade import get_ioc_facade

    print("=== Test 5: Instance Caching ===")

    @service
    class SingletonService(Service):
        def __init__(self):
            super().__init__()
            import uuid
            self.instance_id = uuid.uuid4().hex[:8]

    registry = get_service_registry()
    registry.initialize_all()

    facade = get_ioc_facade()

    # Resolve multiple times
    service1 = facade.resolve(SingletonService)
    service2 = facade.resolve(SingletonService)
    service3 = facade.resolve(SingletonService)

    # Should be the same instance
    assert service1 is service2, "Should return same instance"
    assert service2 is service3, "Should return same instance"
    assert service1.instance_id == service2.instance_id

    print(f"✓ All resolutions return same instance (ID: {service1.instance_id})")

    # Test cache clearing
    facade.clear_cache()
    print("✓ Cache cleared")

    # After clearing, should still get same instance from registry
    service4 = facade.resolve(SingletonService)
    assert service4 is service1, "ServiceRegistry maintains singleton"

    print("✓ Singleton maintained after cache clear")
    print("✓ Test 5 passed: Caching works\n")
    return True


def test_list_dependencies():
    """Test listing available dependencies."""
    from cullinan.service import service, Service, get_service_registry
    from cullinan.core.facade import get_ioc_facade

    print("=== Test 6: List Dependencies ===")

    @service
    class Service1(Service):
        pass

    @service
    class Service2(Service):
        pass

    registry = get_service_registry()
    registry.initialize_all()

    facade = get_ioc_facade()
    dependencies = facade.list_available_dependencies()

    assert 'Service1' in dependencies
    assert 'Service2' in dependencies

    print(f"✓ Found {len(dependencies)} dependencies")
    print(f"  Including: {', '.join(dependencies[:5])}")

    print("✓ Test 6 passed: Listing dependencies works\n")
    return True


def test_performance():
    """Test performance of facade resolution."""
    import time
    from cullinan.service import service, Service, get_service_registry
    from cullinan.core.facade import get_ioc_facade, resolve_dependency

    print("=== Test 7: Performance ===")

    @service
    class PerformanceTestService(Service):
        def operation(self):
            return "done"

    registry = get_service_registry()
    registry.initialize_all()

    facade = get_ioc_facade()

    # Warm up
    facade.resolve(PerformanceTestService)

    # Test resolution performance (with cache)
    iterations = 10000
    start_time = time.perf_counter()

    for _ in range(iterations):
        service = facade.resolve(PerformanceTestService)

    elapsed = time.perf_counter() - start_time
    avg_time_us = (elapsed / iterations) * 1_000_000

    print(f"✓ {iterations} resolutions in {elapsed:.4f}s")
    print(f"✓ Average: {avg_time_us:.2f} μs per resolution (cached)")

    assert avg_time_us < 10, f"Should be fast (<10μs), got {avg_time_us:.2f}μs"

    # Test convenience function performance
    start_time = time.perf_counter()

    for _ in range(iterations):
        service = resolve_dependency(PerformanceTestService)

    elapsed = time.perf_counter() - start_time
    avg_time_us = (elapsed / iterations) * 1_000_000

    print(f"✓ Convenience function: {avg_time_us:.2f} μs per resolution")

    print("✓ Test 7 passed: Performance is acceptable\n")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("Task-1.2: Unified IoC/DI Dependency Resolution Interface")
    print("=" * 70)

    tests = [
        test_basic_resolution,
        test_resolution_by_name,
        test_optional_dependencies,
        test_error_handling,
        test_caching,
        test_list_dependencies,
        test_performance,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} failed: {e}", exc_info=True)
            failed += 1

    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n✓ All tests passed! Task-1.2 implementation is working correctly.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

