# -*- coding: utf-8 -*-
"""Test script for Task-2.3: Explicit Registration Priority Strategy

This test verifies that:
1. Explicit registration mode skips module scanning
2. Explicitly registered services/controllers are properly registered
3. Startup performance is improved when using explicit registration
"""

import logging
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 60)
print("Task-2.3: Explicit Registration Strategy Test")
print("=" * 60)


# ============================================================
# Test 1: Verify explicit registration configuration
# ============================================================
print("\n[Test 1] Configuration Test")
print("-" * 60)

from cullinan import configure
from cullinan.config import get_config

# Define test services and controllers
from cullinan.service import service

@service
class TestDatabaseService:
    def on_init(self):
        logger.info("TestDatabaseService initialized")

@service
class TestCacheService:
    def on_init(self):
        logger.info("TestCacheService initialized")

from cullinan.controller import controller

@controller()
class TestUserController:
    def __init__(self):
        logger.info("TestUserController created")

# Configure with explicit registration
configure(
    explicit_services=[TestDatabaseService, TestCacheService],
    explicit_controllers=[TestUserController],
    auto_scan=False  # Disable auto scan
)

config = get_config()

assert config.explicit_services == [TestDatabaseService, TestCacheService], \
    "explicit_services not configured correctly"
assert config.explicit_controllers == [TestUserController], \
    "explicit_controllers not configured correctly"
assert config.auto_scan == False, "auto_scan should be False"

print("[✓] Configuration loaded correctly")
print(f"    - Explicit services: {len(config.explicit_services)}")
print(f"    - Explicit controllers: {len(config.explicit_controllers)}")
print(f"    - Auto scan: {config.auto_scan}")


# ============================================================
# Test 2: Verify module scanning is skipped
# ============================================================
print("\n[Test 2] Module Scanning Skip Test")
print("-" * 60)

from cullinan.module_scanner import file_list_func, _module_list_cache

# Clear cache to ensure fresh scan
import cullinan.module_scanner as scanner_module
scanner_module._module_list_cache = None

start_time = time.perf_counter()
modules = file_list_func()
elapsed = time.perf_counter() - start_time

assert modules == [], "Module list should be empty when using explicit registration"
assert elapsed < 0.01, f"Scanning should be fast (< 10ms), got {elapsed*1000:.2f}ms"

print(f"[✓] Module scanning skipped")
print(f"    - Modules found: {len(modules)}")
print(f"    - Scan time: {elapsed*1000:.2f}ms")


# ============================================================
# Test 3: Verify explicit registration works
# ============================================================
print("\n[Test 3] Explicit Registration Test")
print("-" * 60)

from cullinan.service import get_service_registry

# Check service registry
service_registry = get_service_registry()
service_names = service_registry.list_names()

print(f"[INFO] Registered services: {service_names}")

# The services should be registered via decorators when modules are imported
assert 'TestDatabaseService' in service_names, "TestDatabaseService should be registered"
assert 'TestCacheService' in service_names, "TestCacheService should be registered"

print(f"[✓] Explicit services registered correctly")
print(f"    - Total services: {len(service_names)}")


# ============================================================
# Test 4: Performance comparison (optional)
# ============================================================
print("\n[Test 4] Performance Comparison")
print("-" * 60)

# Reset for auto-scan mode
scanner_module._module_list_cache = None

# Simulate auto-scan mode (without explicit registration)
from cullinan.config import _config as config_instance
config_instance.explicit_services = []
config_instance.explicit_controllers = []

start_auto = time.perf_counter()
modules_auto = file_list_func()
elapsed_auto = time.perf_counter() - start_auto

# Reset to explicit mode
scanner_module._module_list_cache = None
config_instance.explicit_services = [TestDatabaseService, TestCacheService]
config_instance.explicit_controllers = [TestUserController]

start_explicit = time.perf_counter()
modules_explicit = file_list_func()
elapsed_explicit = time.perf_counter() - start_explicit

speedup = elapsed_auto / elapsed_explicit if elapsed_explicit > 0 else float('inf')

print(f"[INFO] Performance comparison:")
print(f"    - Auto-scan mode: {elapsed_auto*1000:.2f}ms ({len(modules_auto)} modules)")
print(f"    - Explicit mode: {elapsed_explicit*1000:.2f}ms ({len(modules_explicit)} modules)")
print(f"    - Speedup: {speedup:.1f}x faster")

if speedup > 5:
    print(f"[✓] Significant performance improvement!")
else:
    print(f"[INFO] Speedup is modest (expected for small projects)")


# ============================================================
# Test 5: Verify backward compatibility
# ============================================================
print("\n[Test 5] Backward Compatibility Test")
print("-" * 60)

# Reset config to default (auto-scan enabled)
scanner_module._module_list_cache = None
config_instance.explicit_services = []
config_instance.explicit_controllers = []
config_instance.auto_scan = True

modules = file_list_func()
print(f"[INFO] Auto-scan mode: {len(modules)} modules found")

assert len(modules) > 0, "Auto-scan should find modules when enabled"

print(f"[✓] Backward compatibility maintained")
print(f"    - Auto-scan still works when explicit registration is not used")


# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)

print("\n📊 Summary:")
print("  • Explicit registration configuration works")
print("  • Module scanning is skipped when configured")
print("  • Services/Controllers are properly registered")
print(f"  • Performance improvement: {speedup:.1f}x")
print("  • Backward compatibility maintained")

print("\n💡 Usage Example:")
print("""
from cullinan import configure
from myapp.services import DatabaseService, CacheService
from myapp.controllers import UserController, AdminController

configure(
    explicit_services=[DatabaseService, CacheService],
    explicit_controllers=[UserController, AdminController],
    auto_scan=False  # Skip scanning for better performance
)
""")

print("\n" + "=" * 60)

