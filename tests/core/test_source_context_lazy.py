# -*- coding: utf-8 -*-
"""Tests verifying that getsourcelines() is no longer called during decorator processing."""

import unittest
from unittest.mock import MagicMock, patch

from cullinan.core.decorators import _build_source_context


class TestSourceContextLazy(unittest.TestCase):
    """Verify that _build_source_context avoids getsourcelines()."""

    def test_source_line_is_none(self):
        """source_line should be None since getsourcelines() is removed."""
        class SampleService:
            pass

        result = _build_source_context(SampleService)
        self.assertIsNotNone(result["source_file"])
        self.assertIsNone(result["source_line"])
        self.assertFalse(result["is_top_level"])

    def test_source_file_is_captured(self):
        """source_file should still be captured (cheap inspect.getfile)."""
        class AnotherService:
            pass

        result = _build_source_context(AnotherService)
        self.assertIn("test_source_context_lazy.py", result["source_file"])

    @patch("cullinan.core.decorators.inspect.getsourcelines")
    def test_getsourcelines_not_called(self, mock_getsourcelines):
        """Verify inspect.getsourcelines() is never invoked."""
        class YetAnotherService:
            pass

        _build_source_context(YetAnotherService)
        mock_getsourcelines.assert_not_called()

    def test_is_top_level_detection(self):
        """is_top_level should still work based on qualname."""
        class TopLevelService:
            pass

        result = _build_source_context(TopLevelService)
        self.assertFalse(result["is_top_level"])

    def test_source_qualname_captured(self):
        """source_qualname should be the class's __qualname__."""
        class QualNameService:
            class Nested:
                pass

        result = _build_source_context(QualNameService.Nested)
        self.assertEqual(
            result["source_qualname"],
            "TestSourceContextLazy.test_source_qualname_captured.<locals>.QualNameService.Nested",
        )

    def test_cache_is_used_for_same_class(self):
        """The cache should prevent repeated processing of the same class."""
        class CachedService:
            pass

        result1 = _build_source_context(CachedService)
        result2 = _build_source_context(CachedService)
        self.assertIs(result1, result2)  # Same dict object (cache hit)


if __name__ == "__main__":
    unittest.main()
