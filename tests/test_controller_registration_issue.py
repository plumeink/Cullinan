# -*- coding: utf-8 -*-
"""Test Controller Registration Issue"""

from cullinan.core import Inject
from cullinan.service import service, Service, get_service_registry, reset_service_registry
from cullinan.controller import controller, get_controller_registry, reset_controller_registry
from cullinan.handler import get_handler_registry, reset_handler_registry
from cullinan.core import get_injection_registry, reset_injection_registry


def test_controller_registration():
    """Test that controllers are properly registered"""

    # Reset all registries
    reset_injection_registry()
    reset_service_registry()
    reset_controller_registry()
    reset_handler_registry()

    # Configure injection
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    # Define a service
    @service
    class TestService(Service):
        def get_data(self):
            return "test data"

    # Define a controller
    @controller(url='/api/test')
    class TestController:
        test_service: TestService = Inject()

        def index(self):
            return {"message": "Hello"}

    # Check registrations
    controller_registry = get_controller_registry()
    handler_registry = get_handler_registry()

    print("\n=== Controller Registration Test ===")
    print(f"Controller registered: {controller_registry.has('TestController')}")
    print(f"Controller count: {controller_registry.count()}")
    print(f"Handler count: {handler_registry.count()}")
    print(f"Handlers: {handler_registry.get_handlers()}")

    if not controller_registry.has('TestController'):
        print("\nERROR: Controller not registered!")
        return False

    if handler_registry.count() == 0:
        print("\nERROR: No handlers registered!")
        return False

    print("\nSUCCESS: Controller properly registered")
    return True


if __name__ == '__main__':
    success = test_controller_registration()
    if not success:
        print("\n[FAIL] Controller registration test failed")
        exit(1)
    else:
        print("\n[OK] Controller registration test passed")
        exit(0)

