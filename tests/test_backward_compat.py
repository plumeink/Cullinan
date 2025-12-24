# -*- coding: utf-8 -*-
"""Test script for backward compatibility code separation

Tests that backward compatibility code is properly separated and marked.

Author: Plumeink
"""

import sys
import logging
import warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_deprecation_decorator():
    """Test the deprecation decorator."""
    from cullinan.deprecation import deprecated

    print("\n=== Test 1: Deprecation Decorator ===")

    @deprecated(version="0.8", alternative="new_function()", removal_version="1.0")
    def old_function():
        return "result"

    # Should trigger deprecation warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = old_function()

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
        assert "0.8" in str(w[0].message)
        assert "1.0" in str(w[0].message)

    print("✓ Deprecation warning triggered correctly")
    print(f"✓ Warning message: {w[0].message}")
    print("✓ Test 1 passed\n")
    return True


def test_deprecation_manager():
    """Test the deprecation manager."""
    from cullinan.deprecation import (
        get_deprecation_manager,
        reset_deprecation_manager,
        DeprecationError
    )

    print("=== Test 2: Deprecation Manager ===")

    # Reset to start fresh
    reset_deprecation_manager()
    manager = get_deprecation_manager()

    # Test enable/disable
    assert manager.is_enabled()
    manager.disable()
    assert not manager.is_enabled()
    manager.enable()
    assert manager.is_enabled()

    print("✓ Enable/disable works")

    # Test warn_once
    manager.warn_once("test_key", "Test warning")
    manager.warn_once("test_key", "Test warning")  # Should only warn once

    print("✓ warn_once works")

    # Test strict mode
    manager.set_strict_mode(True)
    assert manager.is_strict()

    try:
        manager.warn_once("strict_test", "Strict mode test")
        assert False, "Should have raised DeprecationError"
    except DeprecationError:
        print("✓ Strict mode raises error")

    # Reset strict mode
    manager.set_strict_mode(False)

    print("✓ Test 2 passed\n")
    return True


def test_legacy_middleware_api():
    """Test legacy middleware registration API."""
    from cullinan.middleware import (
        Middleware,
        register_middleware_manual,
        get_registered_middlewares
    )

    print("=== Test 3: Legacy Middleware API ===")

    class TestMiddleware(Middleware):
        def process_request(self, handler):
            return handler

    # Should trigger deprecation warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        register_middleware_manual(TestMiddleware, priority=50)

        assert len(w) >= 1
        # Find the deprecation warning
        deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(deprecation_warnings) > 0

    print("✓ Legacy middleware registration triggers warning")

    # get_registered_middlewares should also trigger warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        middlewares = get_registered_middlewares()

        deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(deprecation_warnings) > 0

    print("✓ Legacy get_registered_middlewares triggers warning")
    print("✓ Test 3 passed\n")
    return True


def test_backward_compat_config():
    """Test backward compatibility configuration."""
    from cullinan.config import get_config

    print("=== Test 4: Backward Compatibility Config ===")

    config = get_config()

    # Check that enable_backward_compat exists
    assert hasattr(config, 'enable_backward_compat')
    assert config.enable_backward_compat == True  # Default should be True

    print("✓ enable_backward_compat config exists")
    print(f"✓ Default value: {config.enable_backward_compat}")

    # Test changing the value
    config.enable_backward_compat = False
    assert config.enable_backward_compat == False

    # Restore
    config.enable_backward_compat = True

    print("✓ Config can be changed")
    print("✓ Test 4 passed\n")
    return True


def test_backward_compat_markers():
    """Test that backward compatibility markers are in place."""
    import os
    import re

    print("=== Test 5: Backward Compatibility Markers ===")

    # Files that should have BACKWARD_COMPAT markers
    files_to_check = [
        'cullinan/core/__init__.py',
        'cullinan/config.py',
        'cullinan/middleware/__init__.py',
        'cullinan/middleware/legacy.py',
    ]

    found_markers = {}
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for file_path in files_to_check:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                markers = re.findall(r'BACKWARD_COMPAT:.*', content)
                if markers:
                    found_markers[file_path] = len(markers)

    assert len(found_markers) > 0, "Should find some BACKWARD_COMPAT markers"

    for file_path, count in found_markers.items():
        print(f"✓ {file_path}: {count} marker(s)")

    print(f"✓ Total files with markers: {len(found_markers)}")
    print("✓ Test 5 passed\n")
    return True


def test_deprecation_info():
    """Test getting deprecation information from decorated objects."""
    from cullinan.deprecation import deprecated, is_deprecated, get_deprecation_info

    print("=== Test 6: Deprecation Info ===")

    @deprecated(version="0.8", alternative="new_func()", removal_version="1.0")
    def old_func():
        return "result"

    # Check if marked as deprecated
    assert is_deprecated(old_func)
    print("✓ Function marked as deprecated")

    # Get deprecation info
    info = get_deprecation_info(old_func)
    assert info is not None
    assert info['version'] == "0.8"
    assert info['alternative'] == "new_func()"
    assert info['removal_version'] == "1.0"

    print(f"✓ Deprecation info: {info}")

    # Non-deprecated function
    def new_func():
        return "result"

    assert not is_deprecated(new_func)
    assert get_deprecation_info(new_func) is None

    print("✓ Non-deprecated function not marked")
    print("✓ Test 6 passed\n")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("Backward Compatibility Code Separation Tests")
    print("=" * 70)

    tests = [
        test_deprecation_decorator,
        test_deprecation_manager,
        test_legacy_middleware_api,
        test_backward_compat_config,
        test_backward_compat_markers,
        test_deprecation_info,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} failed: {e}", exc_info=True)
            failed += 1

    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n✓ All tests passed! Backward compatibility code is properly separated.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

