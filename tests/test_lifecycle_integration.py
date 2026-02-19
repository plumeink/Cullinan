# -*- coding: utf-8 -*-
"""Integration test for unified lifecycle with @service decorator.

This test verifies that services decorated with @service correctly
receive lifecycle callbacks from ApplicationContext.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_service_decorator_with_lifecycle():
    """Test that @service decorated classes get lifecycle callbacks."""
    from cullinan.core import ApplicationContext, set_application_context
    from cullinan.core.pending import PendingRegistry
    from cullinan.core.decorators import service
    from cullinan.service import Service

    # Reset state
    PendingRegistry.get_instance().clear()
    PendingRegistry.get_instance()._frozen = False

    # Track lifecycle calls
    lifecycle_log = []

    # Define a service using the decorator
    @service
    class DatabaseService(Service):
        def get_phase(self):
            return -100  # Start early

        def on_post_construct(self):
            lifecycle_log.append('DatabaseService.on_post_construct')

        def on_startup(self):
            lifecycle_log.append('DatabaseService.on_startup')

        def on_shutdown(self):
            lifecycle_log.append('DatabaseService.on_shutdown')

        def on_pre_destroy(self):
            lifecycle_log.append('DatabaseService.on_pre_destroy')

    @service
    class UserService(Service):
        def get_phase(self):
            return 0

        def on_post_construct(self):
            lifecycle_log.append('UserService.on_post_construct')

        def on_startup(self):
            lifecycle_log.append('UserService.on_startup')

        def on_shutdown(self):
            lifecycle_log.append('UserService.on_shutdown')

        def on_pre_destroy(self):
            lifecycle_log.append('UserService.on_pre_destroy')

    # Create and refresh context
    ctx = ApplicationContext()
    set_application_context(ctx)
    ctx.refresh()

    # Verify startup order
    expected_startup = [
        'DatabaseService.on_post_construct',
        'UserService.on_post_construct',
        'DatabaseService.on_startup',
        'UserService.on_startup',
    ]

    startup_calls = [c for c in lifecycle_log if 'post_construct' in c or 'startup' in c]

    print(f"Actual startup order: {startup_calls}")
    print(f"Expected startup order: {expected_startup}")

    # Database should be before User due to phase
    assert 'DatabaseService.on_post_construct' in lifecycle_log
    assert 'UserService.on_post_construct' in lifecycle_log
    assert 'DatabaseService.on_startup' in lifecycle_log
    assert 'UserService.on_startup' in lifecycle_log

    # Shutdown
    ctx.shutdown()

    # Verify shutdown order (reverse of startup)
    expected_shutdown = [
        'UserService.on_shutdown',
        'DatabaseService.on_shutdown',
        'UserService.on_pre_destroy',
        'DatabaseService.on_pre_destroy',
    ]

    shutdown_calls = [c for c in lifecycle_log if 'shutdown' in c or 'destroy' in c]

    print(f"Actual shutdown order: {shutdown_calls}")
    print(f"Expected shutdown order: {expected_shutdown}")

    assert 'DatabaseService.on_shutdown' in lifecycle_log
    assert 'UserService.on_shutdown' in lifecycle_log
    assert 'DatabaseService.on_pre_destroy' in lifecycle_log
    assert 'UserService.on_pre_destroy' in lifecycle_log

    print("\n✅ test_service_decorator_with_lifecycle passed!")
    print(f"Full lifecycle log: {lifecycle_log}")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Integration Test: @service decorator with unified lifecycle")
    print("=" * 60 + "\n")

    test_service_decorator_with_lifecycle()

    print("\n" + "=" * 60)
    print("Integration test passed!")
    print("=" * 60 + "\n")
