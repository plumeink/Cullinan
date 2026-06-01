# -*- coding: utf-8 -*-
"""Test to diagnose @component decorator registration issue."""

import pytest

pytestmark = pytest.mark.filterwarnings(
    "ignore::cullinan.core.semantic_rules.ComponentDiscoveryWarning"
)


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

    # Verify all types are present
    services = pending.get_by_type(ComponentType.SERVICE)
    controllers = pending.get_by_type(ComponentType.CONTROLLER)
    components = pending.get_by_type(ComponentType.COMPONENT)

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

    assert 'MyService' in definitions, "MyService should be in definitions"
    assert 'MyComponent' in definitions, "MyComponent should be in definitions"

    service_instance = ctx.get('MyService')
    component_instance = ctx.get('MyComponent')

    assert service_instance is not None, "MyService instance should not be None"
    assert component_instance is not None, "MyComponent instance should not be None"

    ctx.shutdown()
