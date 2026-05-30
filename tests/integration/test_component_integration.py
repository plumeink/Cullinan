# -*- coding: utf-8 -*-
"""Integration test to verify @component works in the full application flow."""

import sys
import os
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_component_in_full_flow():
    """Test @component registration in full application initialization flow."""
    from cullinan.core import ApplicationContext, set_application_context
    from cullinan.core.pending import PendingRegistry, ComponentType
    from cullinan.core.decorators import component, service, controller
    from cullinan.core.lifecycle_enhanced import SmartLifecycle

    # Reset state
    PendingRegistry.reset()

    lifecycle_log = []

    # Define a component that inherits SmartLifecycle (so lifecycle hooks work)
    @component
    class CacheManager(SmartLifecycle):
        def get_phase(self):
            return -50  # Early startup

        def on_post_construct(self):
            lifecycle_log.append('CacheManager.on_post_construct')
            self._cache = {}

        def on_startup(self):
            lifecycle_log.append('CacheManager.on_startup')

        def on_shutdown(self):
            lifecycle_log.append('CacheManager.on_shutdown')

    @service
    class UserService(SmartLifecycle):
        def on_post_construct(self):
            lifecycle_log.append('UserService.on_post_construct')

        def on_startup(self):
            lifecycle_log.append('UserService.on_startup')

    @controller
    class ApiController(SmartLifecycle):
        def on_post_construct(self):
            lifecycle_log.append('ApiController.on_post_construct')

        def on_startup(self):
            lifecycle_log.append('ApiController.on_startup')

    # Check PendingRegistry before refresh
    pending = PendingRegistry.get_instance()
    all_regs = pending.get_all()

    print(f"\n=== PendingRegistry before refresh ===")
    print(f"Total registrations: {len(all_regs)}")
    for reg in all_regs:
        print(f"  - {reg.name}: type={reg.component_type.value}")

    # Verify component is in pending
    components = pending.get_by_type(ComponentType.COMPONENT)
    assert len(components) >= 1, f"Expected at least 1 component, got {len(components)}"
    component_names = [c.name for c in components]
    assert 'CacheManager' in component_names, f"CacheManager not in components: {component_names}"

    # Create and refresh ApplicationContext
    ctx = ApplicationContext()
    set_application_context(ctx)
    ctx.refresh()

    # Check definitions
    definitions = ctx.list_definitions()
    print(f"\n=== ApplicationContext definitions ===")
    print(f"Definitions: {definitions}")

    assert 'CacheManager' in definitions, f"CacheManager not in definitions: {definitions}"
    assert 'UserService' in definitions, f"UserService not in definitions: {definitions}"
    assert 'ApiController' in definitions, f"ApiController not in definitions: {definitions}"

    # Check lifecycle log
    print(f"\n=== Lifecycle log ===")
    for entry in lifecycle_log:
        print(f"  - {entry}")

    # CacheManager should be initialized first (lower phase)
    cache_post_idx = lifecycle_log.index('CacheManager.on_post_construct')
    user_post_idx = lifecycle_log.index('UserService.on_post_construct')
    api_post_idx = lifecycle_log.index('ApiController.on_post_construct')

    print(f"\n=== Initialization order ===")
    print(f"CacheManager.on_post_construct: index {cache_post_idx}")
    print(f"UserService.on_post_construct: index {user_post_idx}")
    print(f"ApiController.on_post_construct: index {api_post_idx}")

    # CacheManager should be first (phase -50)
    assert cache_post_idx < user_post_idx, "CacheManager should be initialized before UserService"
    assert cache_post_idx < api_post_idx, "CacheManager should be initialized before ApiController"

    # Get instances
    cache_instance = ctx.get('CacheManager')
    user_instance = ctx.get('UserService')
    api_instance = ctx.get('ApiController')

    assert cache_instance is not None
    assert user_instance is not None
    assert api_instance is not None

    # Verify phase
    assert ctx.is_component_running('CacheManager'), "CacheManager should be running"
    assert ctx.is_component_running('UserService'), "UserService should be running"
    assert ctx.is_component_running('ApiController'), "ApiController should be running"

    # Shutdown
    ctx.shutdown()

    # Verify shutdown callbacks
    assert 'CacheManager.on_shutdown' in lifecycle_log, "CacheManager.on_shutdown should be called"

    print("\n✅ test_component_in_full_flow passed!")


def test_component_without_lifecycle_base():
    """Test that @component works even without SmartLifecycle inheritance."""
    from cullinan.core import ApplicationContext, set_application_context
    from cullinan.core.pending import PendingRegistry
    from cullinan.core.decorators import component

    # Reset state
    PendingRegistry.reset()

    # Plain component without SmartLifecycle
    @component
    class SimpleCache:
        def __init__(self):
            self.data = {}

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value):
            self.data[key] = value

    # Create context
    ctx = ApplicationContext()
    set_application_context(ctx)
    ctx.refresh()

    # Get instance
    cache = ctx.get('SimpleCache')
    assert cache is not None, "SimpleCache instance should not be None"

    # Use it
    cache.set('test', 'value')
    assert cache.get('test') == 'value'

    # Same instance (singleton)
    cache2 = ctx.get('SimpleCache')
    assert cache is cache2, "Should return same singleton instance"

    ctx.shutdown()

    print("✅ test_component_without_lifecycle_base passed!")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Integration Test: @component in full application flow")
    print("=" * 60)

    test_component_without_lifecycle_base()
    test_component_in_full_flow()

    print("\n" + "=" * 60)
    print("All integration tests passed!")
    print("=" * 60 + "\n")
