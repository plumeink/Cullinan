# -*- coding: utf-8 -*-
"""Test to diagnose @component decorator registration issue."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_component_decorator_registration():
    """Test that @component decorator correctly registers to PendingRegistry."""
    from cullinan.core.pending import PendingRegistry, ComponentType
    from cullinan.core.decorators import component, service, controller

    # Reset PendingRegistry
    PendingRegistry.reset()

    # Define test classes with decorators
    @service
    class TestService:
        pass

    @controller
    class TestController:
        pass

    @component
    class TestComponent:
        pass

    @component(name="CustomComponent")
    class TestComponentWithName:
        pass

    # Check PendingRegistry
    pending = PendingRegistry.get_instance()
    all_registrations = pending.get_all()

    print(f"\nTotal registrations: {len(all_registrations)}")

    for reg in all_registrations:
        print(f"  - {reg.name}: type={reg.component_type.value}, scope={reg.scope}")

    # Verify all types are present
    services = pending.get_by_type(ComponentType.SERVICE)
    controllers = pending.get_by_type(ComponentType.CONTROLLER)
    components = pending.get_by_type(ComponentType.COMPONENT)

    print(f"\nBy type:")
    print(f"  Services: {len(services)}")
    print(f"  Controllers: {len(controllers)}")
    print(f"  Components: {len(components)}")

    assert len(services) == 1, f"Expected 1 service, got {len(services)}"
    assert len(controllers) == 1, f"Expected 1 controller, got {len(controllers)}"
    assert len(components) == 2, f"Expected 2 components, got {len(components)}"

    # Check names
    service_names = [s.name for s in services]
    controller_names = [c.name for c in controllers]
    component_names = [c.name for c in components]

    assert 'TestService' in service_names
    assert 'TestController' in controller_names
    assert 'TestComponent' in component_names
    assert 'CustomComponent' in component_names

    print("\n✅ test_component_decorator_registration passed!")


def test_component_processed_by_application_context():
    """Test that @component is processed by ApplicationContext.refresh()."""
    from cullinan.core import ApplicationContext, set_application_context
    from cullinan.core.pending import PendingRegistry, ComponentType
    from cullinan.core.decorators import component, service

    # Reset state
    PendingRegistry.reset()

    lifecycle_log = []

    # Define test components
    @service
    class MyService:
        def on_post_construct(self):
            lifecycle_log.append('MyService.on_post_construct')

    @component
    class MyComponent:
        def on_post_construct(self):
            lifecycle_log.append('MyComponent.on_post_construct')

    # Create and refresh ApplicationContext
    ctx = ApplicationContext()
    set_application_context(ctx)
    ctx.refresh()

    # Check that both are registered
    definitions = ctx.list_definitions()
    print(f"\nRegistered definitions: {definitions}")

    assert 'MyService' in definitions, "MyService should be in definitions"
    assert 'MyComponent' in definitions, "MyComponent should be in definitions"

    # Check that lifecycle was called for both
    print(f"Lifecycle log: {lifecycle_log}")

    # The component should have on_post_construct called if it's a LifecycleAware
    # Since MyComponent doesn't inherit from SmartLifecycle, it may not be called
    # Let's check if get() works

    service_instance = ctx.get('MyService')
    component_instance = ctx.get('MyComponent')

    print(f"MyService instance: {service_instance}")
    print(f"MyComponent instance: {component_instance}")

    assert service_instance is not None, "MyService instance should not be None"
    assert component_instance is not None, "MyComponent instance should not be None"

    ctx.shutdown()

    print("\n✅ test_component_processed_by_application_context passed!")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Diagnosing @component decorator registration")
    print("=" * 60)

    test_component_decorator_registration()
    test_component_processed_by_application_context()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60 + "\n")
