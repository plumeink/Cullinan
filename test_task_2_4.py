# -*- coding: utf-8 -*-
"""Test script for Task-2.4: Module Scanning Statistics and Logging

Tests the enhanced module scanning statistics and monitoring capabilities.

Author: Plumeink
"""

import sys
import logging
import time

# Configure logging to see the statistics
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_scan_statistics():
    """Test basic scan statistics collection."""
    from cullinan.scan_stats import (
        ScanStatistics,
        ScanPhase,
        get_scan_stats_collector,
        log_scan_statistics
    )

    print("\n=== Test 1: Basic Scan Statistics ===")

    # Create statistics
    stats = ScanStatistics(
        total_duration_ms=150.5,
        modules_found=25,
        modules_filtered=5,
        scan_mode="auto",
        packaging_mode="development"
    )

    # Add phase durations
    stats.add_phase_duration(ScanPhase.DISCOVERY, 100.0)
    stats.add_phase_duration(ScanPhase.FILTERING, 30.0)
    stats.add_phase_duration(ScanPhase.CACHING, 20.5)

    # Check summary
    summary = stats.get_summary()
    assert "25 modules" in summary
    assert "150.5" in summary or "150.50" in summary

    print(f"Summary: {summary}")
    print(f"Is slow: {stats.is_slow()}")
    print(f"Stats dict: {stats.to_dict()}")

    # Log statistics
    log_scan_statistics(stats, level="info")

    print("✓ Test 1 passed: Basic statistics work\n")
    return True


def test_stats_collector():
    """Test the statistics collector."""
    from cullinan.scan_stats import (
        get_scan_stats_collector,
        reset_scan_stats_collector,
        ScanPhase
    )

    print("=== Test 2: Statistics Collector ===")

    # Reset to start fresh
    reset_scan_stats_collector()
    collector = get_scan_stats_collector()

    # Simulate a scan operation
    collector.start_scan(scan_mode="auto", packaging_mode="development")

    # Simulate discovery phase
    collector.start_phase(ScanPhase.DISCOVERY)
    time.sleep(0.01)  # Simulate work
    collector.end_phase(ScanPhase.DISCOVERY)

    # Record results
    collector.record_modules_found(30)
    collector.record_modules_filtered(5)

    # End scan
    stats = collector.end_scan(10.5)

    assert stats.modules_found == 30
    assert stats.modules_filtered == 5
    assert stats.total_duration_ms == 10.5
    assert ScanPhase.DISCOVERY.value in stats.phase_durations

    print(f"Collected stats: {stats.get_summary()}")
    print(f"Phase durations: {stats.phase_durations}")

    print("✓ Test 2 passed: Statistics collector works\n")
    return True


def test_aggregate_stats():
    """Test aggregate statistics across multiple scans."""
    from cullinan.scan_stats import (
        get_scan_stats_collector,
        reset_scan_stats_collector
    )

    print("=== Test 3: Aggregate Statistics ===")

    # Reset and perform multiple scans
    reset_scan_stats_collector()
    collector = get_scan_stats_collector()

    # Perform 3 simulated scans
    for i in range(3):
        collector.start_scan(scan_mode="auto", packaging_mode="development")
        collector.record_modules_found(10 + i * 5)
        collector.end_scan(50.0 + i * 20.0)

    # Get aggregate stats
    agg_stats = collector.get_aggregate_stats()

    assert agg_stats['total_scans'] == 3
    assert agg_stats['total_modules'] == 10 + 15 + 20  # Sum of modules
    assert agg_stats['avg_duration_ms'] == (50.0 + 70.0 + 90.0) / 3

    print(f"Aggregate stats: {agg_stats}")
    print(f"  Total scans: {agg_stats['total_scans']}")
    print(f"  Avg duration: {agg_stats['avg_duration_ms']}ms")
    print(f"  Total modules: {agg_stats['total_modules']}")

    print("✓ Test 3 passed: Aggregate statistics work\n")
    return True


def test_module_scanner_integration():
    """Test integration with module scanner."""
    from cullinan.module_scanner import file_list_func
    from cullinan.scan_stats import get_scan_stats_collector, reset_scan_stats_collector

    print("=== Test 4: Module Scanner Integration ===")

    # Reset stats
    reset_scan_stats_collector()

    # Trigger module scanning (which should collect statistics)
    print("Triggering module scan...")
    modules = file_list_func()

    print(f"Found {len(modules)} modules")

    # Check that statistics were collected
    collector = get_scan_stats_collector()
    agg_stats = collector.get_aggregate_stats()

    # Should have at least one scan
    assert agg_stats['total_scans'] >= 1, "Statistics should be collected"

    print(f"Scan statistics collected: {agg_stats['total_scans']} scan(s)")
    print(f"Average duration: {agg_stats['avg_duration_ms']}ms")

    print("✓ Test 4 passed: Integration with module scanner works\n")
    return True


def test_export_statistics():
    """Test exporting statistics to JSON."""
    import os
    import json
    from cullinan.scan_stats import (
        get_scan_stats_collector,
        reset_scan_stats_collector,
        export_scan_statistics
    )

    print("=== Test 5: Export Statistics ===")

    # Reset and create some stats
    reset_scan_stats_collector()
    collector = get_scan_stats_collector()

    collector.start_scan(scan_mode="auto", packaging_mode="development")
    collector.record_modules_found(20)
    collector.end_scan(75.0)

    # Export to file
    output_file = "test_scan_stats.json"
    export_scan_statistics(output_file)

    # Verify file was created
    assert os.path.exists(output_file), "Statistics file should be created"

    # Read and verify content
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert 'aggregate' in data
    assert 'scans' in data
    assert data['aggregate']['total_scans'] == 1
    assert len(data['scans']) == 1

    print(f"Exported statistics to {output_file}")
    print(f"Content: {json.dumps(data, indent=2)}")

    # Cleanup
    os.remove(output_file)

    print("✓ Test 5 passed: Export statistics works\n")
    return True


def test_error_recording():
    """Test error recording in statistics."""
    from cullinan.scan_stats import get_scan_stats_collector, reset_scan_stats_collector

    print("=== Test 6: Error Recording ===")

    reset_scan_stats_collector()
    collector = get_scan_stats_collector()

    collector.start_scan(scan_mode="auto", packaging_mode="development")

    # Record some errors
    collector.record_error("Failed to import module: test_module")
    collector.record_error("Module not found: another_module")

    collector.record_modules_found(10)
    stats = collector.end_scan(100.0)

    assert len(stats.errors) == 2
    assert "test_module" in stats.errors[0]
    assert "another_module" in stats.errors[1]

    print(f"Recorded {len(stats.errors)} errors")
    for error in stats.errors:
        print(f"  - {error}")

    print("✓ Test 6 passed: Error recording works\n")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("Task-2.4: Module Scanning Statistics and Logging")
    print("=" * 70)

    tests = [
        test_scan_statistics,
        test_stats_collector,
        test_aggregate_stats,
        test_module_scanner_integration,
        test_export_statistics,
        test_error_recording,
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
        print("\n✓ All tests passed! Task-2.4 implementation is working correctly.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

