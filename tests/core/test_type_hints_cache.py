# -*- coding: utf-8 -*-
"""Unit tests for the module-level global type hints cache."""

import unittest
from unittest.mock import MagicMock, patch

from cullinan.core.application_context import (
    _global_type_hints_cache,
    invalidate_type_hints_cache,
)


class TestGlobalTypeHintsCache(unittest.TestCase):
    """Tests for _global_type_hints_cache lifecycle."""

    def setUp(self):
        invalidate_type_hints_cache()

    def tearDown(self):
        invalidate_type_hints_cache()

    def test_cache_is_module_level_singleton(self):
        """Verify the cache is a module-level dict, not instance-level."""
        self.assertIsInstance(_global_type_hints_cache, dict)

    def test_invalidate_clears_cache(self):
        _global_type_hints_cache[12345] = ({}, {}, None)
        self.assertEqual(len(_global_type_hints_cache), 1)

        invalidate_type_hints_cache()
        self.assertEqual(len(_global_type_hints_cache), 0)

    def test_cache_survives_multiple_context_instances(self):
        """Verify cache is shared across ApplicationContext instances."""
        from cullinan.core.application_context import ApplicationContext

        invalidate_type_hints_cache()

        class SharedService:
            pass

        ctx1 = ApplicationContext(container_id="ctx1")
        ctx2 = ApplicationContext(container_id="ctx2")

        # Resolve through ctx1
        result1 = ctx1._get_class_type_hints(SharedService)
        # Resolve through ctx2 — should hit the same cache
        result2 = ctx2._get_class_type_hints(SharedService)

        # Same result object (same cache entry)
        self.assertIs(result1, result2)
        self.assertIn(id(SharedService), _global_type_hints_cache)

    def test_successful_resolution_is_cached(self):
        """Verify that successful type_hints resolution is cached."""
        from cullinan.core.application_context import ApplicationContext

        invalidate_type_hints_cache()

        class GoodHints:
            name: str

        ctx = ApplicationContext()
        result = ctx._get_class_type_hints(GoodHints)

        self.assertEqual(result[0], {"name": str})
        self.assertIsNone(result[2])  # no exception
        self.assertIn(id(GoodHints), _global_type_hints_cache)

    def test_invalidation_from_pending_registry_reset(self):
        """Verify PendingRegistry.reset() calls invalidate_type_hints_cache."""
        from cullinan.core.pending import PendingRegistry

        _global_type_hints_cache[99999] = ({}, {}, None)
        self.assertEqual(len(_global_type_hints_cache), 1)

        PendingRegistry.reset()
        self.assertEqual(len(_global_type_hints_cache), 0)


if __name__ == "__main__":
    unittest.main()
