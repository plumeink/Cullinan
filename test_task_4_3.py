# -*- coding: utf-8 -*-
"""Test script for Task-4.3: RequestContext Feature Flags

Tests the configurable feature flags for RequestContext.

Author: Plumeink
"""

import sys
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_default_features():
    """Test RequestContext with default features."""
    from cullinan.core.context import RequestContext

    print("\n=== Test 1: Default Features ===")

    # Reset to ensure clean state
    RequestContext.reset_features()

    ctx = RequestContext()

    # Should have auto-generated request_id
    request_id = ctx.get('request_id')
    assert request_id is not None, "Should have auto-generated request_id"
    print(f"✓ Auto-generated request_id: {request_id}")

    # Should support timing
    elapsed = ctx.elapsed_time()
    assert elapsed is not None, "Should support timing"
    assert elapsed >= 0, "Elapsed time should be non-negative"
    print(f"✓ Timing enabled: {elapsed:.6f}s")

    # Should support metadata
    ctx.set_metadata('test_key', 'test_value')
    meta_value = ctx.get_metadata('test_key')
    assert meta_value == 'test_value', "Should support metadata"
    print("✓ Metadata enabled")

    # Should support cleanup callbacks
    callback_called = []
    ctx.register_cleanup(lambda: callback_called.append(True))
    ctx.cleanup()
    assert callback_called, "Should support cleanup callbacks"
    print("✓ Cleanup callbacks enabled")

    print("✓ Test 1 passed: Default features work\n")
    return True


def test_disabled_auto_request_id():
    """Test with auto_request_id disabled."""
    from cullinan.config import get_config
    from cullinan.core.context import RequestContext

    print("=== Test 2: Disabled Auto Request ID ===")

    # Configure
    config = get_config()
    config.context_features['auto_request_id'] = False
    RequestContext.reset_features()

    ctx = RequestContext()

    # Should NOT have auto-generated request_id
    request_id = ctx.get('request_id')
    assert request_id is None, "Should NOT have auto-generated request_id"
    print("✓ Auto request_id disabled")

    # Restore
    config.context_features['auto_request_id'] = True
    RequestContext.reset_features()

    print("✓ Test 2 passed: Auto request_id can be disabled\n")
    return True


def test_disabled_timing():
    """Test with timing disabled."""
    from cullinan.config import get_config
    from cullinan.core.context import RequestContext

    print("=== Test 3: Disabled Timing ===")

    # Configure
    config = get_config()
    config.context_features['timing'] = False
    RequestContext.reset_features()

    ctx = RequestContext()

    # Should NOT support timing
    elapsed = ctx.elapsed_time()
    assert elapsed is None, "Should NOT support timing when disabled"
    print("✓ Timing disabled")

    # Restore
    config.context_features['timing'] = True
    RequestContext.reset_features()

    print("✓ Test 3 passed: Timing can be disabled\n")
    return True


def test_disabled_metadata():
    """Test with metadata disabled."""
    from cullinan.config import get_config
    from cullinan.core.context import RequestContext

    print("=== Test 4: Disabled Metadata ===")

    # Configure
    config = get_config()
    config.context_features['metadata'] = False
    RequestContext.reset_features()

    ctx = RequestContext()

    # Should NOT support metadata
    ctx.set_metadata('test_key', 'test_value')
    meta_value = ctx.get_metadata('test_key')
    assert meta_value is None, "Should NOT support metadata when disabled"
    print("✓ Metadata disabled")

    # Restore
    config.context_features['metadata'] = True
    RequestContext.reset_features()

    print("✓ Test 4 passed: Metadata can be disabled\n")
    return True


def test_disabled_cleanup_callbacks():
    """Test with cleanup_callbacks disabled."""
    from cullinan.config import get_config
    from cullinan.core.context import RequestContext

    print("=== Test 5: Disabled Cleanup Callbacks ===")

    # Configure
    config = get_config()
    config.context_features['cleanup_callbacks'] = False
    RequestContext.reset_features()

    ctx = RequestContext()

    # Should NOT support cleanup callbacks
    callback_called = []
    ctx.register_cleanup(lambda: callback_called.append(True))
    ctx.cleanup()
    assert not callback_called, "Should NOT support cleanup callbacks when disabled"
    print("✓ Cleanup callbacks disabled")

    # Restore
    config.context_features['cleanup_callbacks'] = True
    RequestContext.reset_features()

    print("✓ Test 5 passed: Cleanup callbacks can be disabled\n")
    return True


def test_sequential_request_id():
    """Test sequential request ID format."""
    from cullinan.config import get_config
    from cullinan.core.context import RequestContext

    print("=== Test 6: Sequential Request ID ===")

    # Configure
    config = get_config()
    config.context_features['request_id_format'] = 'sequential'
    RequestContext.reset_features()

    # Create multiple contexts
    ctx1 = RequestContext()
    ctx2 = RequestContext()
    ctx3 = RequestContext()

    req_id1 = ctx1.get('request_id')
    req_id2 = ctx2.get('request_id')
    req_id3 = ctx3.get('request_id')

    # Should be sequential
    assert 'req_' in req_id1, "Should use 'req_' prefix"
    assert 'req_' in req_id2, "Should use 'req_' prefix"
    assert 'req_' in req_id3, "Should use 'req_' prefix"

    print(f"✓ Sequential IDs: {req_id1}, {req_id2}, {req_id3}")

    # Restore
    config.context_features['request_id_format'] = 'uuid'
    RequestContext.reset_features()

    print("✓ Test 6 passed: Sequential request ID works\n")
    return True


def test_custom_request_id_generator():
    """Test custom request ID generator."""
    from cullinan.config import get_config
    from cullinan.core.context import RequestContext

    print("=== Test 7: Custom Request ID Generator ===")

    # Configure
    config = get_config()
    config.context_features['request_id_format'] = 'custom'
    config.context_features['custom_request_id_generator'] = lambda: 'custom-id-12345'
    RequestContext.reset_features()

    ctx = RequestContext()
    request_id = ctx.get('request_id')

    assert request_id == 'custom-id-12345', "Should use custom generator"
    print(f"✓ Custom request_id: {request_id}")

    # Restore
    config.context_features['request_id_format'] = 'uuid'
    config.context_features['custom_request_id_generator'] = None
    RequestContext.reset_features()

    print("✓ Test 7 passed: Custom request ID generator works\n")
    return True


def test_performance_with_disabled_features():
    """Test performance improvement with disabled features."""
    from cullinan.config import get_config
    from cullinan.core.context import RequestContext

    print("=== Test 8: Performance with Disabled Features ===")

    # Measure with all features enabled
    config = get_config()
    RequestContext.reset_features()

    start = time.perf_counter()
    for _ in range(10000):
        ctx = RequestContext()
        ctx.set('key', 'value')
        ctx.set_metadata('meta', 'data')
        ctx.register_cleanup(lambda: None)
    elapsed_enabled = time.perf_counter() - start

    # Measure with features disabled
    config.context_features['metadata'] = False
    config.context_features['cleanup_callbacks'] = False
    config.context_features['timing'] = False
    config.context_features['debug_logging'] = False
    RequestContext.reset_features()

    start = time.perf_counter()
    for _ in range(10000):
        ctx = RequestContext()
        ctx.set('key', 'value')
        ctx.set_metadata('meta', 'data')  # Should be no-op
        ctx.register_cleanup(lambda: None)  # Should be no-op
    elapsed_disabled = time.perf_counter() - start

    print(f"With features enabled:  {elapsed_enabled*1000:.2f}ms")
    print(f"With features disabled: {elapsed_disabled*1000:.2f}ms")
    print(f"Speedup: {elapsed_enabled/elapsed_disabled:.2f}x")

    # Should be faster (or at least not slower)
    assert elapsed_disabled <= elapsed_enabled * 1.1, "Disabled features should not be slower"

    # Restore
    config.context_features['metadata'] = True
    config.context_features['cleanup_callbacks'] = True
    config.context_features['timing'] = True
    RequestContext.reset_features()

    print("✓ Test 8 passed: Performance impact verified\n")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("Task-4.3: RequestContext Feature Flags")
    print("=" * 70)

    tests = [
        test_default_features,
        test_disabled_auto_request_id,
        test_disabled_timing,
        test_disabled_metadata,
        test_disabled_cleanup_callbacks,
        test_sequential_request_id,
        test_custom_request_id_generator,
        test_performance_with_disabled_features,
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
        print("\n✓ All tests passed! Task-4.3 implementation is working correctly.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

