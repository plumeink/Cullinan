#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Integration Test for Cullinan Framework After Legacy Cleanup

This script tests all critical functionality to ensure nothing was broken
by the legacy code cleanup.
"""

import sys
import os
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test results tracking
tests_passed = 0
tests_failed = 0
test_details = []


def test(description):
    """Decorator for test functions."""
    def decorator(func):
        def wrapper():
            global tests_passed, tests_failed, test_details
            try:
                func()
                tests_passed += 1
                test_details.append(('PASS', description))
                print(f"✓ {description}")
                return True
            except Exception as e:
                tests_failed += 1
                test_details.append(('FAIL', description, str(e)))
                print(f"✗ {description}")
                print(f"  Error: {e}")
                traceback.print_exc()
                return False
        return wrapper
    return decorator


print("=" * 80)
print("CULLINAN FRAMEWORK - COMPREHENSIVE INTEGRATION TEST")
print("=" * 80)
print()

# ============================================================================
# Test 1: Core Imports
# ============================================================================
print("TEST CATEGORY 1: Core Imports")
print("-" * 80)

@test("Import main cullinan package")
def test_import_main():
    import cullinan
    assert cullinan.__version__ == '0.76'

test_import_main()

@test("Import core module")
def test_import_core():
    from cullinan import core
    assert hasattr(core, 'Registry')
    assert hasattr(core, 'DependencyInjector')
    assert hasattr(core, 'LifecycleManager')

test_import_core()

@test("Import service module")
def test_import_service():
    from cullinan import Service, ServiceRegistry
    assert Service is not None
    assert ServiceRegistry is not None

test_import_service()

@test("Import handler module")
def test_import_handler():
    from cullinan import handler
    assert hasattr(handler, 'HandlerRegistry')
    assert hasattr(handler, 'BaseHandler')

test_import_handler()

@test("Import monitoring module")
def test_import_monitoring():
    from cullinan import monitoring
    assert hasattr(monitoring, 'MonitoringHook')
    assert hasattr(monitoring, 'MonitoringManager')

test_import_monitoring()

print()

# ============================================================================
# Test 2: Legacy Code Cleanup Verification
# ============================================================================
print("TEST CATEGORY 2: Legacy Code Cleanup Verification")
print("-" * 80)

@test("Verify cullinan/hooks.py is removed")
def test_hooks_removed():
    import cullinan
    cullinan_path = os.path.dirname(cullinan.__file__)
    hooks_path = os.path.join(cullinan_path, 'hooks.py')
    assert not os.path.exists(hooks_path), "hooks.py should not exist"

test_hooks_removed()

@test("Verify MissingHeaderHandlerHook is not in namespace")
def test_no_old_hook():
    import cullinan
    assert not hasattr(cullinan, 'MissingHeaderHandlerHook')

test_no_old_hook()

@test("Verify monitoring/hooks.py exists (new module)")
def test_monitoring_hooks_exists():
    from cullinan.monitoring import hooks
    assert hasattr(hooks, 'MonitoringHook')
    assert hasattr(hooks, 'MonitoringManager')

test_monitoring_hooks_exists()

print()

# ============================================================================
# Test 3: New Missing Header Handler API
# ============================================================================
print("TEST CATEGORY 3: New Missing Header Handler API")
print("-" * 80)

@test("Import missing header handler functions")
def test_import_handler_functions():
    from cullinan import set_missing_header_handler, get_missing_header_handler
    assert callable(set_missing_header_handler)
    assert callable(get_missing_header_handler)

test_import_handler_functions()

@test("Get default missing header handler")
def test_get_default_handler():
    from cullinan import get_missing_header_handler
    handler = get_missing_header_handler()
    assert handler is not None
    assert callable(handler)

test_get_default_handler()

@test("Set custom missing header handler")
def test_set_custom_handler():
    from cullinan import set_missing_header_handler, get_missing_header_handler

    custom_calls = []
    def custom_handler(request, header_name):
        custom_calls.append(header_name)

    set_missing_header_handler(custom_handler)
    handler = get_missing_header_handler()
    assert handler == custom_handler

    # Test it works
    handler('mock_request', 'X-Test')
    assert len(custom_calls) == 1
    assert custom_calls[0] == 'X-Test'

test_set_custom_handler()

@test("Default handler raises MissingHeaderException")
def test_default_raises_exception():
    from cullinan import get_missing_header_handler, set_missing_header_handler
    from cullinan.exceptions import MissingHeaderException

    # Reset to a fresh default handler that raises exception
    def default_handler(request, header_name):
        raise MissingHeaderException(header_name=header_name)

    set_missing_header_handler(default_handler)

    # Get the current handler through public API
    handler = get_missing_header_handler()

    try:
        handler('request', 'X-Missing')
        assert False, "Should have raised exception"
    except MissingHeaderException as e:
        assert e.header_name == 'X-Missing'

test_default_raises_exception()

print()

# ============================================================================
# Test 4: Core Module Functionality
# ============================================================================
print("TEST CATEGORY 4: Core Module Functionality")
print("-" * 80)

@test("SimpleRegistry - register and get")
def test_simple_registry():
    from cullinan.core import SimpleRegistry

    registry = SimpleRegistry()
    registry.register('test_item', 'test_value')

    assert registry.has('test_item')
    assert registry.get('test_item') == 'test_value'
    assert 'test_item' in registry.list_all()

test_simple_registry()

@test("DependencyInjector - register and resolve")
def test_dependency_injector():
    from cullinan.core import DependencyInjector

    injector = DependencyInjector()
    injector.register_provider('dep1', lambda: 'value1')

    result = injector.resolve('dep1')
    assert result == 'value1'

test_dependency_injector()

@test("LifecycleManager - basic lifecycle")
def test_lifecycle_manager():
    from cullinan.core import LifecycleManager, LifecycleState

    manager = LifecycleManager()

    init_called = []

    class Component:
        def on_init(self):
            init_called.append(True)

    component = Component()
    manager.register_component('comp1', component)
    manager.initialize_all()

    assert len(init_called) == 1
    assert manager.get_state('comp1') == LifecycleState.INITIALIZED

test_lifecycle_manager()

@test("RequestContext - set and get")
def test_request_context():
    from cullinan.core import RequestContext

    context = RequestContext()
    context.set('key1', 'value1')

    assert context.has('key1')
    assert context.get('key1') == 'value1'

test_request_context()

print()

# ============================================================================
# Test 5: Service Layer
# ============================================================================
print("TEST CATEGORY 5: Service Layer")
print("-" * 80)

@test("Service registration with @service decorator")
def test_service_registration():
    from cullinan import Service, service, get_service_registry, reset_service_registry

    reset_service_registry()

    @service
    class TestService(Service):
        def get_data(self):
            return "test_data"

    registry = get_service_registry()
    assert registry.has('TestService')

    instance = registry.get_instance('TestService')
    assert instance.get_data() == "test_data"

test_service_registration()

@test("Service with lifecycle hooks")
def test_service_lifecycle():
    from cullinan import Service, service, get_service_registry, reset_service_registry

    reset_service_registry()

    init_calls = []

    @service
    class LifecycleService(Service):
        def on_init(self):
            init_calls.append('init')

    registry = get_service_registry()
    registry.initialize_all()  # Need to call this to trigger on_init
    instance = registry.get_instance('LifecycleService')

    assert len(init_calls) == 1

test_service_lifecycle()

@test("Service with dependencies")
def test_service_dependencies():
    from cullinan import Service, service, get_service_registry, reset_service_registry

    reset_service_registry()

    @service
    class ServiceA(Service):
        def get_value(self):
            return "A"

    @service(dependencies=['ServiceA'])
    class ServiceB(Service):
        def on_init(self):
            self.service_a = self.dependencies['ServiceA']

        def get_combined(self):
            return f"B+{self.service_a.get_value()}"

    registry = get_service_registry()
    registry.initialize_all()  # Need to call this to trigger on_init
    instance_b = registry.get_instance('ServiceB')

    assert instance_b.get_combined() == "B+A"

test_service_dependencies()

print()

# ============================================================================
# Test 6: Handler Module
# ============================================================================
print("TEST CATEGORY 6: Handler Module")
print("-" * 80)

@test("HandlerRegistry - register and get")
def test_handler_registry():
    from cullinan import HandlerRegistry, reset_handler_registry

    reset_handler_registry()
    registry = HandlerRegistry()

    class MockHandler:
        pass

    registry.register('/api/test', MockHandler)
    handlers = registry.get_handlers()

    assert len(handlers) == 1
    assert handlers[0][0] == '/api/test'

test_handler_registry()

@test("Get global handler registry")
def test_get_handler_registry():
    from cullinan import get_handler_registry

    registry = get_handler_registry()
    assert registry is not None

test_get_handler_registry()

print()

# ============================================================================
# Test 7: Backward Compatibility
# ============================================================================
print("TEST CATEGORY 7: Backward Compatibility")
print("-" * 80)

@test("Old registry module has been removed")
def test_registry_module_removed():
    """Test that cullinan.registry module no longer exists."""
    try:
        from cullinan import registry
        assert False, "registry module should have been removed"
    except (ImportError, AttributeError):
        # This is expected - module should not exist
        pass

test_registry_module_removed()

@test("Old websocket module has been removed")
def test_websocket_module_removed():
    """Test that cullinan.websocket module no longer exists."""
    try:
        from cullinan.websocket import websocket
        assert False, "websocket module should have been removed"
    except ImportError:
        # This is expected - module should not exist
        pass

test_websocket_module_removed()

print()

# ============================================================================
# Test 8: WebSocket Registry
# ============================================================================
print("TEST CATEGORY 8: WebSocket Support")
print("-" * 80)

@test("WebSocket registry and decorator")
def test_websocket_registry():
    from cullinan import WebSocketRegistry, websocket_handler, reset_websocket_registry

    reset_websocket_registry()

    @websocket_handler(url='/ws/chat')
    class ChatHandler:
        pass

    from cullinan import get_websocket_registry
    registry = get_websocket_registry()

    assert registry.has('ChatHandler')

test_websocket_registry()

print()

# ============================================================================
# Test 9: Monitoring Module
# ============================================================================
print("TEST CATEGORY 9: Monitoring Module")
print("-" * 80)

@test("MonitoringHook and MonitoringManager")
def test_monitoring():
    from cullinan import MonitoringHook, MonitoringManager

    calls = []

    class TestHook(MonitoringHook):
        def on_service_init(self, service_name, service):
            calls.append(('init', service_name))

    manager = MonitoringManager()
    hook = TestHook()
    manager.register(hook)

    manager.on_service_init('TestService', None)

    assert len(calls) == 1
    assert calls[0] == ('init', 'TestService')

test_monitoring()

print()

# ============================================================================
# Test 10: Exception Hierarchy
# ============================================================================
print("TEST CATEGORY 10: Exception Hierarchy")
print("-" * 80)

@test("MissingHeaderException exists and works")
def test_missing_header_exception():
    from cullinan.exceptions import MissingHeaderException, RequestError

    exc = MissingHeaderException('X-API-Key')

    assert exc.header_name == 'X-API-Key'
    assert exc.error_code == 'MISSING_HEADER'
    assert isinstance(exc, RequestError)

test_missing_header_exception()

@test("CullinanError hierarchy")
def test_error_hierarchy():
    from cullinan.exceptions import (
        CullinanError, ConfigurationError,
        RequestError, ServiceError
    )

    assert issubclass(ConfigurationError, CullinanError)
    assert issubclass(RequestError, CullinanError)
    assert issubclass(ServiceError, CullinanError)

test_error_hierarchy()

print()

# ============================================================================
# Final Results
# ============================================================================
print("=" * 80)
print("TEST RESULTS SUMMARY")
print("=" * 80)
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Total Tests:  {tests_passed + tests_failed}")
print(f"Success Rate: {100 * tests_passed / (tests_passed + tests_failed):.1f}%")
print()

if tests_failed > 0:
    print("FAILED TESTS:")
    for detail in test_details:
        if detail[0] == 'FAIL':
            print(f"  ✗ {detail[1]}")
            if len(detail) > 2:
                print(f"    {detail[2]}")
    print()

# Exit with appropriate code
if tests_failed == 0:
    print("✓ ALL TESTS PASSED!")
    print()
    sys.exit(0)
else:
    print("✗ SOME TESTS FAILED")
    print()
    sys.exit(1)

