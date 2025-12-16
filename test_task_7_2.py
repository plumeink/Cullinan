# -*- coding: utf-8 -*-
"""Test script for Task-7.2: Unified Extension Registration and Discovery Pattern

Tests the new middleware decorator and extension registry system.

Author: Plumeink
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_middleware_decorator():
    """Test the new @middleware decorator."""
    from cullinan.middleware import middleware, Middleware, get_middleware_registry

    print("\n=== Test 1: Middleware Decorator Registration ===")

    @middleware(priority=50)
    class SecurityMiddleware(Middleware):
        def process_request(self, handler):
            logger.info("SecurityMiddleware: process_request")
            return None

        def process_response(self, handler, response):
            logger.info("SecurityMiddleware: process_response")
            return response

    @middleware(priority=100)
    class LoggingMiddleware(Middleware):
        def process_request(self, handler):
            logger.info("LoggingMiddleware: process_request")
            return None

        def process_response(self, handler, response):
            logger.info("LoggingMiddleware: process_response")
            return response

    @middleware(priority=150)
    class MetricsMiddleware(Middleware):
        def process_request(self, handler):
            logger.info("MetricsMiddleware: process_request")
            return None

        def process_response(self, handler, response):
            logger.info("MetricsMiddleware: process_response")
            return response

    # Check registration
    registry = get_middleware_registry()
    registered = registry.get_registered_middleware()

    print(f"Registered {len(registered)} middleware:")
    for mw in registered:
        print(f"  - {mw['name']} (priority: {mw['priority']})")

    assert len(registered) == 3, f"Expected 3 middleware, got {len(registered)}"

    # Check priority ordering
    chain = registry.get_middleware_chain()
    print("\nMiddleware chain created successfully")

    print("✓ Test 1 passed: Middleware decorator works")
    return True


def test_extension_registry():
    """Test the extension registry and discovery API."""
    from cullinan.extensions import (
        get_extension_registry,
        list_extension_points,
        ExtensionCategory,
    )

    print("\n=== Test 2: Extension Registry ===")

    registry = get_extension_registry()

    # List all extension points
    all_points = registry.get_extension_points()
    print(f"\nTotal extension points: {len(all_points)}")

    # List by category
    categories = registry.list_categories()
    print(f"\nAvailable categories: {', '.join(categories)}")

    for category in [ExtensionCategory.MIDDLEWARE, ExtensionCategory.LIFECYCLE]:
        points = registry.get_extension_points(category=category)
        print(f"\n{category.value.capitalize()} extension points ({len(points)}):")
        for point in points:
            print(f"  - {point.name}: {point.description}")

    # Test convenience function
    middleware_points = list_extension_points(category='middleware')
    print(f"\nMiddleware points via convenience function: {len(middleware_points)}")

    assert len(all_points) > 0, "No extension points registered"
    assert len(middleware_points) > 0, "No middleware extension points"

    print("✓ Test 2 passed: Extension registry works")
    return True


def test_get_specific_extension_point():
    """Test getting a specific extension point."""
    from cullinan.extensions import get_extension_registry

    print("\n=== Test 3: Get Specific Extension Point ===")

    registry = get_extension_registry()

    # Get a specific extension point
    point = registry.get_extension_point('Middleware.process_request')

    if point:
        print(f"\nFound extension point: {point.name}")
        print(f"  Category: {point.category.value}")
        print(f"  Description: {point.description}")
        print(f"  Interface: {point.interface.__name__ if point.interface else 'N/A'}")
        print(f"  Example URL: {point.example_url or 'N/A'}")
    else:
        raise AssertionError("Extension point 'Middleware.process_request' not found")

    print("✓ Test 3 passed: Specific extension point retrieval works")
    return True


def test_middleware_priority_ordering():
    """Test that middleware are ordered by priority."""
    from cullinan.middleware import middleware, Middleware, get_middleware_registry, reset_middleware_registry

    print("\n=== Test 4: Middleware Priority Ordering ===")

    # Reset registry for clean test
    reset_middleware_registry()

    execution_order = []

    @middleware(priority=200)
    class ThirdMiddleware(Middleware):
        def process_request(self, handler):
            execution_order.append('Third')
            return handler  # Return handler to continue

    @middleware(priority=50)
    class FirstMiddleware(Middleware):
        def process_request(self, handler):
            execution_order.append('First')
            return handler  # Return handler to continue

    @middleware(priority=100)
    class SecondMiddleware(Middleware):
        def process_request(self, handler):
            execution_order.append('Second')
            return handler  # Return handler to continue

    # Get middleware chain (should be sorted)
    registry = get_middleware_registry()
    chain = registry.get_middleware_chain()

    # Mock handler for testing
    class MockHandler:
        pass

    handler = MockHandler()
    chain.process_request(handler)

    print(f"\nExecution order: {' -> '.join(execution_order)}")
    expected = ['First', 'Second', 'Third']

    assert execution_order == expected, f"Expected {expected}, got {execution_order}"

    print("✓ Test 4 passed: Middleware execute in correct priority order")
    return True


def test_backward_compatibility():
    """Test that manual registration still works."""
    from cullinan.middleware import Middleware, get_middleware_registry, reset_middleware_registry

    print("\n=== Test 5: Backward Compatibility ===")

    # Reset registry
    reset_middleware_registry()

    class ManualMiddleware(Middleware):
        def process_request(self, handler):
            return None

    # Manual registration (old way)
    registry = get_middleware_registry()
    registry.register(ManualMiddleware, priority=75)

    registered = registry.get_registered_middleware()
    assert len(registered) == 1, f"Expected 1 middleware, got {len(registered)}"
    assert registered[0]['name'] == 'ManualMiddleware'
    assert registered[0]['priority'] == 75

    print("\nManual registration still works:")
    print(f"  - {registered[0]['name']} (priority: {registered[0]['priority']})")

    print("✓ Test 5 passed: Backward compatibility maintained")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("Task-7.2: Unified Extension Registration and Discovery Pattern")
    print("=" * 70)

    tests = [
        test_middleware_decorator,
        test_extension_registry,
        test_get_specific_extension_point,
        test_middleware_priority_ordering,
        test_backward_compatibility,
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

    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n✓ All tests passed! Task-7.2 implementation is working correctly.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

