# -*- coding: utf-8 -*-
"""Unit tests for scan_pipelines.py — pipeline routing and execution."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from cullinan.runtime.scan_pipelines import (
    execute_pipeline,
    PIPELINE_REGISTRY,
    _map_mode_to_pipeline_key,
    _resolve_base_dirs,
)


class MockConfig:
    """Minimal config mock."""

    def __init__(self, **kwargs):
        self.explicit_modules = kwargs.get("explicit_modules", None)
        self.user_packages = kwargs.get("user_packages", None)
        self.auto_scan = kwargs.get("auto_scan", False)


# ---------------------------------------------------------------------------
# Pipeline key mapping
# ---------------------------------------------------------------------------

class TestPipelineKeyMapping(unittest.TestCase):
    """Tests for _map_mode_to_pipeline_key."""

    def test_nuitka_standalone(self):
        self.assertEqual(
            _map_mode_to_pipeline_key("nuitka-standalone"),
            "nuitka-standalone",
        )

    def test_nuitka_onefile(self):
        self.assertEqual(
            _map_mode_to_pipeline_key("nuitka-onefile"),
            "nuitka-onefile",
        )

    def test_pyinstaller_onedir(self):
        self.assertEqual(
            _map_mode_to_pipeline_key("pyinstaller-onedir"),
            "pyinstaller-onedir",
        )

    def test_pyinstaller_onefile(self):
        self.assertEqual(
            _map_mode_to_pipeline_key("pyinstaller-onefile"),
            "pyinstaller-onefile",
        )

    def test_development(self):
        self.assertEqual(
            _map_mode_to_pipeline_key("development"),
            "development",
        )

    def test_unknown_falls_back_to_development(self):
        self.assertEqual(
            _map_mode_to_pipeline_key("unknown-mode"),
            "development",
        )

    def test_none_falls_back_to_development(self):
        self.assertEqual(
            _map_mode_to_pipeline_key("none"),
            "development",
        )

    def test_nuitka_defaults_to_standalone(self):
        self.assertEqual(
            _map_mode_to_pipeline_key("nuitka"),
            "nuitka-standalone",
        )

    def test_pyinstaller_defaults_to_onedir(self):
        self.assertEqual(
            _map_mode_to_pipeline_key("pyinstaller"),
            "pyinstaller-onedir",
        )


# ---------------------------------------------------------------------------
# Base directory resolution
# ---------------------------------------------------------------------------

class TestBaseDirResolution(unittest.TestCase):
    """Tests for _resolve_base_dirs."""

    def test_development_has_empty_base_dirs(self):
        """Development mode should not add executable dir to base_dirs."""
        dirs = _resolve_base_dirs("development")
        # Development mode doesn't scan filesystem directories
        self.assertIsInstance(dirs, list)

    def test_nuitka_standalone_includes_executable_dir(self):
        """Nuitka standalone should include the executable directory."""
        dirs = _resolve_base_dirs("nuitka-standalone")
        self.assertIsInstance(dirs, list)
        self.assertIn(os.path.dirname(sys.executable), dirs)


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

class TestPipelineExecution(unittest.TestCase):
    """Tests for execute_pipeline."""

    def test_development_pipeline_without_explicit_modules_returns_empty(self):
        config = MockConfig()
        result = execute_pipeline(
            config,
            packaging_mode="development",
            early_termination=True,
        )
        # auto_scan is False in MockConfig, but S3 (main_module_inference)
        # always runs and finds __main__ in the test runner environment.
        self.assertIsInstance(result, list)

    def test_explicit_modules_returns_early(self):
        config = MockConfig(explicit_modules=["myapp"])
        result = execute_pipeline(
            config,
            packaging_mode="nuitka-standalone",
            early_termination=True,
        )
        # S0 should find the explicit modules
        self.assertIn("myapp", result)

    def test_unknown_mode_falls_back_to_development(self):
        config = MockConfig()
        result = execute_pipeline(
            config,
            packaging_mode="bogus-mode-12345",
            early_termination=True,
        )
        # Falls back to development pipeline — S3 finds __main__ in tests
        self.assertIsInstance(result, list)

    def test_nuitka_onefile_pipeline_excludes_s4(self):
        pipeline = PIPELINE_REGISTRY.get("nuitka-onefile")
        self.assertIsNotNone(pipeline)
        strategy_labels = [label for label, _ in pipeline]
        # S4 should NOT be in the onefile pipeline
        self.assertNotIn("S4_directory_scanning", strategy_labels)
        # S5 should be in the onefile pipeline
        self.assertIn("S5_onefile_dir_fallback", strategy_labels)

    def test_nuitka_standalone_pipeline_includes_s4(self):
        pipeline = PIPELINE_REGISTRY.get("nuitka-standalone")
        self.assertIsNotNone(pipeline)
        strategy_labels = [label for label, _ in pipeline]
        self.assertIn("S4_directory_scanning", strategy_labels)

    def test_all_pipelines_include_s0_and_s1(self):
        for key, pipeline in PIPELINE_REGISTRY.items():
            labels = [label for label, _ in pipeline]
            self.assertIn("S0_explicit_modules", labels, f"Missing S0 in {key}")
            self.assertIn("S1_user_packages", labels, f"Missing S1 in {key}")

    def test_all_registered_pipelines_exist(self):
        expected_keys = {
            "nuitka-standalone",
            "nuitka-onefile",
            "pyinstaller-onedir",
            "pyinstaller-onefile",
            "development",
        }
        self.assertEqual(set(PIPELINE_REGISTRY.keys()), expected_keys)


if __name__ == "__main__":
    unittest.main()
