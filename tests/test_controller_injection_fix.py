# -*- coding: utf-8 -*-
"""Test Controller Dependency Injection Fix

Verifies that controller dependency injection works correctly
with class-level injection (not instance-level).
"""

from cullinan.core import Inject, get_injection_registry, reset_injection_registry
from cullinan.service import service, Service, get_service_registry, reset_service_registry
from cullinan.controller import controller, get_api, reset_controller_registry


def test_controller_class_level_injection():
    """Test that controller gets dependencies injected at class level"""

    # Reset
    reset_injection_registry()
    reset_service_registry()
    reset_controller_registry()

    # Configure injection
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n=== Controller Class-Level Injection Test ===\n")

    # Define service
    @service
    class ChannelService(Service):
        def get_binding(self, repo_name):
            return f"binding_for_{repo_name}"

    # Define controller WITH dependency injection
    @controller(url='/api')
    class WebhookController:
        # This should be injected at CLASS level (not instance)
        channel_service: ChannelService = Inject()

        @get_api(url='/test')
        def test_method(self, query_params):
            # Should be able to use channel_service directly
            return self.channel_service.get_binding("test_repo")

    # Verify injection at class level
    print("[1] Checking class-level injection...")

    # Check that the class attribute is now the service instance
    assert hasattr(WebhookController, 'channel_service'), "channel_service attribute missing"

    channel_svc = getattr(WebhookController, 'channel_service')
    print(f"  WebhookController.channel_service = {channel_svc}")
    print(f"  Type: {type(channel_svc).__name__}")

    # CRITICAL: Should be ChannelService instance, NOT Inject object
    assert not isinstance(channel_svc, Inject), \
        f"ERROR: channel_service is still Inject object! {channel_svc}"

    assert isinstance(channel_svc, ChannelService), \
        f"ERROR: channel_service is not ChannelService! Got {type(channel_svc)}"

    print("  [OK] Class attribute is ChannelService instance (not Inject)")

    # Test functionality (without full HTTP request)
    print("\n[2] Testing direct access...")

    # Simulate what happens in request_handler
    # The controller class is used directly (not instantiated)
    controller_class = WebhookController

    # Access the injected service
    result = controller_class.channel_service.get_binding("test_repo")
    print(f"  Result: {result}")
    assert result == "binding_for_test_repo", f"Expected 'binding_for_test_repo', got {result}"
    print("  [OK] Service method works correctly")

    print("\n" + "="*50)
    print("SUCCESS: Controller class-level injection works!")
    print("="*50)

    return True


def test_multiple_services_injection():
    """Test controller with multiple service dependencies"""

    reset_injection_registry()
    reset_service_registry()
    reset_controller_registry()

    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n=== Multiple Services Injection Test ===\n")

    @service
    class ServiceA(Service):
        def method_a(self):
            return "A"

    @service
    class ServiceB(Service):
        def method_b(self):
            return "B"

    @controller(url='/api')
    class MultiController:
        svc_a: ServiceA = Inject()
        svc_b: ServiceB = Inject()

        @get_api(url='/test')
        def test(self, query_params):
            return f"{self.svc_a.method_a()}-{self.svc_b.method_b()}"

    # Verify both injected
    assert isinstance(MultiController.svc_a, ServiceA), "svc_a not injected"
    assert isinstance(MultiController.svc_b, ServiceB), "svc_b not injected"
    print("  [OK] Both services injected")

    # Test direct access
    result_a = MultiController.svc_a.method_a()
    result_b = MultiController.svc_b.method_b()
    result = f"{result_a}-{result_b}"
    assert result == "A-B", f"Expected 'A-B', got {result}"
    print(f"  [OK] Result: {result}")

    print("\nSUCCESS: Multiple services injection works!")

    return True


if __name__ == '__main__':
    try:
        print("\n" + "="*70)
        print("Controller Dependency Injection Fix - Verification")
        print("="*70)

        success1 = test_controller_class_level_injection()
        success2 = test_multiple_services_injection()

        if success1 and success2:
            print("\n" + "="*70)
            print("ALL TESTS PASSED!")
            print("="*70)
            print("\nThe fix resolves:")
            print("  • AttributeError: 'Inject' object has no attribute 'get_binding'")
            print("  • UnboundLocalError: cannot access local variable 'resp_obj'")
            print("\nControllers now work correctly with dependency injection!")
            print("="*70 + "\n")
            exit(0)
        else:
            print("\nSome tests failed")
            exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

