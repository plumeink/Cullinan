# -*- coding: utf-8 -*-
"""Test unified registration using cullinan.core.Registry for both services and controllers.

This test verifies that both ServiceRegistry and ControllerRegistry properly
use the cullinan.core.Registry pattern, abandoning their own registration logic.
"""

import unittest
from cullinan.core import Registry
from cullinan.service import ServiceRegistry, get_service_registry, reset_service_registry, Service, service
from cullinan.controller import ControllerRegistry, get_controller_registry, reset_controller_registry


class TestUnifiedRegistration(unittest.TestCase):
    """Test that services and controllers use unified core.Registry."""

    def setUp(self):
        """Reset registries before each test."""
        reset_service_registry()
        reset_controller_registry()

    def tearDown(self):
        """Clean up after each test."""
        reset_service_registry()
        reset_controller_registry()

    def test_service_registry_inherits_from_core_registry(self):
        """Test that ServiceRegistry inherits from core.Registry."""
        registry = get_service_registry()
        self.assertIsInstance(registry, Registry)
        self.assertIsInstance(registry, ServiceRegistry)

    def test_controller_registry_inherits_from_core_registry(self):
        """Test that ControllerRegistry inherits from core.Registry."""
        registry = get_controller_registry()
        self.assertIsInstance(registry, Registry)
        self.assertIsInstance(registry, ControllerRegistry)

    def test_service_registry_uses_core_methods(self):
        """Test that ServiceRegistry uses core Registry methods."""
        registry = get_service_registry()

        # Test core Registry methods are available
        self.assertTrue(hasattr(registry, 'register'))
        self.assertTrue(hasattr(registry, 'get'))
        self.assertTrue(hasattr(registry, 'has'))
        self.assertTrue(hasattr(registry, 'list_all'))
        self.assertTrue(hasattr(registry, 'clear'))
        self.assertTrue(hasattr(registry, 'count'))

        # Test registration works
        class TestService(Service):
            pass

        registry.register('TestService', TestService)
        self.assertTrue(registry.has('TestService'))
        self.assertEqual(registry.count(), 1)
        self.assertIn('TestService', registry.list_all())

    def test_controller_registry_uses_core_methods(self):
        """Test that ControllerRegistry uses core Registry methods."""
        registry = get_controller_registry()

        # Test core Registry methods are available
        self.assertTrue(hasattr(registry, 'register'))
        self.assertTrue(hasattr(registry, 'get'))
        self.assertTrue(hasattr(registry, 'has'))
        self.assertTrue(hasattr(registry, 'list_all'))
        self.assertTrue(hasattr(registry, 'clear'))
        self.assertTrue(hasattr(registry, 'count'))

        # Test registration works
        class TestController:
            pass

        registry.register('TestController', TestController, url_prefix='/api/test')
        self.assertTrue(registry.has('TestController'))
        self.assertEqual(registry.count(), 1)
        self.assertIn('TestController', registry.list_all())

    def test_service_decorator_uses_registry(self):
        """Test that @service decorator uses ServiceRegistry."""
        registry = get_service_registry()

        @service
        class EmailService(Service):
            def send_email(self, to, subject):
                return f"Email to {to}"

        # Verify service was registered
        self.assertTrue(registry.has('EmailService'))
        self.assertEqual(registry.count(), 1)

        # Verify we can get the service class
        service_class = registry.get('EmailService')
        self.assertEqual(service_class, EmailService)

    def test_service_with_dependencies_uses_registry(self):
        """Test that services with dependencies use ServiceRegistry."""
        registry = get_service_registry()

        @service
        class DatabaseService(Service):
            def connect(self):
                return "Connected"

        @service(dependencies=['DatabaseService'])
        class UserService(Service):
            def on_init(self):
                self.db = self.dependencies.get('DatabaseService')

        # Verify both services were registered
        self.assertTrue(registry.has('DatabaseService'))
        self.assertTrue(registry.has('UserService'))
        self.assertEqual(registry.count(), 2)

        # Verify dependencies metadata
        metadata = registry.get_metadata('UserService')
        self.assertIsNotNone(metadata)
        self.assertIn('dependencies', metadata)
        self.assertEqual(metadata['dependencies'], ['DatabaseService'])

    def test_controller_method_registration_uses_registry(self):
        """Test that controller method registration uses ControllerRegistry."""
        registry = get_controller_registry()

        class TestController:
            def list_items(self):
                return []

        # Register controller
        registry.register('TestController', TestController, url_prefix='/api')

        # Register methods
        registry.register_method('TestController', '/items', 'get', TestController.list_items)
        registry.register_method('TestController', '/items', 'post', TestController.list_items)

        # Verify methods were registered
        methods = registry.get_methods('TestController')
        self.assertEqual(len(methods), 2)

        # Verify method details
        urls = [m[0] for m in methods]
        http_methods = [m[1] for m in methods]
        self.assertIn('/items', urls)
        self.assertIn('get', http_methods)
        self.assertIn('post', http_methods)

    def test_registries_are_independent(self):
        """Test that service and controller registries are independent."""
        service_registry = get_service_registry()
        controller_registry = get_controller_registry()

        # Register in both
        @service
        class MyService(Service):
            pass

        class MyController:
            pass

        controller_registry.register('MyController', MyController)

        # Verify they don't interfere with each other
        self.assertEqual(service_registry.count(), 1)
        self.assertEqual(controller_registry.count(), 1)
        self.assertTrue(service_registry.has('MyService'))
        self.assertTrue(controller_registry.has('MyController'))
        self.assertFalse(service_registry.has('MyController'))
        self.assertFalse(controller_registry.has('MyService'))

    def test_registry_clear_works(self):
        """Test that clearing registries works properly."""
        service_registry = get_service_registry()
        controller_registry = get_controller_registry()

        # Register items
        @service
        class TestService(Service):
            pass

        class TestController:
            pass

        controller_registry.register('TestController', TestController)

        # Verify they're registered
        self.assertEqual(service_registry.count(), 1)
        self.assertEqual(controller_registry.count(), 1)

        # Clear and verify
        service_registry.clear()
        controller_registry.clear()

        self.assertEqual(service_registry.count(), 0)
        self.assertEqual(controller_registry.count(), 0)

    def test_no_legacy_registration_logic(self):
        """Test that legacy registration logic (global lists) is not used."""
        # Verify that controller_func_list is not used globally
        from cullinan import controller as ctrl_module

        # The old controller_func_list should not be in use
        # It should be replaced by context variable
        self.assertFalse(hasattr(ctrl_module, 'controller_func_list') and
                        isinstance(getattr(ctrl_module, 'controller_func_list', None), list))


class TestRegistryIntegration(unittest.TestCase):
    """Test integration between registries and core components."""

    def setUp(self):
        """Reset registries before each test."""
        reset_service_registry()
        reset_controller_registry()

    def tearDown(self):
        """Clean up after each test."""
        reset_service_registry()
        reset_controller_registry()

    def test_service_registry_metadata(self):
        """Test that ServiceRegistry properly stores and retrieves metadata."""
        registry = get_service_registry()

        class TestService(Service):
            pass

        registry.register('TestService', TestService,
                         dependencies=['OtherService'],
                         custom_meta='test_value')

        metadata = registry.get_metadata('TestService')
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['dependencies'], ['OtherService'])
        self.assertEqual(metadata['custom_meta'], 'test_value')

    def test_controller_registry_url_prefix(self):
        """Test that ControllerRegistry properly stores URL prefixes."""
        registry = get_controller_registry()

        class UserController:
            pass

        registry.register('UserController', UserController, url_prefix='/api/v1/users')

        prefix = registry.get_url_prefix('UserController')
        self.assertEqual(prefix, '/api/v1/users')

    def test_registry_error_handling(self):
        """Test that registries properly handle errors."""
        from cullinan.core.exceptions import RegistryError

        service_registry = get_service_registry()
        controller_registry = get_controller_registry()

        # Test invalid name validation
        with self.assertRaises(RegistryError):
            service_registry.register('', Service)

        with self.assertRaises(RegistryError):
            controller_registry.register('', object)

        # Test registering method for non-existent controller
        with self.assertRaises(RegistryError):
            controller_registry.register_method('NonExistent', '/test', 'get', lambda: None)


if __name__ == '__main__':
    unittest.main()

