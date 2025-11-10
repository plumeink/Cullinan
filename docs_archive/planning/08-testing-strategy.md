# Testing Strategy

## Executive Summary

This document outlines the comprehensive testing strategy for Cullinan's enhanced service layer, including unit testing, integration testing, and best practices for testing applications built with Cullinan.

## 1. Testing Philosophy

### 1.1 Test Pyramid

```
        /\
       /  \
      / E2E \      End-to-End Tests (Few)
     /______\
    /        \
   / Integr.  \    Integration Tests (Some)
  /____________\
 /              \
/   Unit Tests   \  Unit Tests (Many)
/_________________\
```

**Distribution**:
- **70% Unit Tests**: Fast, isolated, comprehensive
- **20% Integration Tests**: Component interactions
- **10% E2E Tests**: Full application workflows

### 1.2 Testing Principles

✅ **Fast**: Tests should run quickly (< 1 second each)
✅ **Isolated**: Tests don't affect each other
✅ **Repeatable**: Same result every time
✅ **Self-checking**: Pass/fail without manual verification
✅ **Timely**: Written with or before code

## 2. Unit Testing Services

### 2.1 Testing Without Dependencies

**Service**:
```python
@service
class EmailService(Service):
    def send(self, to, subject, body):
        # Email sending logic
        return {'to': to, 'subject': subject}
```

**Test**:
```python
import unittest
from services.email_service import EmailService

class TestEmailService(unittest.TestCase):
    def setUp(self):
        self.service = EmailService()
    
    def test_send_email(self):
        result = self.service.send('test@example.com', 'Hello', 'Body')
        
        self.assertEqual(result['to'], 'test@example.com')
        self.assertEqual(result['subject'], 'Hello')
    
    def test_send_email_validation(self):
        with self.assertRaises(ValueError):
            self.service.send('', 'Hello', 'Body')  # Empty email
```

### 2.2 Testing With Dependencies (Manual Mocking)

**Service**:
```python
@service(dependencies=['EmailService'])
class UserService(Service):
    def on_init(self):
        self.email = self.dependencies['EmailService']
    
    def create_user(self, name, email):
        user = {'name': name, 'email': email}
        self.email.send(email, 'Welcome', f'Hello {name}!')
        return user
```

**Test**:
```python
import unittest
from unittest.mock import Mock
from services.user_service import UserService

class TestUserService(unittest.TestCase):
    def setUp(self):
        # Create service
        self.service = UserService()
        
        # Create mock email service
        self.mock_email = Mock()
        self.mock_email.send = Mock(return_value=True)
        
        # Inject mock
        self.service.dependencies = {'EmailService': self.mock_email}
        self.service.on_init()
    
    def test_create_user(self):
        user = self.service.create_user('John', 'john@example.com')
        
        # Assert user created
        self.assertEqual(user['name'], 'John')
        self.assertEqual(user['email'], 'john@example.com')
        
        # Assert email sent
        self.mock_email.send.assert_called_once()
        call_args = self.mock_email.send.call_args
        self.assertEqual(call_args[0][0], 'john@example.com')
        self.assertIn('Welcome', call_args[0][1])
```

### 2.3 Testing With TestRegistry (Recommended)

**Test**:
```python
from cullinan.testing import TestRegistry, MockService

class MockEmailService(MockService):
    def send(self, to, subject, body):
        self.record_call('send', to=to, subject=subject, body=body)
        return True

class TestUserService(unittest.TestCase):
    def setUp(self):
        # Create test registry
        self.registry = TestRegistry()
        
        # Register mock
        self.mock_email = MockEmailService()
        self.registry.register_mock('EmailService', self.mock_email)
        
        # Register service under test
        self.registry.register('UserService', UserService, 
                              dependencies=['EmailService'])
    
    def test_create_user(self):
        # Get service with injected mocks
        service = self.registry.get('UserService')
        
        # Test
        user = service.create_user('John', 'john@example.com')
        
        # Assert
        self.assertEqual(user['name'], 'John')
        self.assertTrue(self.mock_email.was_called('send'))
        self.assertEqual(self.mock_email.call_count('send'), 1)
        
        # Check arguments
        args = self.mock_email.get_call_args('send')
        self.assertEqual(args['to'], 'john@example.com')
    
    def tearDown(self):
        self.registry.clear()
```

## 3. Integration Testing

### 3.1 Testing Service Interactions

**Test multiple services together**:
```python
class TestServiceIntegration(unittest.TestCase):
    def setUp(self):
        self.registry = TestRegistry()
        
        # Register real services (not mocks)
        self.registry.register('ConfigService', ConfigService)
        self.registry.register('EmailService', EmailService, 
                              dependencies=['ConfigService'])
        self.registry.register('UserService', UserService,
                              dependencies=['EmailService'])
        
        # Initialize all
        self.registry.initialize_all()
    
    def test_user_creation_workflow(self):
        # Test complete workflow
        user_service = self.registry.get('UserService')
        user = user_service.create_user('John', 'john@example.com')
        
        self.assertIsNotNone(user)
        self.assertEqual(user['name'], 'John')
    
    def tearDown(self):
        self.registry.shutdown_all()
        self.registry.clear()
```

### 3.2 Testing Lifecycle Hooks

**Test initialization order**:
```python
class TestLifecycleIntegration(unittest.TestCase):
    def test_initialization_order(self):
        registry = TestRegistry()
        
        # Track initialization order
        init_order = []
        
        @service
        class ServiceA(Service):
            def on_init(self):
                init_order.append('A')
        
        @service(dependencies=['ServiceA'])
        class ServiceB(Service):
            def on_init(self):
                init_order.append('B')
        
        registry.register('ServiceA', ServiceA)
        registry.register('ServiceB', ServiceB, dependencies=['ServiceA'])
        
        # Initialize
        registry.initialize_all()
        
        # Assert order: A before B
        self.assertEqual(init_order, ['A', 'B'])
```

## 4. Testing Controllers

### 4.1 Controller Unit Tests

**Controller**:
```python
@controller(url='/api')
class UserController:
    @post_api(url='/users', body_params=['name', 'email'])
    def create_user(self, body_params):
        user = self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )
        return self.response_build(status=201, data=user)
```

**Test**:
```python
import unittest
from unittest.mock import Mock, patch
from controllers.user_controller import UserController

class TestUserController(unittest.TestCase):
    def setUp(self):
        self.controller = UserController()
        
        # Mock service
        self.mock_user_service = Mock()
        self.mock_user_service.create_user = Mock(
            return_value={'id': 1, 'name': 'John'}
        )
        
        # Mock service access
        self.controller.service = {'UserService': self.mock_user_service}
    
    def test_create_user_endpoint(self):
        body_params = {'name': 'John', 'email': 'john@example.com'}
        
        response = self.controller.create_user(body_params)
        
        # Assert service called
        self.mock_user_service.create_user.assert_called_once_with(
            'John', 'john@example.com'
        )
        
        # Assert response
        self.assertEqual(response['status'], 201)
        self.assertEqual(response['data']['name'], 'John')
```

### 4.2 Controller Integration Tests

**With Tornado TestCase**:
```python
import tornado.testing
from cullinan import application

class TestUserControllerIntegration(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return application.app
    
    def test_create_user_endpoint(self):
        body = {'name': 'John', 'email': 'john@example.com'}
        
        response = self.fetch(
            '/api/users',
            method='POST',
            body=json.dumps(body),
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.code, 201)
        data = json.loads(response.body)
        self.assertEqual(data['name'], 'John')
```

## 5. Testing Best Practices

### 5.1 Test Organization

**Directory Structure**:
```
tests/
├── unit/
│   ├── test_email_service.py
│   ├── test_user_service.py
│   └── test_order_service.py
├── integration/
│   ├── test_service_integration.py
│   └── test_lifecycle.py
├── controllers/
│   ├── test_user_controller.py
│   └── test_order_controller.py
└── e2e/
    └── test_user_workflow.py
```

### 5.2 Test Naming Conventions

**Pattern**: `test_<method>_<scenario>_<expected_result>`

```python
def test_create_user_with_valid_data_succeeds(self):
    pass

def test_create_user_with_empty_email_raises_error(self):
    pass

def test_send_email_when_service_unavailable_retries(self):
    pass
```

### 5.3 AAA Pattern (Arrange-Act-Assert)

```python
def test_create_user(self):
    # Arrange
    service = UserService()
    service.dependencies = {'EmailService': MockEmailService()}
    service.on_init()
    
    # Act
    user = service.create_user('John', 'john@example.com')
    
    # Assert
    self.assertEqual(user['name'], 'John')
```

### 5.4 Test Fixtures

**Using setUp and tearDown**:
```python
class TestUserService(unittest.TestCase):
    def setUp(self):
        """Run before each test."""
        self.registry = TestRegistry()
        self.mock_email = MockEmailService()
        self.registry.register_mock('EmailService', self.mock_email)
        self.registry.register('UserService', UserService,
                              dependencies=['EmailService'])
    
    def tearDown(self):
        """Run after each test."""
        self.registry.clear()
    
    def test_something(self):
        # setUp has run, registry is ready
        service = self.registry.get('UserService')
        # ... test code ...
        # tearDown will run automatically
```

**Using pytest fixtures**:
```python
import pytest
from cullinan.testing import TestRegistry

@pytest.fixture
def test_registry():
    """Provide a clean test registry for each test."""
    registry = TestRegistry()
    yield registry
    registry.clear()

@pytest.fixture
def mock_email():
    """Provide a mock email service."""
    return MockEmailService()

def test_create_user(test_registry, mock_email):
    test_registry.register_mock('EmailService', mock_email)
    test_registry.register('UserService', UserService,
                          dependencies=['EmailService'])
    
    service = test_registry.get('UserService')
    user = service.create_user('John', 'john@example.com')
    
    assert user['name'] == 'John'
    assert mock_email.was_called('send')
```

## 6. Test Coverage

### 6.1 Measuring Coverage

**Using coverage.py**:
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run -m pytest tests/

# View report
coverage report

# Generate HTML report
coverage html
# Open htmlcov/index.html
```

### 6.2 Coverage Goals

**Target Coverage**:
- **Core module**: 100% (critical infrastructure)
- **Service layer**: 90%+ (business logic)
- **Controllers**: 80%+ (HTTP layer)
- **Overall**: 85%+

**What to Cover**:
✅ Happy paths (normal operation)
✅ Error paths (exceptions, validation)
✅ Edge cases (empty inputs, nulls, boundaries)
✅ Integration points (service interactions)

**What NOT to Cover**:
❌ Third-party libraries
❌ Generated code
❌ Simple getters/setters
❌ Trivial one-liners

## 7. Mocking Strategies

### 7.1 Mock vs Real Dependencies

**Use Mocks When**:
✅ External services (APIs, databases)
✅ Slow operations (network calls, file I/O)
✅ Non-deterministic behavior (random, time)
✅ Error scenarios (simulate failures)

**Use Real When**:
✅ Fast operations (calculations, transformations)
✅ Deterministic behavior (pure functions)
✅ Integration tests (want real interactions)

### 7.2 Creating Effective Mocks

**Simple Mock**:
```python
class MockEmailService(MockService):
    def send(self, to, subject, body):
        self.record_call('send', to=to, subject=subject, body=body)
        return {'sent': True, 'to': to}
```

**Mock with Behavior**:
```python
class MockEmailService(MockService):
    def __init__(self):
        super().__init__()
        self.fail_on_call = None
    
    def send(self, to, subject, body):
        self.record_call('send', to=to, subject=subject, body=body)
        
        if self.fail_on_call == self.call_count('send'):
            raise ConnectionError("Email service unavailable")
        
        return {'sent': True, 'to': to}

# In test
mock_email = MockEmailService()
mock_email.fail_on_call = 1  # Fail on first call
```

## 8. Continuous Integration

### 8.1 CI Pipeline

**GitHub Actions Example**:
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        python run_tests.py --verbose
    
    - name: Check coverage
      run: |
        coverage run -m pytest tests/
        coverage report --fail-under=85
```

### 8.2 Pre-commit Hooks

**Using pre-commit**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: python run_tests.py
        language: system
        pass_filenames: false
        always_run: true
```

## 9. Performance Testing

### 9.1 Benchmarking Services

```python
import time

class TestServicePerformance(unittest.TestCase):
    def test_user_service_performance(self):
        registry = TestRegistry()
        registry.register('UserService', UserService)
        service = registry.get('UserService')
        
        # Measure performance
        start = time.time()
        for i in range(1000):
            service.create_user(f'User{i}', f'user{i}@example.com')
        elapsed = time.time() - start
        
        # Assert performance
        self.assertLess(elapsed, 1.0)  # Should complete in < 1 second
        print(f"Created 1000 users in {elapsed:.3f}s")
```

### 9.2 Load Testing

**Using locust**:
```python
from locust import HttpUser, task, between

class UserLoadTest(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def create_user(self):
        self.client.post('/api/users', json={
            'name': 'TestUser',
            'email': 'test@example.com'
        })
```

## 10. Test Documentation

### 10.1 Docstrings in Tests

```python
def test_create_user_with_valid_data(self):
    """Test that creating a user with valid data succeeds.
    
    This test verifies:
    - User is created with correct name and email
    - Welcome email is sent
    - User ID is generated
    """
    service = self.registry.get('UserService')
    user = service.create_user('John', 'john@example.com')
    
    self.assertEqual(user['name'], 'John')
    self.assertIsNotNone(user['id'])
```

### 10.2 Test Reports

**Generate readable reports**:
```bash
# pytest with verbose output
pytest tests/ -v --tb=short

# Generate JUnit XML
pytest tests/ --junit-xml=test-results.xml

# Generate HTML report
pytest tests/ --html=test-report.html
```

---

**Document Version**: 1.0  
**Author**: Cullinan Framework Team  
**Date**: 2025-11-10  
**Status**: Final Draft
