# -*- coding: utf-8 -*-
"""
最终验证脚本 - 测试所有核心修复功能

避免 Unicode 字符以兼容 Windows GBK 编码。
"""

import sys
import os

project_path = r'G:\pj\Cullinan'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

print("="*70)
print("Cullinan Core IoC/DI Fix Verification")
print("="*70)

passed = 0
failed = 0

# Test 1: MRO Lookup
print("\n[Test 1] MRO Metadata Lookup...")
try:
    from cullinan.core import Inject, injectable, get_injection_registry, reset_injection_registry
    from cullinan.core.registry import SimpleRegistry

    reset_injection_registry()
    registry = get_injection_registry()

    service_registry = SimpleRegistry()

    class TestService:
        def __init__(self):
            self.value = "test"

    service_registry.register('TestService', TestService())
    registry.add_provider_registry(service_registry)

    @injectable
    class BaseClass:
        service: TestService = Inject()

    class SubClass(BaseClass):
        pass

    instance = SubClass()
    assert hasattr(instance, 'service'), "SubClass should have service attribute"
    assert instance.service.value == "test", "Service value should be 'test'"

    print("  [PASS] Subclass inherits parent injection")
    passed += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    failed += 1

# Test 2: Thread Safety
print("\n[Test 2] Thread Safety...")
try:
    import threading
    from cullinan.core.registry import SimpleRegistry

    registry = SimpleRegistry()
    errors = []

    def register_items(tid):
        try:
            for i in range(50):
                registry.register(f"item_{tid}_{i}", f"value_{tid}_{i}")
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=register_items, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    expected = 5 * 50
    actual = registry.count()

    assert actual == expected, f"Expected {expected} items, got {actual}"
    assert len(errors) == 0, f"Got {len(errors)} errors"

    print(f"  [PASS] Concurrent registration stable ({actual} items)")
    passed += 1
except Exception as e:
    print(f"  [FAIL] {e}")
    failed += 1

# Test 3: Duplicate Policy
print("\n[Test 3] Duplicate Registration Policy...")
try:
    from cullinan.core.registry import SimpleRegistry
    from cullinan.core.exceptions import RegistryError

    # Test error policy
    registry = SimpleRegistry(duplicate_policy='error')
    registry.register('item1', 'value1')

    try:
        registry.register('item1', 'value2')
        print("  [FAIL] Should raise RegistryError")
        failed += 1
    except RegistryError:
        print("  [PASS] Error policy works correctly")
        passed += 1

except Exception as e:
    print(f"  [FAIL] {e}")
    failed += 1

# Test 4: Circular Dependency Detection
print("\n[Test 4] Circular Dependency Detection...")
try:
    from cullinan.core import get_injection_registry, reset_injection_registry, CircularDependencyError
    from cullinan.core.registry import SimpleRegistry

    reset_injection_registry()
    registry = get_injection_registry()

    class CircularRegistry(SimpleRegistry):
        def get(self, name: str):
            if name == 'ServiceA':
                return registry._resolve_dependency('ServiceB')
            elif name == 'ServiceB':
                return registry._resolve_dependency('ServiceA')
            return None

    circular_registry = CircularRegistry()
    registry.add_provider_registry(circular_registry)

    try:
        result = registry._resolve_dependency('ServiceA')
        print("  [FAIL] Should detect circular dependency")
        failed += 1
    except CircularDependencyError as e:
        print(f"  [PASS] Circular dependency detected: {e}")
        passed += 1

except Exception as e:
    print(f"  [FAIL] {e}")
    failed += 1

# Summary
print("\n" + "="*70)
print("Test Summary")
print("="*70)
print(f"Total: {passed + failed}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Success Rate: {passed/(passed+failed)*100:.1f}%")

if failed == 0:
    print("\n[SUCCESS] All fixes verified!")
    print("\nPhase 1 Completion:")
    print("  [OK] Fix #01: Subclass Injection Metadata MRO Lookup")
    print("  [OK] Fix #02: Registry Thread Safety (Locking)")
    print("  [OK] Fix #03: Duplicate Registration Policy")
    print("  [OK] Fix #04: Circular Dependency Detection")
    sys.exit(0)
else:
    print(f"\n[WARNING] {failed} test(s) failed")
    sys.exit(1)

