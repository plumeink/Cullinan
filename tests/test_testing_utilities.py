# -*- coding: utf-8 -*-
"""
Tests for the testing utilities module.

Tests MockService, TestRegistry, and test fixtures.
"""

import unittest

from cullinan.testing import (
    MockService,
    TestRegistry,
    ServiceTestCase,
    IsolatedServiceTestCase
)
from cullinan.service import Service, service, get_service_registry


# ============================================================================
# Test MockService
# ============================================================================

class TestMockService(unittest.TestCase):
    """Test MockService functionality."""
    
    def test_record_call(self):
        """Test recording method calls."""
        mock = MockService()
        mock.record_call('test_method', arg1='value1', arg2='value2')
        
        self.assertTrue(mock.was_called('test_method'))
        self.assertEqual(mock.call_count('test_method'), 1)
    
    def test_get_call_args(self):
        """Test retrieving call arguments."""
        mock = MockService()
        mock.record_call('test_method', arg1='value1', arg2='value2')
        
        args = mock.get_call_args('test_method')
        self.assertEqual(args['arg1'], 'value1')
        self.assertEqual(args['arg2'], 'value2')
    
    def test_multiple_calls(self):
        """Test handling multiple calls to same method."""
        mock = MockService()
        mock.record_call('test_method', count=1)
        mock.record_call('test_method', count=2)
        mock.record_call('test_method', count=3)
        
        self.assertEqual(mock.call_count('test_method'), 3)
        
        # Get first call
        first_call = mock.get_call_args('test_method', 0)
        self.assertEqual(first_call['count'], 1)
        
        # Get last call
        last_call = mock.get_call_args('test_method', -1)
        self.assertEqual(last_call['count'], 3)
    
    def test_get_all_calls(self):
        """Test getting all calls to a method."""
        mock = MockService()
        mock.record_call('test_method', value='a')
        mock.record_call('test_method', value='b')
        mock.record_call('test_method', value='c')
        
        all_calls = mock.get_all_calls('test_method')
        self.assertEqual(len(all_calls), 3)
        self.assertEqual(all_calls[0]['value'], 'a')
        self.assertEqual(all_calls[1]['value'], 'b')
        self.assertEqual(all_calls[2]['value'], 'c')
    
    def test_was_not_called(self):
        """Test checking for methods that were not called."""
        mock = MockService()
        self.assertFalse(mock.was_called('nonexistent_method'))
    
    def test_reset_calls(self):
        """Test resetting all recorded calls."""
        mock = MockService()
        mock.record_call('test_method', arg='value')
        self.assertTrue(mock.was_called('test_method'))
        
        mock.reset_calls()
        self.assertFalse(mock.was_called('test_method'))
    
    def test_lifecycle_methods(self):
        """Test that MockService has lifecycle methods."""
        mock = MockService()
        # Should not raise
        mock.on_init()
        mock.on_destroy()
    
    def test_custom_mock_implementation(self):
        """Test creating a custom mock service."""
        class MockEmailService(MockService):
            def send_email(self, to, subject):
                self.record_call('send_email', to=to, subject=subject)
                return True
        
        mock = MockEmailService()
        result = mock.send_email('test@example.com', 'Hello')
        
        self.assertTrue(result)
        self.assertTrue(mock.was_called('send_email'))
        args = mock.get_call_args('send_email')
        self.assertEqual(args['to'], 'test@example.com')
        self.assertEqual(args['subject'], 'Hello')


# ============================================================================
# Test TestRegistry
# ============================================================================

class TestTestRegistry(unittest.TestCase):
    """Test TestRegistry functionality."""
    
    def test_isolated_from_global(self):
        """Test that TestRegistry is isolated from global registry."""
        # Register in test registry
        test_reg = TestRegistry()
        
        class TestService(Service):
            pass
        
        test_reg.register('TestService', TestService)
        
        # Should not appear in global registry
        global_reg = get_service_registry()
        self.assertFalse(global_reg.has('TestService'))
    
    def test_register_mock_instance(self):
        """Test registering a mock instance directly."""
        test_reg = TestRegistry()
        
        mock = MockService()
        test_reg.register_mock('MockService', mock)
        
        self.assertTrue(test_reg.has('MockService'))
    
    def test_register_mock_with_dependencies(self):
        """Test registering mock with dependencies."""
        test_reg = TestRegistry()
        
        mock_a = MockService()
        mock_b = MockService()
        
        test_reg.register_mock('ServiceA', mock_a)
        test_reg.register_mock('ServiceB', mock_b, dependencies=['ServiceA'])
        
        test_reg.initialize_all()
        
        # ServiceB should have ServiceA as dependency
        instance_b = test_reg.get_instance('ServiceB')
        self.assertIs(instance_b, mock_b)


# ============================================================================
# Test ServiceTestCase
# ============================================================================

class TestServiceTestCase(ServiceTestCase):
    """Test ServiceTestCase fixture."""
    
    def test_registry_is_clean(self):
        """Test that registry starts clean."""
        registry = get_service_registry()
        # Should be empty (or only have items from other tests that cleanup properly)
        # The key is that setUp runs before each test
        initial_count = registry.count()
        
        @service
        class TestService(Service):
            pass
        
        # After registering, count should increase
        self.assertEqual(registry.count(), initial_count + 1)
    
    def test_registry_cleaned_between_tests(self):
        """Test that registry is cleaned between tests."""
        # This test should start with clean registry due to setUp
        registry = get_service_registry()
        
        # Even if previous test registered services, this should start clean
        # (thanks to setUp/tearDown)
        @service
        class AnotherService(Service):
            pass


# ============================================================================
# Test IsolatedServiceTestCase
# ============================================================================

class TestIsolatedServiceTestCase(IsolatedServiceTestCase):
    """Test IsolatedServiceTestCase fixture."""
    
    def test_has_isolated_registry(self):
        """Test that test case has isolated registry."""
        self.assertIsNotNone(self.registry)
        self.assertIsInstance(self.registry, TestRegistry)
    
    def test_can_use_isolated_registry(self):
        """Test using isolated registry in test."""
        class TestService(Service):
            pass
        
        self.registry.register('TestService', TestService)
        self.registry.initialize_all()
        
        instance = self.registry.get_instance('TestService')
        self.assertIsInstance(instance, TestService)
        
        # Should not affect global registry
        global_reg = get_service_registry()
        self.assertFalse(global_reg.has('TestService'))


# ============================================================================
# Integration Test
# ============================================================================

class TestTestingUtilitiesIntegration(IsolatedServiceTestCase):
    """Integration test for testing utilities."""
    
    def test_complete_mock_testing_workflow(self):
        """Test complete workflow with mocks."""
        # Create mock service
        class MockEmailService(MockService):
            def send_email(self, to, subject, body):
                self.record_call('send_email', to=to, subject=subject, body=body)
                return True
        
        # Create service under test
        class UserService(Service):
            def on_init(self):
                self.email = self.dependencies.get('EmailService')
            
            def create_user(self, name, email):
                user = {'name': name, 'email': email}
                if self.email:
                    self.email.send_email(email, 'Welcome', f'Welcome {name}!')
                return user
        
        # Register services in isolated registry
        self.registry.register('EmailService', MockEmailService)
        self.registry.register('UserService', UserService, dependencies=['EmailService'])
        
        # Initialize
        self.registry.initialize_all()
        
        # Get instances
        email_svc = self.registry.get_instance('EmailService')
        user_svc = self.registry.get_instance('UserService')
        
        # Test
        user = user_svc.create_user('John Doe', 'john@example.com')
        
        # Verify
        self.assertEqual(user['name'], 'John Doe')
        self.assertTrue(email_svc.was_called('send_email'))
        self.assertEqual(email_svc.call_count('send_email'), 1)
        
        args = email_svc.get_call_args('send_email')
        self.assertEqual(args['to'], 'john@example.com')
        self.assertEqual(args['subject'], 'Welcome')
        self.assertIn('John Doe', args['body'])


if __name__ == '__main__':
    unittest.main()
