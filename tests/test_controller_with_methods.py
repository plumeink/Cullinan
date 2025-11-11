# -*- coding: utf-8 -*-
"""Test with actual method decorators"""

from cullinan.core import Inject
from cullinan.service import service, Service, get_service_registry, reset_service_registry
from cullinan.controller import controller, get_api, post_api, get_controller_registry, reset_controller_registry
from cullinan.handler import get_handler_registry, reset_handler_registry
from cullinan.core import get_injection_registry, reset_injection_registry


def test_controller_with_methods():
    """Test controller with method decorators"""
    
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
    
    # Define a controller WITH method decorators
    @controller(url='/api/test')
    class TestController:
        test_service: TestService = Inject()
        
        @get_api(url='')
        def index(self):
            return {"message": "Hello"}
        
        @post_api(url='/create')
        def create(self, body_params):
            return {"created": True}
    
    # Check registrations
    controller_registry = get_controller_registry()
    handler_registry = get_handler_registry()
    
    print("\n=== Controller with Methods Test ===")
    print(f"Controller registered: {controller_registry.has('TestController')}")
    print(f"Controller count: {controller_registry.count()}")
    print(f"Controller methods: {controller_registry.get_method_count('TestController')}")
    print(f"Handler count: {handler_registry.count()}")
    
    handlers = handler_registry.get_handlers()
    print(f"\nRegistered handlers:")
    for url, servlet in handlers:
        print(f"  {url} -> {servlet}")
    
    success = True
    if not controller_registry.has('TestController'):
        print("\nERROR: Controller not registered!")
        success = False
    
    if controller_registry.get_method_count('TestController') == 0:
        print("\nERROR: No methods registered in controller!")
        success = False
    
    if handler_registry.count() == 0:
        print("\nERROR: No handlers registered!")
        success = False
    
    if success:
        print("\nSUCCESS: Controller with methods properly registered")
    
    return success


if __name__ == '__main__':
    success = test_controller_with_methods()
    if not success:
        print("\n[FAIL] Test failed")
        exit(1)
    else:
        print("\n[OK] Test passed")
        exit(0)

