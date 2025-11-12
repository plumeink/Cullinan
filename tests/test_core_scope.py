# -*- coding: utf-8 -*-
"""测试修复 #06: Scope 作用域支持

测试所有 Scope 实现和与 Provider 的集成。
"""

import sys
import os
import threading
import time

project_path = r'G:\pj\Cullinan'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from cullinan.core.scope import (
    Scope, SingletonScope, TransientScope, RequestScope,
    get_singleton_scope, get_transient_scope, get_request_scope
)
from cullinan.core.provider import ScopedProvider
from cullinan.core.context import create_context


# 测试用的类
class TestService:
    _instance_count = 0

    def __init__(self, name="TestService"):
        TestService._instance_count += 1
        self.id = TestService._instance_count
        self.name = name
        self.created_at = time.time()


def test_singleton_scope():
    """测试单例作用域"""
    print("\n[Test 1] SingletonScope...")

    try:
        scope = SingletonScope()
        TestService._instance_count = 0

        # 多次获取应该返回同一个实例
        instance1 = scope.get('service', lambda: TestService())
        instance2 = scope.get('service', lambda: TestService())
        instance3 = scope.get('service', lambda: TestService())

        assert instance1 is instance2, "Should return same instance"
        assert instance2 is instance3, "Should return same instance"
        assert TestService._instance_count == 1, "Should only create one instance"
        assert scope.count() == 1, "Should have one instance"
        assert scope.has('service'), "Should have service"

        # 不同 key 应该是不同实例
        instance4 = scope.get('another', lambda: TestService('another'))
        assert instance4 is not instance1, "Different keys should have different instances"
        assert scope.count() == 2, "Should have two instances"

        # 移除实例
        assert scope.remove('service'), "Should remove successfully"
        assert not scope.has('service'), "Service should be removed"
        assert scope.count() == 1, "Should have one instance left"

        # 清空
        scope.clear()
        assert scope.count() == 0, "Should be empty"

        print("  [PASS] SingletonScope works correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transient_scope():
    """测试瞬时作用域"""
    print("\n[Test 2] TransientScope...")

    try:
        scope = TransientScope()
        TestService._instance_count = 0

        # 每次获取应该返回新实例
        instance1 = scope.get('service', lambda: TestService())
        instance2 = scope.get('service', lambda: TestService())
        instance3 = scope.get('service', lambda: TestService())

        assert instance1 is not instance2, "Should return different instances"
        assert instance2 is not instance3, "Should return different instances"
        assert TestService._instance_count == 3, "Should create three instances"

        # 瞬时作用域不缓存
        assert not scope.remove('service'), "Transient scope doesn't cache"

        print("  [PASS] TransientScope works correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_request_scope():
    """测试请求作用域"""
    print("\n[Test 3] RequestScope...")

    try:
        scope = RequestScope()
        TestService._instance_count = 0

        # 在第一个请求上下文中
        with create_context():
            instance1 = scope.get('handler', lambda: TestService('req1'))
            instance2 = scope.get('handler', lambda: TestService('req1'))

            assert instance1 is instance2, "Same request should return same instance"
            assert TestService._instance_count == 1, "Should only create one instance in request"
            assert scope.count() == 1, "Should have one instance in context"
            assert scope.has('handler'), "Should have handler"

        # 在第二个请求上下文中（新请求）
        with create_context():
            instance3 = scope.get('handler', lambda: TestService('req2'))

            assert instance3 is not instance1, "Different requests should have different instances"
            assert TestService._instance_count == 2, "Should create second instance"
            assert scope.count() == 1, "New request should have one instance"

            # 测试移除
            assert scope.remove('handler'), "Should remove successfully"
            assert not scope.has('handler'), "Handler should be removed"

            # 再次获取会创建新实例
            instance4 = scope.get('handler', lambda: TestService('req2-new'))
            assert instance4 is not instance3, "Should create new instance after removal"

        print("  [PASS] RequestScope works correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_request_scope_no_context():
    """测试请求作用域在无上下文时的错误处理"""
    print("\n[Test 4] RequestScope without context...")

    try:
        scope = RequestScope()

        # 没有上下文应该抛出异常
        try:
            instance = scope.get('handler', lambda: TestService())
            print("  [FAIL] Should raise RuntimeError")
            return False
        except RuntimeError as e:
            if "No active request context" in str(e):
                print(f"  [PASS] Correctly raised error: {e}")
                return True
            else:
                print(f"  [FAIL] Wrong error message: {e}")
                return False
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        return False


def test_scoped_provider_singleton():
    """测试带单例作用域的 Provider"""
    print("\n[Test 5] ScopedProvider with SingletonScope...")

    try:
        scope = SingletonScope()
        provider = ScopedProvider(lambda: TestService('scoped'), scope, 'test_service')

        TestService._instance_count = 0

        instance1 = provider.get()
        instance2 = provider.get()

        assert instance1 is instance2, "Should return same instance"
        assert TestService._instance_count == 1, "Should only create once"
        assert provider.is_singleton(), "Should be singleton"

        print("  [PASS] ScopedProvider with SingletonScope works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scoped_provider_transient():
    """测试带瞬时作用域的 Provider"""
    print("\n[Test 6] ScopedProvider with TransientScope...")

    try:
        scope = TransientScope()
        provider = ScopedProvider(lambda: TestService('transient'), scope, 'test_service')

        TestService._instance_count = 0

        instance1 = provider.get()
        instance2 = provider.get()

        assert instance1 is not instance2, "Should return different instances"
        assert TestService._instance_count == 2, "Should create twice"
        assert not provider.is_singleton(), "Should not be singleton"

        print("  [PASS] ScopedProvider with TransientScope works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_scoped_provider_request():
    """测试带请求作用域的 Provider"""
    print("\n[Test 7] ScopedProvider with RequestScope...")

    try:
        scope = RequestScope()
        provider = ScopedProvider(lambda: TestService('request'), scope, 'test_service')

        TestService._instance_count = 0

        # 第一个请求
        with create_context():
            instance1 = provider.get()
            instance2 = provider.get()
            assert instance1 is instance2, "Same request should return same instance"

        # 第二个请求
        with create_context():
            instance3 = provider.get()
            assert instance3 is not instance1, "Different request should return different instance"

        assert TestService._instance_count == 2, "Should create two instances (one per request)"

        print("  [PASS] ScopedProvider with RequestScope works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_singleton_scope_thread_safety():
    """测试单例作用域的线程安全性"""
    print("\n[Test 8] SingletonScope thread safety...")

    try:
        scope = SingletonScope()
        TestService._instance_count = 0

        instances = []
        errors = []

        def get_instance():
            try:
                inst = scope.get('service', lambda: TestService())
                instances.append(inst)
            except Exception as e:
                errors.append(str(e))

        # 10个线程同时获取
        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Should have no errors, got {errors}"
        assert len(instances) == 10, "Should have 10 instances"

        # 所有实例应该是同一个
        first = instances[0]
        assert all(inst is first for inst in instances), "All instances should be the same"
        assert TestService._instance_count == 1, "Should only create one instance"

        print("  [PASS] SingletonScope is thread-safe")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_global_scope_instances():
    """测试全局作用域实例"""
    print("\n[Test 9] Global scope instances...")

    try:
        singleton1 = get_singleton_scope()
        singleton2 = get_singleton_scope()
        assert singleton1 is singleton2, "Should return same singleton instance"

        transient1 = get_transient_scope()
        transient2 = get_transient_scope()
        assert transient1 is transient2, "Should return same transient instance"

        request1 = get_request_scope()
        request2 = get_request_scope()
        assert request1 is request2, "Should return same request instance"

        print("  [PASS] Global scope instances work correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_scoped_provider_error_handling():
    """测试 ScopedProvider 错误处理"""
    print("\n[Test 10] ScopedProvider error handling...")

    try:
        scope = SingletonScope()

        # 测试非可调用工厂
        try:
            provider = ScopedProvider("not callable", scope, 'test')
            print("  [FAIL] Should raise TypeError for non-callable factory")
            return False
        except TypeError:
            pass  # 预期行为

        # 测试 None scope
        try:
            provider = ScopedProvider(lambda: TestService(), None, 'test')
            print("  [FAIL] Should raise ValueError for None scope")
            return False
        except ValueError:
            pass  # 预期行为

        # 测试空 key
        try:
            provider = ScopedProvider(lambda: TestService(), scope, '')
            print("  [FAIL] Should raise ValueError for empty key")
            return False
        except ValueError:
            pass  # 预期行为

        print("  [PASS] ScopedProvider error handling works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


if __name__ == '__main__':
    print("="*70)
    print("Test Fix #06: Scope Support")
    print("="*70)

    results = []
    results.append(test_singleton_scope())
    results.append(test_transient_scope())
    results.append(test_request_scope())
    results.append(test_request_scope_no_context())
    results.append(test_scoped_provider_singleton())
    results.append(test_scoped_provider_transient())
    results.append(test_scoped_provider_request())
    results.append(test_singleton_scope_thread_safety())
    results.append(test_global_scope_instances())
    results.append(test_scoped_provider_error_handling())

    print("\n" + "="*70)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*70)

    if all(results):
        print("\n[SUCCESS] All tests passed! Fix #06 verified.")
        sys.exit(0)
    else:
        print(f"\n[WARNING] {len(results) - sum(results)} test(s) failed")
        sys.exit(1)

