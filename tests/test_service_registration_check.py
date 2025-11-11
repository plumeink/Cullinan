# -*- coding: utf-8 -*-
"""Test Service Registration"""

from cullinan.core import Inject
from cullinan.service import service, Service, get_service_registry, reset_service_registry
from cullinan.core import get_injection_registry, reset_injection_registry


def test_service_registration():
    """Test that services are properly registered and injectable"""

    # Reset
    reset_injection_registry()
    reset_service_registry()

    # Configure injection
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n=== Service Registration Test ===")

    # Test 1: Basic service registration
    @service
    class ServiceA(Service):
        def method_a(self):
            return "A"

    assert service_registry.has('ServiceA'), "ServiceA not registered"
    print("OK: Basic service registration")

    # Test 2: Service with dependency
    @service
    class ServiceB(Service):
        a: ServiceA = Inject()

        def method_b(self):
            return f"B+{self.a.method_a()}"

    assert service_registry.has('ServiceB'), "ServiceB not registered"
    print("OK: Service with dependency registered")

    # Test 3: Get instance and check injection
    b_instance = service_registry.get_instance('ServiceB')
    assert b_instance is not None, "Failed to get ServiceB instance"
    assert hasattr(b_instance, 'a'), "ServiceB doesn't have 'a' attribute"
    assert isinstance(b_instance.a, ServiceA), "ServiceB.a is not ServiceA instance"
    print("OK: Service instance created with dependency injected")

    # Test 4: Functionality
    result = b_instance.method_b()
    assert result == "B+A", f"Expected 'B+A', got '{result}'"
    print("OK: Service functionality works")

    # Test 5: Dependency chain
    @service
    class ServiceC(Service):
        b: ServiceB = Inject()

        def method_c(self):
            return f"C+{self.b.method_b()}"

    c_instance = service_registry.get_instance('ServiceC')
    assert isinstance(c_instance.b, ServiceB), "ServiceC.b is not ServiceB"
    assert isinstance(c_instance.b.a, ServiceA), "ServiceC.b.a is not ServiceA"

    result = c_instance.method_c()
    assert result == "C+B+A", f"Expected 'C+B+A', got '{result}'"
    print("OK: Dependency chain works")

    print("\nSUCCESS: All service registration tests passed")
    return True


if __name__ == '__main__':
    try:
        success = test_service_registration()
        if success:
            print("\n[OK] Service registration test passed")
            exit(0)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

