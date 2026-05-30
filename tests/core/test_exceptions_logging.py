# -*- coding: utf-8 -*-
"""
Tests for exception handling and logging utilities.
"""

import unittest
import logging
from io import StringIO

from cullinan.exceptions import (
    CullinanError,
    ConfigurationError,
    PackageDiscoveryError,
    CallerPackageException,
    RoutingError,
    RequestError,
    MissingHeaderException,
    ParameterError,
    ResponseError,
    HandlerError,
    ServiceError,
)
from cullinan.logging_utils import (
    StructuredLogger,
    PerformanceLogger,
    should_log,
    log_if_enabled,
    get_structured_logger,
    get_performance_logger,
)


class TestExceptionHierarchy(unittest.TestCase):
    """Test exception hierarchy and error codes."""
    
    def test_base_exception_creation(self):
        """Test creating base CullinanError."""
        error = CullinanError("Test error")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.error_code, "CULLINAN_ERROR")
        self.assertEqual(error.details, {})
        self.assertIsNone(error.original_exception)
    
    def test_exception_with_details(self):
        """Test exception with additional details."""
        error = CullinanError(
            "Configuration failed",
            error_code="CONFIG_001",
            details={"param": "host", "value": None}
        )
        self.assertEqual(error.error_code, "CONFIG_001")
        self.assertEqual(error.details["param"], "host")
        self.assertIn("param=host", str(error))
    
    def test_exception_with_cause(self):
        """Test exception wrapping another exception."""
        original = ValueError("Invalid value")
        error = CullinanError(
            "Wrapper error",
            original_exception=original
        )
        self.assertEqual(error.original_exception, original)
        self.assertIn("Caused by", str(error))
        self.assertIn("ValueError", str(error))
    
    def test_exception_to_dict(self):
        """Test converting exception to dictionary."""
        error = CullinanError(
            "Test error",
            error_code="TEST_001",
            details={"key": "value"}
        )
        data = error.to_dict()
        
        self.assertEqual(data["error_code"], "TEST_001")
        self.assertEqual(data["error_type"], "CullinanError")
        self.assertEqual(data["message"], "Test error")
        self.assertEqual(data["details"]["key"], "value")
    
    def test_configuration_error(self):
        """Test ConfigurationError subclass."""
        error = ConfigurationError("Invalid config")
        self.assertEqual(error.error_code, "CONFIG_ERROR")
        self.assertIsInstance(error, CullinanError)
    
    def test_caller_package_exception_backward_compat(self):
        """Test CallerPackageException maintains backward compatibility."""
        error = CallerPackageException()
        self.assertEqual(error.message, "Failed to get the caller package directory")
        self.assertEqual(error.error_code, "CALLER_PACKAGE_ERROR")
        
        # Test custom message
        error2 = CallerPackageException("Custom message")
        self.assertEqual(error2.message, "Custom message")
    
    def test_missing_header_exception_backward_compat(self):
        """Test MissingHeaderException maintains backward compatibility."""
        error = MissingHeaderException("Authorization")
        self.assertEqual(error.header_name, "Authorization")
        self.assertIn("Authorization", str(error))
        self.assertEqual(error.error_code, "MISSING_HEADER")
        self.assertEqual(error.details["header_name"], "Authorization")
    
    def test_all_error_subclasses(self):
        """Test all error subclasses have correct hierarchy."""
        errors = [
            (ConfigurationError, "CONFIG_ERROR"),
            (PackageDiscoveryError, "PACKAGE_DISCOVERY_ERROR"),
            (RoutingError, "ROUTING_ERROR"),
            (RequestError, "REQUEST_ERROR"),
            (ParameterError, "PARAMETER_ERROR"),
            (ResponseError, "RESPONSE_ERROR"),
            (HandlerError, "HANDLER_ERROR"),
            (ServiceError, "SERVICE_ERROR"),
        ]
        
        for error_class, expected_code in errors:
            error = error_class("Test message")
            self.assertIsInstance(error, CullinanError)
            self.assertEqual(error.error_code, expected_code)


class TestStructuredLogger(unittest.TestCase):
    """Test structured logging functionality."""
    
    def setUp(self):
        """Set up test logger."""
        self.logger = logging.getLogger('test_structured')
        self.logger.setLevel(logging.DEBUG)
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        
        self.structured_logger = StructuredLogger(self.logger)
    
    def tearDown(self):
        """Clean up handlers."""
        self.logger.handlers.clear()
    
    def test_context_management(self):
        """Test logging context management."""
        self.structured_logger.set_context(request_id="123", user="alice")
        ctx = self.structured_logger.get_context()
        
        self.assertEqual(ctx["request_id"], "123")
        self.assertEqual(ctx["user"], "alice")
        
        self.structured_logger.clear_context()
        ctx2 = self.structured_logger.get_context()
        self.assertEqual(ctx2, {})
    
    def test_structured_logging(self):
        """Test structured log output."""
        self.structured_logger.set_context(request_id="456")
        self.structured_logger.info_structured("Test message", extra_field="value")
        
        output = self.log_stream.getvalue()
        self.assertIn("Test message", output)
        self.assertIn("extra_field", output)
        self.assertIn("request_id", output)
    
    def test_conditional_logging(self):
        """Test that logging respects level settings."""
        # Set to WARNING, debug should not appear
        self.logger.setLevel(logging.WARNING)
        self.structured_logger.debug_structured("Debug message")
        
        output = self.log_stream.getvalue()
        self.assertEqual(output, "")


class TestPerformanceLogger(unittest.TestCase):
    """Test performance logging functionality."""
    
    def setUp(self):
        """Set up test logger."""
        self.logger = logging.getLogger('test_performance')
        self.logger.setLevel(logging.INFO)
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
        self.perf_logger = PerformanceLogger(self.logger)
    
    def tearDown(self):
        """Clean up handlers."""
        self.logger.handlers.clear()
    
    def test_log_timing(self):
        """Test basic timing logging."""
        self.perf_logger.log_timing("test_operation", 0.150)
        output = self.log_stream.getvalue()
        
        self.assertIn("test_operation", output)
        self.assertIn("150", output)  # 150ms
    
    def test_threshold_logging(self):
        """Test that threshold filters timing logs."""
        # Below threshold - should not log
        self.perf_logger.log_timing("fast_op", 0.05, threshold=1.0)
        output1 = self.log_stream.getvalue()
        self.assertEqual(output1, "")
        
        # Above threshold - should log
        self.perf_logger.log_timing("slow_op", 1.5, threshold=1.0)
        output2 = self.log_stream.getvalue()
        self.assertIn("slow_op", output2)
    
    def test_timed_decorator(self):
        """Test the @timed decorator."""
        import time
        
        @self.perf_logger.timed(operation="test_func")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        result = test_function()
        self.assertEqual(result, "result")
        
        output = self.log_stream.getvalue()
        self.assertIn("test_func", output)


class TestLoggingUtilities(unittest.TestCase):
    """Test logging utility functions."""
    
    def test_should_log(self):
        """Test should_log helper."""
        logger = logging.getLogger('test_should_log')
        logger.setLevel(logging.INFO)
        
        self.assertTrue(should_log(logger, logging.INFO))
        self.assertTrue(should_log(logger, logging.WARNING))
        self.assertFalse(should_log(logger, logging.DEBUG))
    
    def test_log_if_enabled(self):
        """Test conditional logging helper."""
        logger = logging.getLogger('test_log_if_enabled')
        logger.setLevel(logging.WARNING)
        
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger.addHandler(handler)
        
        # Should log (WARNING level)
        log_if_enabled(logger, logging.WARNING, "Warning message")
        self.assertIn("Warning message", log_stream.getvalue())
        
        # Should not log (DEBUG level)
        log_if_enabled(logger, logging.DEBUG, "Debug message")
        self.assertNotIn("Debug message", log_stream.getvalue())
        
        logger.handlers.clear()
    
    def test_get_structured_logger(self):
        """Test getting a structured logger."""
        logger = get_structured_logger("test_module")
        self.assertIsInstance(logger, StructuredLogger)
    
    def test_get_performance_logger(self):
        """Test getting a performance logger."""
        logger = get_performance_logger("test_module")
        self.assertIsInstance(logger, PerformanceLogger)


class TestExceptionFormatting(unittest.TestCase):
    """Test exception message formatting."""
    
    def test_format_with_all_components(self):
        """Test formatting with all components present."""
        original = ValueError("Original error")
        error = CullinanError(
            "Main error",
            error_code="TEST_001",
            details={"key1": "value1", "key2": "value2"},
            original_exception=original
        )
        
        formatted = str(error)
        self.assertIn("[TEST_001]", formatted)
        self.assertIn("Main error", formatted)
        self.assertIn("key1=value1", formatted)
        self.assertIn("Caused by", formatted)
        self.assertIn("ValueError", formatted)
    
    def test_format_minimal(self):
        """Test formatting with minimal components."""
        error = CullinanError("Simple error")
        formatted = str(error)
        
        self.assertIn("[CULLINAN_ERROR]", formatted)
        self.assertIn("Simple error", formatted)
        self.assertNotIn("Details:", formatted)
        self.assertNotIn("Caused by:", formatted)


if __name__ == '__main__':
    unittest.main()
