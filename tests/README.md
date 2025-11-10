# Cullinan Test Suite

This directory contains all test files for the Cullinan framework.

## Running Tests

### From Project Root

Run all tests:
```bash
python tests/run_tests.py
```

Run tests with verbose output:
```bash
python tests/run_tests.py --verbose
```

Generate coverage report:
```bash
python tests/run_tests.py --coverage
```

Quick test (skip time-consuming tests):
```bash
python tests/run_tests.py --quick
```

Check test dependencies:
```bash
python tests/run_tests.py --check-deps
```

### Using pytest (Alternative)

If you have pytest installed:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=cullinan tests/
```

### Using unittest Directly

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Test Structure

```
tests/
├── run_tests.py                    # Main test runner script
├── test_application_coverage.py    # Application module tests
├── test_async_support.py           # Async functionality tests
├── test_compatibility.py           # Backward compatibility tests
├── test_config_coverage.py         # Configuration tests
├── test_controller_coverage.py     # Controller tests
├── test_core.py                    # Core functionality tests
├── test_core_module.py             # Core module tests
├── test_exceptions_logging.py      # Exception & logging tests
├── test_handler_module.py          # Handler module tests
├── test_middleware.py              # Middleware tests
├── test_module_scanner.py          # Module scanner tests
├── test_packaging.py               # Packaging tests
├── test_performance.py             # Performance benchmarks
├── test_registry.py                # Registry pattern tests
├── test_service_enhanced.py        # Enhanced service layer tests
└── test_testing_utilities.py       # Testing utilities tests
```

## Test Categories

### Core Tests
- `test_core.py` - Core framework functionality
- `test_core_module.py` - Core module (registry, DI, lifecycle)
- `test_application_coverage.py` - Application class

### Feature Tests
- `test_service_enhanced.py` - Service layer with DI
- `test_registry.py` - Registry pattern
- `test_controller_coverage.py` - Controller decorators
- `test_handler_module.py` - HTTP handlers
- `test_middleware.py` - Middleware chain

### Quality Tests
- `test_compatibility.py` - Backward compatibility
- `test_async_support.py` - Async/await support
- `test_performance.py` - Performance benchmarks
- `test_packaging.py` - Packaging with Nuitka/PyInstaller

### Utility Tests
- `test_module_scanner.py` - Module discovery
- `test_exceptions_logging.py` - Error handling
- `test_config_coverage.py` - Configuration system
- `test_testing_utilities.py` - Testing framework

## Writing Tests

### Test File Naming
- All test files must start with `test_`
- Example: `test_feature_name.py`

### Test Class Naming
- Test classes should start with `Test`
- Example: `class TestServiceLayer(unittest.TestCase):`

### Test Method Naming
- Test methods must start with `test_`
- Use descriptive names: `test_service_with_dependencies()`

### Example Test

```python
import unittest
from cullinan import service, Service

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_feature_works(self):
        """Test that feature works correctly"""
        # Arrange
        expected = "result"
        
        # Act
        actual = my_feature()
        
        # Assert
        self.assertEqual(actual, expected)
```

## Test Dependencies

Required for running tests:
- Python 3.7+
- unittest (built-in)

Optional for enhanced testing:
- `coverage` - for coverage reports
- `pytest` - alternative test runner
- `colorama` - colored output (recommended)

Install optional dependencies:
```bash
pip install coverage pytest colorama
```

## Continuous Integration

Tests are automatically run on:
- Push to main branch
- Pull requests
- Scheduled nightly builds

## Coverage Goals

- **Overall**: > 80%
- **Core modules**: > 90%
- **New features**: 100%

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the project root:
```bash
cd /path/to/Cullinan
python tests/run_tests.py
```

### Module Not Found
Ensure the project is installed in development mode:
```bash
pip install -e .
```

### Test Failures
1. Check if all dependencies are installed
2. Run with `--verbose` for detailed output
3. Run individual test files to isolate issues:
   ```bash
   python -m unittest tests.test_core
   ```

## Contributing Tests

When adding new features:
1. Write tests first (TDD approach recommended)
2. Ensure tests pass locally
3. Add test file to this directory
4. Update this README if adding new test category
5. Maintain > 80% coverage

---

**Last Updated**: November 11, 2025  
**Maintained By**: Cullinan Development Team

