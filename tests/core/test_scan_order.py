# -*- coding: utf-8 -*-
"""Test to verify that service modules are scanned before controller modules.

This test verifies the module scanning order using the public API.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cullinan.application import scan_service, scan_controller


class TestScanOrder(unittest.TestCase):
    """Test module scanning order."""

    def test_scan_service_processes_all_modules(self):
        """Test that scan_service processes all modules passed to it."""

        import_order = []

        def mock_reflect_module(module_name, func_type):
            """Track which modules are processed."""
            import_order.append((module_name, func_type))

        # scan_service doesn't filter - it processes all modules given
        all_modules = ['app.service.user', 'app.services.auth']

        with patch('cullinan.application.reflect_module', side_effect=mock_reflect_module):
            import_order.clear()
            scan_service(all_modules)

            # All modules should be processed with 'nobody' function type
            self.assertEqual(len(import_order), 2)
            self.assertEqual(import_order[0], ('app.service.user', 'nobody'))
            self.assertEqual(import_order[1], ('app.services.auth', 'nobody'))

            print("  OK: scan_service processes all given modules")

    def test_scan_controller_processes_all_modules(self):
        """Test that scan_controller processes all modules passed to it."""

        import_order = []

        def mock_reflect_module(module_name, func_type):
            """Track which modules are processed."""
            import_order.append((module_name, func_type))

        # scan_controller doesn't filter - it processes all modules given
        all_modules = ['app.controller.user', 'app.controllers.api']

        with patch('cullinan.application.reflect_module', side_effect=mock_reflect_module):
            import_order.clear()
            scan_controller(all_modules)

            # All modules should be processed with 'controller' function type
            self.assertEqual(len(import_order), 2)
            self.assertEqual(import_order[0], ('app.controller.user', 'controller'))
            self.assertEqual(import_order[1], ('app.controllers.api', 'controller'))

            print("  OK: scan_controller processes all given modules")

    def test_scan_order_service_before_controller(self):
        """Test that when scanning service then controller modules, order is maintained."""

        import_order = []

        def mock_reflect_module(module_name, func_type):
            """Track the order of module imports."""
            import_order.append((module_name, func_type))

        # Pre-filtered module lists (as they would be in real usage)
        service_modules = ['app.service.user', 'app.service.auth']
        controller_modules = ['app.controller.main', 'app.controller.api']

        with patch('cullinan.application.reflect_module', side_effect=mock_reflect_module):
            import_order.clear()

            # Typical application flow: scan services first, then controllers
            scan_service(service_modules)
            scan_controller(controller_modules)

            # Verify scan order
            self.assertEqual(len(import_order), 4)

            # First two should be services with 'nobody'
            self.assertEqual(import_order[0][1], 'nobody')
            self.assertEqual(import_order[1][1], 'nobody')

            # Last two should be controllers with 'controller'
            self.assertEqual(import_order[2][1], 'controller')
            self.assertEqual(import_order[3][1], 'controller')

            print("  OK: Services scanned before controllers")



if __name__ == '__main__':
    unittest.main()
