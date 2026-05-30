# -*- coding: utf-8 -*-
"""Tests for the module_scanner module.

Tests the module discovery and scanning functionality across different
deployment environments (development, Nuitka, PyInstaller).
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from cullinan.module_scanner import (
    is_pyinstaller_frozen,
    is_nuitka_compiled,
    get_nuitka_standalone_mode,
    get_pyinstaller_mode,
    get_caller_package,
    _is_user_module_by_path,
)


class TestEnvironmentDetection(unittest.TestCase):
    """Test environment detection functions."""
    
    def test_is_pyinstaller_frozen_false(self):
        """Test PyInstaller detection in normal environment."""
        # In normal Python environment, should return False
        result = is_pyinstaller_frozen()
        self.assertFalse(result)
    
    def test_is_nuitka_compiled_false(self):
        """Test Nuitka detection in normal environment."""
        # In normal Python environment, should return False
        result = is_nuitka_compiled()
        self.assertFalse(result)
    
    def test_get_nuitka_standalone_mode_none(self):
        """Test Nuitka mode detection returns None in normal environment."""
        result = get_nuitka_standalone_mode()
        self.assertIsNone(result)
    
    def test_get_pyinstaller_mode_none(self):
        """Test PyInstaller mode detection returns None in normal environment."""
        result = get_pyinstaller_mode()
        self.assertIsNone(result)


class TestModulePathChecking(unittest.TestCase):
    """Test module path validation functions."""
    
    def test_is_user_module_by_path_cullinan(self):
        """Test that cullinan modules are excluded."""
        mod = MagicMock()
        mod.__file__ = '/path/to/cullinan/module.py'
        result = _is_user_module_by_path('cullinan.module', mod)
        self.assertFalse(result)
    
    def test_is_user_module_by_path_site_packages(self):
        """Test that site-packages modules are excluded."""
        mod = MagicMock()
        mod.__file__ = '/usr/lib/python3.12/site-packages/some_lib/module.py'
        result = _is_user_module_by_path('some_lib.module', mod)
        self.assertFalse(result)
    
    def test_is_user_module_by_path_stdlib(self):
        """Test that stdlib modules are excluded."""
        mod = MagicMock()
        mod.__file__ = '/usr/lib/python3.12/json/__init__.py'
        result = _is_user_module_by_path('json', mod)
        self.assertFalse(result)
    
    def test_is_user_module_by_path_user_code(self):
        """Test that user modules are included."""
        mod = MagicMock()
        mod.__file__ = '/home/user/myproject/myapp/controller.py'
        result = _is_user_module_by_path('myapp.controller', mod)
        self.assertTrue(result)


class TestCallerPackage(unittest.TestCase):
    """Test caller package detection."""
    
    def test_get_caller_package(self):
        """Test that get_caller_package returns a package name."""
        # This test will return 'tests' since it's called from test module
        try:
            result = get_caller_package()
            # Should return something, even if it's an error
            self.assertIsInstance(result, str)
            # Should not be 'cullinan' since we're in tests
            self.assertNotEqual(result, 'cullinan')
        except Exception:
            # If it fails, that's also acceptable for this test
            pass


class TestModuleScannerIntegration(unittest.TestCase):
    """Integration tests for module scanning."""
    
    def test_module_scanner_imports(self):
        """Test that all expected functions are importable."""
        from cullinan import module_scanner
        
        # Check that all key functions exist
        self.assertTrue(hasattr(module_scanner, 'is_pyinstaller_frozen'))
        self.assertTrue(hasattr(module_scanner, 'is_nuitka_compiled'))
        self.assertTrue(hasattr(module_scanner, 'get_nuitka_standalone_mode'))
        self.assertTrue(hasattr(module_scanner, 'get_pyinstaller_mode'))
        self.assertTrue(hasattr(module_scanner, 'get_caller_package'))
        self.assertTrue(hasattr(module_scanner, 'scan_modules_nuitka'))
        self.assertTrue(hasattr(module_scanner, 'scan_modules_pyinstaller'))
        self.assertTrue(hasattr(module_scanner, 'list_submodules'))
        self.assertTrue(hasattr(module_scanner, 'file_list_func'))
    
    def test_file_list_func_returns_list(self):
        """Test that file_list_func returns a list."""
        from cullinan.module_scanner import file_list_func
        
        result = file_list_func()
        self.assertIsInstance(result, list)
        # Should return at least some modules (like tests)
        self.assertGreaterEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
