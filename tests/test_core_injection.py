# -*- coding: utf-8 -*-
"""Core Dependency Injection System - Comprehensive Tests"""

import unittest
from typing import Any

from cullinan.core import Inject, injectable, get_injection_registry, reset_injection_registry
from cullinan.service import Service, service, get_service_registry, reset_service_registry
from cullinan.controller import controller, get_controller_registry, reset_controller_registry


class TestCoreInjection(unittest.TestCase):
    """Test core layer dependency injection"""

    def setUp(self):
        reset_injection_registry()
        reset_service_registry()
        reset_controller_registry()

    def test_inject_marker(self):
        """Test Inject marker class"""
        inject1 = Inject()
        self.assertIsNone(inject1.name)
        self.assertTrue(inject1.required)

        inject2 = Inject(name='MyService')
        self.assertEqual(inject2.name, 'MyService')

        inject3 = Inject(name='Optional', required=False)
        self.assertFalse(inject3.required)

    def test_injectable_decorator(self):
        """Test @injectable decorator"""
        @injectable
        class TestClass:
            dep: Any = Inject(name='TestDep')

        injection_registry = get_injection_registry()
        self.assertTrue(injection_registry.has_injections(TestClass))

    def test_injection_with_provider(self):
        """Test actual injection with provider"""
        from cullinan.core import SimpleRegistry

        provider = SimpleRegistry()
        provider.register('TestDep', 'MockedDependency')

        injection_registry = get_injection_registry()
        injection_registry.add_provider_registry(provider)

        @injectable
        class TestClass:
            dep: Any = Inject(name='TestDep')

        instance = TestClass()
        self.assertEqual(instance.dep, 'MockedDependency')


class TestServiceInjection(unittest.TestCase):
    """Test Service dependency injection"""

    def setUp(self):
        reset_injection_registry()
        reset_service_registry()
        reset_controller_registry()

        injection_registry = get_injection_registry()
        service_registry = get_service_registry()
        injection_registry.add_provider_registry(service_registry, priority=100)

    def test_service_type_injection(self):
        """Test type injection in Service"""
        @service
        class EmailService(Service):
            def send_email(self, to: str):
                return f"Email sent to {to}"

        @service
        class UserService(Service):
            email: EmailService = Inject()

            def create_user(self, name: str):
                result = self.email.send_email(f"{name}@example.com")
                return f"User {name} created, {result}"

        service_registry = get_service_registry()
        user_service = service_registry.get_instance('UserService')

        self.assertIsNotNone(user_service.email)
        self.assertIsInstance(user_service.email, EmailService)

        result = user_service.create_user('Alice')
        self.assertIn('Alice', result)

    def test_service_injection_chain(self):
        """Test dependency chain"""
        @service
        class ServiceA(Service):
            def method_a(self):
                return 'A'

        @service
        class ServiceB(Service):
            a: ServiceA = Inject()

            def method_b(self):
                return f"B+{self.a.method_a()}"

        @service
        class ServiceC(Service):
            b: ServiceB = Inject()

            def method_c(self):
                return f"C+{self.b.method_b()}"

        service_registry = get_service_registry()
        service_c = service_registry.get_instance('ServiceC')

        self.assertIsInstance(service_c.b, ServiceB)
        self.assertIsInstance(service_c.b.a, ServiceA)

        result = service_c.method_c()
        self.assertEqual(result, 'C+B+A')


class TestControllerInjection(unittest.TestCase):
    """Test Controller dependency injection"""

    def setUp(self):
        reset_injection_registry()
        reset_service_registry()
        reset_controller_registry()

        injection_registry = get_injection_registry()
        service_registry = get_service_registry()
        injection_registry.add_provider_registry(service_registry, priority=100)

    def test_controller_inject_service(self):
        """Test Controller inject Service"""
        @service
        class ProductService(Service):
            def get_products(self):
                return [{'id': 1, 'name': 'Product A'}]

        @controller(url='/api')
        class ProductController:
            product_service: ProductService = Inject()

            def get_products_list(self):
                return self.product_service.get_products()

        controller_instance = ProductController()

        self.assertIsNotNone(controller_instance.product_service)
        self.assertIsInstance(controller_instance.product_service, ProductService)

        products = controller_instance.get_products_list()
        self.assertEqual(len(products), 1)


class TestScanOrderIndependence(unittest.TestCase):
    """Test scan order independence"""

    def setUp(self):
        reset_injection_registry()
        reset_service_registry()
        reset_controller_registry()

        injection_registry = get_injection_registry()
        service_registry = get_service_registry()
        injection_registry.add_provider_registry(service_registry, priority=100)

    def test_controller_before_service(self):
        """Test Controller defined before Service still works"""
        from cullinan.service import service as service_decorator

        @controller(url='/api')
        class OrderController:
            order_service: Any = Inject(name='OrderService')

        @service_decorator
        class OrderService(Service):
            def get_orders(self):
                return ['Order1', 'Order2']

        # Controller uses class-level injection with lazy loading
        # Need to create a mock instance to trigger the property getter
        class MockController:
            pass

        # Copy the property to mock instance
        for key in dir(OrderController):
            if not key.startswith('_'):
                attr = getattr(OrderController, key)
                if isinstance(attr, property):
                    setattr(MockController, key, attr)

        mock_instance = MockController()

        # Now access the property through instance
        svc = mock_instance.order_service
        self.assertIsInstance(svc, OrderService)
        orders = svc.get_orders()
        self.assertEqual(len(orders), 2)


class TestErrorHandling(unittest.TestCase):
    """Test error handling"""

    def setUp(self):
        reset_injection_registry()
        reset_service_registry()

        injection_registry = get_injection_registry()
        service_registry = get_service_registry()
        injection_registry.add_provider_registry(service_registry, priority=100)

    def test_missing_required_service(self):
        """Test missing required service raises error"""
        from cullinan.core.exceptions import RegistryError

        @service
        class TestService(Service):
            missing: Any = Inject(name='NonExistentService', required=True)

        service_registry = get_service_registry()

        with self.assertRaises(RegistryError):
            service_registry.get_instance('TestService')

    def test_optional_service_no_error(self):
        """Test missing optional service doesn't raise error"""
        @service
        class TestService(Service):
            optional: Any = Inject(name='NonExistentService', required=False)

        service_registry = get_service_registry()
        instance = service_registry.get_instance('TestService')

        self.assertIsNotNone(instance)


if __name__ == '__main__':
    unittest.main(verbosity=2)

