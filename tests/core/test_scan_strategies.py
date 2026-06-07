# -*- coding: utf-8 -*-
"""Unit tests for scan_strategies.py — the six composable strategy functions."""

import sys
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from cullinan.runtime.scan_strategies import (
    strategy_explicit_modules,
    strategy_user_packages,
    strategy_sys_modules_scan,
    strategy_main_module_inference,
    strategy_directory_scanning,
    strategy_onefile_dir_fallback,
)


class MockConfig:
    """Minimal config mock for strategy testing."""

    def __init__(self, **kwargs):
        self.explicit_modules = kwargs.get("explicit_modules", None)
        self.user_packages = kwargs.get("user_packages", None)
        self.auto_scan = kwargs.get("auto_scan", True)


# ---------------------------------------------------------------------------
# S0: strategy_explicit_modules
# ---------------------------------------------------------------------------

class TestStrategyExplicitModules(unittest.TestCase):
    """Tests for strategy_explicit_modules (S0)."""

    def test_returns_empty_when_not_configured(self):
        config = MockConfig(explicit_modules=None)
        result = strategy_explicit_modules(config)
        self.assertEqual(result, [])

    def test_returns_empty_when_empty_list(self):
        config = MockConfig(explicit_modules=[])
        result = strategy_explicit_modules(config)
        self.assertEqual(result, [])

    @patch("cullinan.runtime.scan_strategies.importlib.import_module")
    @patch("cullinan.runtime.scan_strategies.pkgutil.walk_packages")
    def test_adds_explicit_modules_and_submodules(self, mock_walk, mock_import):
        mock_pkg = MagicMock()
        mock_pkg.__path__ = ["/fake/path"]
        mock_import.return_value = mock_pkg
        mock_walk.return_value = [
            (None, "myapp.services", True),
            (None, "myapp.services.auth", False),
        ]

        config = MockConfig(explicit_modules=["myapp"])
        result = strategy_explicit_modules(config)

        self.assertIn("myapp", result)
        self.assertIn("myapp.services", result)
        self.assertIn("myapp.services.auth", result)

    @patch("cullinan.runtime.scan_strategies.importlib.import_module")
    def test_handles_import_error_gracefully(self, mock_import):
        mock_import.side_effect = ImportError("no such module")

        config = MockConfig(explicit_modules=["nonexistent"])
        result = strategy_explicit_modules(config)

        # Should still add the original module name even if import fails
        self.assertIn("nonexistent", result)


# ---------------------------------------------------------------------------
# S1: strategy_user_packages
# ---------------------------------------------------------------------------

class TestStrategyUserPackages(unittest.TestCase):
    """Tests for strategy_user_packages (S1)."""

    def test_returns_empty_when_not_configured(self):
        config = MockConfig(user_packages=None)
        result = strategy_user_packages(config)
        self.assertEqual(result, [])

    @patch("cullinan.runtime.scan_strategies.importlib.import_module")
    @patch("cullinan.runtime.scan_strategies.pkgutil.walk_packages")
    def test_discovers_packages_and_submodules(self, mock_walk, mock_import):
        mock_pkg = MagicMock()
        mock_pkg.__path__ = ["/fake/path"]
        mock_import.return_value = mock_pkg
        mock_walk.return_value = [
            (None, "myapp.controllers", True),
            (None, "myapp.controllers.user", False),
        ]

        config = MockConfig(user_packages=["myapp"])
        result = strategy_user_packages(config)

        self.assertIn("myapp", result)
        self.assertIn("myapp.controllers", result)

    @patch("cullinan.runtime.scan_strategies.importlib.import_module")
    def test_fallback_to_sys_modules_on_import_error(self, mock_import):
        mock_import.side_effect = ImportError("no module")

        # Directly inject a fake module into sys.modules
        fake_mod = MagicMock()
        sys.modules["myapp.fallback"] = fake_mod
        try:
            config = MockConfig(user_packages=["myapp"])
            result = strategy_user_packages(config)
            self.assertIn("myapp.fallback", result)
        finally:
            del sys.modules["myapp.fallback"]


# ---------------------------------------------------------------------------
# S2: strategy_sys_modules_scan
# ---------------------------------------------------------------------------

class TestStrategySysModulesScan(unittest.TestCase):
    """Tests for strategy_sys_modules_scan (S2)."""

    def test_returns_empty_when_auto_scan_disabled(self):
        config = MockConfig(auto_scan=False)
        result = strategy_sys_modules_scan(config)
        self.assertEqual(result, [])

    @patch("cullinan.runtime.scan_strategies._is_user_module_by_path")
    def test_scans_sys_modules(self, mock_filter):
        mock_filter.side_effect = lambda name, mod: name.startswith("myapp")

        with patch.dict("sys.modules", {
            "myapp.core": MagicMock(),
            "stdlib.json": MagicMock(),
            "myapp.api": MagicMock(),
        }):
            config = MockConfig(auto_scan=True)
            result = strategy_sys_modules_scan(config)

            self.assertIn("myapp.core", result)
            self.assertIn("myapp.api", result)
            self.assertNotIn("stdlib.json", result)


# ---------------------------------------------------------------------------
# S3: strategy_main_module_inference
# ---------------------------------------------------------------------------

class TestStrategyMainModuleInference(unittest.TestCase):
    """Tests for strategy_main_module_inference (S3)."""

    def test_returns_empty_when_no_main_module(self):
        with patch.dict("sys.modules", {}, clear=True):
            result = strategy_main_module_inference(MockConfig())
            self.assertEqual(result, [])

    def test_adds_main_when_has_file(self):
        main_mock = MagicMock()
        main_mock.__file__ = "/fake/main.py"

        with patch.dict("sys.modules", {"__main__": main_mock}):
            result = strategy_main_module_inference(MockConfig())
            self.assertIn("__main__", result)

    def test_infers_package_from_init_py(self):
        import tempfile
        import os

        main_mock = MagicMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package structure: tmpdir/mypkg/__init__.py + main.py
            pkg_dir = os.path.join(tmpdir, "mypkg")
            os.makedirs(pkg_dir)
            with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
                f.write("")

            main_file = os.path.join(pkg_dir, "main.py")
            main_mock.__file__ = main_file

            with patch.dict("sys.modules", {"__main__": main_mock}):
                result = strategy_main_module_inference(MockConfig())
                # __main__ should be included
                self.assertIn("__main__", result)


# ---------------------------------------------------------------------------
# S4: strategy_directory_scanning
# ---------------------------------------------------------------------------

class TestStrategyDirectoryScanning(unittest.TestCase):
    """Tests for strategy_directory_scanning (S4)."""

    def test_returns_empty_for_empty_base_dirs(self):
        config = MockConfig()
        result = strategy_directory_scanning(config, base_dirs=[])
        self.assertEqual(result, [])

    def test_discovers_py_files(self):
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a package with .py files
            pkg_dir = os.path.join(tmpdir, "myapp")
            os.makedirs(pkg_dir)
            with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
                f.write("")
            with open(os.path.join(pkg_dir, "service.py"), "w") as f:
                f.write("")

            config = MockConfig()
            result = strategy_directory_scanning(
                config, base_dirs=[tmpdir]
            )

            self.assertIn("myapp", result)
            self.assertIn("myapp.service", result)

    def test_excludes_cullinan_prefix(self):
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            cullinan_dir = os.path.join(tmpdir, "cullinan")
            os.makedirs(cullinan_dir)
            with open(os.path.join(cullinan_dir, "core.py"), "w") as f:
                f.write("")

            config = MockConfig()
            result = strategy_directory_scanning(
                config, base_dirs=[tmpdir]
            )

            self.assertNotIn("cullinan.core", result)


# ---------------------------------------------------------------------------
# S5: strategy_onefile_dir_fallback
# ---------------------------------------------------------------------------

class TestStrategyOnefileDirFallback(unittest.TestCase):
    """Tests for strategy_onefile_dir_fallback (S5)."""

    @patch("cullinan.runtime.scan_strategies._resolve_caller_package")
    def test_returns_empty_when_no_caller_pkg(self, mock_resolve):
        mock_resolve.return_value = None
        config = MockConfig()
        result = strategy_onefile_dir_fallback(config)
        self.assertEqual(result, [])

    @patch("cullinan.runtime.scan_strategies._resolve_caller_package")
    @patch("cullinan.runtime.scan_strategies.importlib.import_module")
    def test_discovers_submodules_via_dir(self, mock_import, mock_resolve):
        import types
        mock_resolve.return_value = "myapp"

        # Create a real module-like object so inspect.ismodule() passes
        sub_mod = types.ModuleType("myapp.services")

        class FakePkg:
            services = sub_mod

        mock_import.return_value = FakePkg()

        config = MockConfig()
        result = strategy_onefile_dir_fallback(config)

        self.assertIn("myapp.services", result)


if __name__ == "__main__":
    unittest.main()
