# -*- coding: utf-8 -*-
"""测试修复 #05: Provider/Binding API 抽象

测试 Provider 系统的所有功能。
"""

import sys
import os
import threading
import time

project_path = r'G:\pj\Cullinan'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from cullinan.core.provider import (
    Provider, InstanceProvider, ClassProvider,
    FactoryProvider, ProviderRegistry
)


# 测试用的类
class TestService:
    def __init__(self, name="TestService"):
        self.name = name
        self.created_at = time.time()


class Counter:
    _instance_count = 0

    def __init__(self):
        Counter._instance_count += 1
        self.id = Counter._instance_count


def test_instance_provider():
    """测试实例提供者"""
    print("\n[Test 1] InstanceProvider...")

    try:
        service = TestService("test1")
        provider = InstanceProvider(service)

        # 应该返回同一个实例
        result1 = provider.get()
        result2 = provider.get()

        assert result1 is service, "Should return the same instance"
        assert result2 is service, "Should return the same instance"
        assert provider.is_singleton(), "InstanceProvider is always singleton"

        print("  [PASS] InstanceProvider works correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_class_provider_singleton():
    """测试类提供者（单例模式）"""
    print("\n[Test 2] ClassProvider (singleton)...")

    try:
        Counter._instance_count = 0
        provider = ClassProvider(Counter, singleton=True)

        # 应该返回同一个实例
        instance1 = provider.get()
        instance2 = provider.get()

        assert instance1 is instance2, "Should return same instance in singleton mode"
        assert Counter._instance_count == 1, "Should only create one instance"
        assert provider.is_singleton(), "Should be singleton"

        print("  [PASS] ClassProvider singleton mode works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_class_provider_transient():
    """测试类提供者（瞬时模式）"""
    print("\n[Test 3] ClassProvider (transient)...")

    try:
        Counter._instance_count = 0
        provider = ClassProvider(Counter, singleton=False)

        # 应该返回不同的实例
        instance1 = provider.get()
        instance2 = provider.get()

        assert instance1 is not instance2, "Should return different instances in transient mode"
        assert Counter._instance_count == 2, "Should create two instances"
        assert not provider.is_singleton(), "Should not be singleton"

        print("  [PASS] ClassProvider transient mode works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_factory_provider_singleton():
    """测试工厂提供者（单例模式）"""
    print("\n[Test 4] FactoryProvider (singleton)...")

    try:
        call_count = [0]

        def factory():
            call_count[0] += 1
            return TestService(f"factory_{call_count[0]}")

        provider = FactoryProvider(factory, singleton=True)

        # 应该返回同一个实例
        instance1 = provider.get()
        instance2 = provider.get()

        assert instance1 is instance2, "Should return same instance in singleton mode"
        assert call_count[0] == 1, "Factory should be called only once"
        assert provider.is_singleton(), "Should be singleton"

        print("  [PASS] FactoryProvider singleton mode works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_factory_provider_transient():
    """测试工厂提供者（瞬时模式）"""
    print("\n[Test 5] FactoryProvider (transient)...")

    try:
        call_count = [0]

        def factory():
            call_count[0] += 1
            return TestService(f"factory_{call_count[0]}")

        provider = FactoryProvider(factory, singleton=False)

        # 应该返回不同的实例
        instance1 = provider.get()
        instance2 = provider.get()

        assert instance1 is not instance2, "Should return different instances"
        assert call_count[0] == 2, "Factory should be called twice"
        assert not provider.is_singleton(), "Should not be singleton"

        print("  [PASS] FactoryProvider transient mode works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_provider_registry():
    """测试 Provider 注册表"""
    print("\n[Test 6] ProviderRegistry...")

    try:
        registry = ProviderRegistry()

        # 注册实例
        service = TestService("test")
        registry.register_instance('service', service)

        # 注册类
        registry.register_class('counter', Counter, singleton=True)

        # 注册工厂
        registry.register_factory('factory', lambda: TestService("from_factory"), singleton=False)

        # 验证注册
        assert registry.count() == 3, "Should have 3 providers"
        assert registry.has_provider('service'), "Should have service"
        assert registry.has_provider('counter'), "Should have counter"
        assert registry.has_provider('factory'), "Should have factory"

        # 获取实例
        s1 = registry.get_instance('service')
        assert s1 is service, "Should return registered instance"

        c1 = registry.get_instance('counter')
        c2 = registry.get_instance('counter')
        assert c1 is c2, "Counter should be singleton"

        f1 = registry.get_instance('factory')
        f2 = registry.get_instance('factory')
        assert f1 is not f2, "Factory should be transient"

        # 列出名称
        names = registry.list_names()
        assert len(names) == 3, "Should list 3 names"
        assert 'service' in names, "Should include service"

        # 取消注册
        assert registry.unregister('service'), "Should unregister successfully"
        assert not registry.has_provider('service'), "Service should be removed"
        assert registry.count() == 2, "Should have 2 providers left"

        # 清空
        registry.clear()
        assert registry.count() == 0, "Should be empty after clear"

        print("  [PASS] ProviderRegistry works correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_thread_safety():
    """测试 Provider 的线程安全性"""
    print("\n[Test 7] Provider thread safety...")

    try:
        Counter._instance_count = 0
        provider = ClassProvider(Counter, singleton=True)

        instances = []
        errors = []

        def get_instance():
            try:
                inst = provider.get()
                instances.append(inst)
            except Exception as e:
                errors.append(str(e))

        # 创建多个线程同时获取实例
        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证
        assert len(errors) == 0, f"Should have no errors, got {errors}"
        assert len(instances) == 10, "Should have 10 instances"

        # 所有实例应该是同一个（单例）
        first = instances[0]
        assert all(inst is first for inst in instances), "All instances should be the same"
        assert Counter._instance_count == 1, "Should only create one instance"

        print("  [PASS] Provider is thread-safe")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_registry_thread_safety():
    """测试 ProviderRegistry 的线程安全性"""
    print("\n[Test 8] ProviderRegistry thread safety...")

    try:
        registry = ProviderRegistry()
        errors = []

        def register_providers(thread_id):
            try:
                for i in range(20):
                    name = f"service_{thread_id}_{i}"
                    registry.register_instance(name, TestService(name))
            except Exception as e:
                errors.append(str(e))

        # 多线程并发注册
        threads = [threading.Thread(target=register_providers, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证
        assert len(errors) == 0, f"Should have no errors, got {errors}"
        expected_count = 5 * 20
        actual_count = registry.count()
        assert actual_count == expected_count, f"Expected {expected_count}, got {actual_count}"

        print("  [PASS] ProviderRegistry is thread-safe")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n[Test 9] Error handling...")

    try:
        # 测试 None 实例
        try:
            provider = InstanceProvider(None)
            print("  [FAIL] Should raise ValueError for None instance")
            return False
        except ValueError:
            pass  # 预期行为

        # 测试非类型对象
        try:
            provider = ClassProvider("not a class")
            print("  [FAIL] Should raise TypeError for non-type")
            return False
        except TypeError:
            pass  # 预期行为

        # 测试非可调用对象
        try:
            provider = FactoryProvider("not callable")
            print("  [FAIL] Should raise TypeError for non-callable")
            return False
        except TypeError:
            pass  # 预期行为

        print("  [PASS] Error handling works correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


if __name__ == '__main__':
    print("="*70)
    print("Test Fix #05: Provider/Binding API")
    print("="*70)

    results = []
    results.append(test_instance_provider())
    results.append(test_class_provider_singleton())
    results.append(test_class_provider_transient())
    results.append(test_factory_provider_singleton())
    results.append(test_factory_provider_transient())
    results.append(test_provider_registry())
    results.append(test_provider_thread_safety())
    results.append(test_registry_thread_safety())
    results.append(test_error_handling())

    print("\n" + "="*70)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*70)

    if all(results):
        print("\n[SUCCESS] All tests passed! Fix #05 verified.")
        sys.exit(0)
    else:
        print(f"\n[WARNING] {len(results) - sum(results)} test(s) failed")
        sys.exit(1)

