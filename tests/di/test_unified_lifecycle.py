# -*- coding: utf-8 -*-
"""Test unified lifecycle management for all components.

Verifies that:
1. All components (@service, @controller, @component) use unified lifecycle
2. ApplicationContext.refresh() calls on_post_construct and on_startup
3. ApplicationContext.shutdown() calls on_shutdown and on_pre_destroy
4. Phase ordering works correctly
"""

from typing import List


def test_unified_lifecycle_basic():
    """Test that basic lifecycle hooks are called."""
    from cullinan.core import ApplicationContext, set_application_context
    from cullinan.core.pending import PendingRegistry
    from cullinan.core.lifecycle_enhanced import LifecycleAware, SmartLifecycle

    # Reset state
    PendingRegistry.get_instance().clear()
    PendingRegistry.get_instance()._frozen = False

    # Track lifecycle calls
    lifecycle_calls: List[str] = []

    # Define a test service with lifecycle hooks
    class TestService(SmartLifecycle):
        def on_post_construct(self):
            lifecycle_calls.append('on_post_construct')

        def on_startup(self):
            lifecycle_calls.append('on_startup')

        def on_shutdown(self):
            lifecycle_calls.append('on_shutdown')

        def on_pre_destroy(self):
            lifecycle_calls.append('on_pre_destroy')

    # Create context and register service
    ctx = ApplicationContext()
    set_application_context(ctx)

    from cullinan.core.definitions import Definition, ScopeType

    ctx.register(Definition(
        name='TestService',
        type_=TestService,
        scope=ScopeType.SINGLETON,
        factory=lambda c: TestService(),
        source='test',
    ))

    # Refresh should call on_post_construct and on_startup
    ctx.refresh()

    assert 'on_post_construct' in lifecycle_calls, "on_post_construct should be called"
    assert 'on_startup' in lifecycle_calls, "on_startup should be called"
    assert lifecycle_calls.index('on_post_construct') < lifecycle_calls.index('on_startup'), \
        "on_post_construct should be called before on_startup"

    # Shutdown should call on_shutdown and on_pre_destroy
    ctx.shutdown()

    assert 'on_shutdown' in lifecycle_calls, "on_shutdown should be called"
    assert 'on_pre_destroy' in lifecycle_calls, "on_pre_destroy should be called"
    assert lifecycle_calls.index('on_shutdown') < lifecycle_calls.index('on_pre_destroy'), \
        "on_shutdown should be called before on_pre_destroy"

    print(f"Lifecycle calls order: {lifecycle_calls}")
    print("✅ test_unified_lifecycle_basic passed!")


def test_lifecycle_phase_ordering():
    """Test that components are initialized in phase order."""
    from cullinan.core import ApplicationContext, set_application_context
    from cullinan.core.pending import PendingRegistry
    from cullinan.core.lifecycle_enhanced import SmartLifecycle
    from cullinan.core.definitions import Definition, ScopeType

    # Reset state
    PendingRegistry.get_instance().clear()
    PendingRegistry.get_instance()._frozen = False

    startup_order: List[str] = []
    shutdown_order: List[str] = []

    class EarlyService(SmartLifecycle):
        def get_phase(self) -> int:
            return -100  # Start early

        def on_startup(self):
            startup_order.append('EarlyService')

        def on_shutdown(self):
            shutdown_order.append('EarlyService')

    class NormalService(SmartLifecycle):
        def get_phase(self) -> int:
            return 0  # Default

        def on_startup(self):
            startup_order.append('NormalService')

        def on_shutdown(self):
            shutdown_order.append('NormalService')

    class LateService(SmartLifecycle):
        def get_phase(self) -> int:
            return 100  # Start late

        def on_startup(self):
            startup_order.append('LateService')

        def on_shutdown(self):
            shutdown_order.append('LateService')

    ctx = ApplicationContext()
    set_application_context(ctx)

    # Register in random order
    ctx.register(Definition(
        name='LateService',
        type_=LateService,
        scope=ScopeType.SINGLETON,
        factory=lambda c: LateService(),
        source='test',
    ))
    ctx.register(Definition(
        name='EarlyService',
        type_=EarlyService,
        scope=ScopeType.SINGLETON,
        factory=lambda c: EarlyService(),
        source='test',
    ))
    ctx.register(Definition(
        name='NormalService',
        type_=NormalService,
        scope=ScopeType.SINGLETON,
        factory=lambda c: NormalService(),
        source='test',
    ))

    ctx.refresh()

    # Should start in phase order: Early (-100) -> Normal (0) -> Late (100)
    assert startup_order == ['EarlyService', 'NormalService', 'LateService'], \
        f"Expected startup order: Early->Normal->Late, got: {startup_order}"

    ctx.shutdown()

    # Should shutdown in reverse order: Late -> Normal -> Early
    assert shutdown_order == ['LateService', 'NormalService', 'EarlyService'], \
        f"Expected shutdown order: Late->Normal->Early, got: {shutdown_order}"

    print(f"Startup order: {startup_order}")
    print(f"Shutdown order: {shutdown_order}")
    print("✅ test_lifecycle_phase_ordering passed!")


def test_service_class_uses_unified_lifecycle():
    """Test that Service class correctly inherits unified lifecycle."""
    from cullinan.service import Service
    from cullinan.core.lifecycle_enhanced import LifecycleAware, SmartLifecycle

    s = Service()

    # Service should inherit from SmartLifecycle
    assert isinstance(s, SmartLifecycle), "Service should inherit from SmartLifecycle"
    assert isinstance(s, LifecycleAware), "Service should inherit from LifecycleAware"

    # Service should have all lifecycle methods
    assert hasattr(s, 'on_post_construct')
    assert hasattr(s, 'on_startup')
    assert hasattr(s, 'on_shutdown')
    assert hasattr(s, 'on_pre_destroy')
    assert hasattr(s, 'get_phase')

    # Default phase should be 0
    assert s.get_phase() == 0

    print("✅ test_service_class_uses_unified_lifecycle passed!")


def test_no_legacy_lifecycle_methods():
    """Test that legacy lifecycle methods (on_init, on_destroy) are removed."""
    from cullinan.service import Service

    s = Service()

    # Legacy methods should NOT exist
    assert not hasattr(s, 'on_init') or not callable(getattr(s, 'on_init', None)), \
        "Legacy on_init should be removed"
    assert not hasattr(s, 'on_destroy') or not callable(getattr(s, 'on_destroy', None)), \
        "Legacy on_destroy should be removed"

    print("✅ test_no_legacy_lifecycle_methods passed!")


def test_service_registry_no_lifecycle_methods():
    """Test that ServiceRegistry no longer has lifecycle management methods."""
    from cullinan.service import ServiceRegistry, get_service_registry

    registry = get_service_registry()

    # These methods should NOT exist anymore
    assert not hasattr(registry, 'initialize_all'), \
        "ServiceRegistry.initialize_all should be removed"
    assert not hasattr(registry, 'initialize_all_async'), \
        "ServiceRegistry.initialize_all_async should be removed"
    assert not hasattr(registry, 'destroy_all'), \
        "ServiceRegistry.destroy_all should be removed"
    assert not hasattr(registry, 'destroy_all_async'), \
        "ServiceRegistry.destroy_all_async should be removed"

    print("✅ test_service_registry_no_lifecycle_methods passed!")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Testing Unified Lifecycle Management")
    print("=" * 60 + "\n")

    test_service_class_uses_unified_lifecycle()
    test_no_legacy_lifecycle_methods()
    test_service_registry_no_lifecycle_methods()
    test_unified_lifecycle_basic()
    test_lifecycle_phase_ordering()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60 + "\n")
