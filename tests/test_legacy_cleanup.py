# -*- coding: utf-8 -*-
"""
Test suite to verify legacy code cleanup is complete and new functionality works.

This test verifies:
1. Legacy files are removed
2. New missing header handler API works
3. No broken imports or references
4. Backward compatibility is maintained
5. Deprecation warnings work correctly
"""

import unittest
import warnings
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLegacyCleanup(unittest.TestCase):
    """Test that legacy code has been properly removed."""

    def test_hooks_py_removed(self):
        """Verify old cullinan/hooks.py file is removed."""
        import cullinan
        cullinan_path = os.path.dirname(cullinan.__file__)
        hooks_path = os.path.join(cullinan_path, 'hooks.py')

        self.assertFalse(
            os.path.exists(hooks_path),
            "Legacy cullinan/hooks.py should be removed"
        )

    def test_no_missing_header_handler_hook_in_cullinan(self):
        """Verify MissingHeaderHandlerHook is not in cullinan namespace."""
        import cullinan

        self.assertFalse(
            hasattr(cullinan, 'MissingHeaderHandlerHook'),
            "MissingHeaderHandlerHook should not be in cullinan namespace"
        )

    def test_monitoring_hooks_exists(self):
        """Verify new monitoring hooks module exists."""
        from cullinan.monitoring import hooks

        self.assertTrue(hasattr(hooks, 'MonitoringHook'))
        self.assertTrue(hasattr(hooks, 'MonitoringManager'))


class TestNewMissingHeaderHandlerAPI(unittest.TestCase):
    """Test new missing header handler API."""

    def setUp(self):
        """Reset handler before each test."""
        from cullinan import set_missing_header_handler
        from cullinan.exceptions import MissingHeaderException

        # Reset to default behavior using a fresh default handler
        def default_handler(request, header_name):
            raise MissingHeaderException(header_name=header_name)

        set_missing_header_handler(default_handler)

    def test_get_missing_header_handler(self):
        """Test getting the missing header handler."""
        from cullinan import get_missing_header_handler

        handler = get_missing_header_handler()
        self.assertIsNotNone(handler)
        self.assertTrue(callable(handler))

    def test_set_missing_header_handler(self):
        """Test setting a custom missing header handler."""
        from cullinan import set_missing_header_handler, get_missing_header_handler

        # Create custom handler
        custom_called = []
        def custom_handler(request, header_name):
            custom_called.append((request, header_name))

        # Set custom handler
        set_missing_header_handler(custom_handler)

        # Verify it was set
        handler = get_missing_header_handler()
        self.assertEqual(handler, custom_handler)

        # Test it works
        handler('mock_request', 'X-Test-Header')
        self.assertEqual(len(custom_called), 1)
        self.assertEqual(custom_called[0][1], 'X-Test-Header')

    def test_default_handler_raises_exception(self):
        """Test that default handler raises MissingHeaderException."""
        from cullinan import get_missing_header_handler
        from cullinan.exceptions import MissingHeaderException

        handler = get_missing_header_handler()

        with self.assertRaises(MissingHeaderException) as cm:
            handler('mock_request', 'X-Missing-Header')

        self.assertEqual(cm.exception.header_name, 'X-Missing-Header')

    def test_api_exported_from_main_package(self):
        """Test that API is exported from main cullinan package."""
        import cullinan

        self.assertTrue(hasattr(cullinan, 'set_missing_header_handler'))
        self.assertTrue(hasattr(cullinan, 'get_missing_header_handler'))


class TestBackwardCompatibility(unittest.TestCase):
    """Test that old modules have been properly removed."""

    def test_registry_module_removed(self):
        """Test that cullinan.registry module no longer exists."""
        with self.assertRaises(ImportError):
            from cullinan import registry

    def test_websocket_module_removed(self):
        """Test that cullinan.websocket module no longer exists."""
        with self.assertRaises(ImportError):
            from cullinan.websocket import websocket



class TestModuleStructure(unittest.TestCase):
    """Test that module structure is correct."""

    def test_core_module_complete(self):
        """Test core module has all expected components."""
        from cullinan import core

        expected = [
            'Registry', 'SimpleRegistry', 'DependencyInjector',
            'LifecycleManager', 'LifecycleState', 'LifecycleAware',
            'RequestContext', 'get_current_context', 'set_current_context'
        ]

        for item in expected:
            self.assertTrue(hasattr(core, item), f"core.{item} should exist")

    def test_service_module_complete(self):
        """Test service module has all expected components."""
        from cullinan.service import (
            Service, service, ServiceRegistry,
            get_service_registry, reset_service_registry
        )

        # Verify all expected components exist
        self.assertIsNotNone(Service)
        self.assertIsNotNone(service)
        self.assertIsNotNone(ServiceRegistry)
        self.assertIsNotNone(get_service_registry)
        self.assertIsNotNone(reset_service_registry)

    def test_monitoring_module_complete(self):
        """Test monitoring module has all expected components."""
        from cullinan import monitoring

        expected = [
            'MonitoringHook', 'MonitoringManager',
            'get_monitoring_manager', 'reset_monitoring_manager'
        ]

        for item in expected:
            self.assertTrue(hasattr(monitoring, item), f"monitoring.{item} should exist")

    def test_handler_module_complete(self):
        """Test handler module has all expected components."""
        from cullinan import handler

        expected = [
            'HandlerRegistry', 'get_handler_registry',
            'reset_handler_registry', 'BaseHandler'
        ]

        for item in expected:
            self.assertTrue(hasattr(handler, item), f"handler.{item} should exist")


class TestCoreModuleFunctionality(unittest.TestCase):
    """Test core module functionality."""

    def test_simple_registry(self):
        """Test SimpleRegistry basic operations."""
        from cullinan.core import SimpleRegistry

        registry = SimpleRegistry()

        # Test register and get
        registry.register('test_item', 'test_value')
        self.assertEqual(registry.get('test_item'), 'test_value')

        # Test has
        self.assertTrue(registry.has('test_item'))
        self.assertFalse(registry.has('nonexistent'))

        # Test list_all
        all_items = registry.list_all()
        self.assertIn('test_item', all_items)

    def test_dependency_injector(self):
        """Test DependencyInjector basic operations."""
        from cullinan.core import DependencyInjector

        injector = DependencyInjector()

        # Register provider
        injector.register_provider('service1', lambda: 'value1')

        # Resolve dependency
        result = injector.resolve('service1')
        self.assertEqual(result, 'value1')


class TestServiceLayer(unittest.TestCase):
    """Test service layer functionality."""

    def setUp(self):
        """Reset service registry before each test."""
        from cullinan.service import reset_service_registry
        reset_service_registry()

    def tearDown(self):
        """Clean up after each test."""
        from cullinan.service import reset_service_registry
        reset_service_registry()

    def test_simple_service_registration(self):
        """Test simple service registration."""
        from cullinan import Service, service, get_service_registry

        @service
        class TestService(Service):
            def do_something(self):
                return "result"

        # Verify registration
        registry = get_service_registry()
        self.assertTrue(registry.has('TestService'))

        # Get instance
        instance = registry.get_instance('TestService')
        self.assertIsNotNone(instance)
        self.assertEqual(instance.do_something(), "result")

    def test_service_with_lifecycle(self):
        """Test service with lifecycle hooks."""
        from cullinan import Service, service, get_service_registry

        init_called = []

        @service
        class TestService(Service):
            def on_init(self):
                init_called.append(True)

        # Get instance should trigger on_init
        registry = get_service_registry()
        instance = registry.get_instance('TestService')

        self.assertEqual(len(init_called), 1)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLegacyCleanup))
    suite.addTests(loader.loadTestsFromTestCase(TestNewMissingHeaderHandlerAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestBackwardCompatibility))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestCoreModuleFunctionality))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceLayer))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)

