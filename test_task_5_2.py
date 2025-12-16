#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for Task-5.2: Startup Error Policy + on_shutdown Hook"""

import sys
sys.path.insert(0, 'G:/pj/Cullinan - 副本 (3)')

from cullinan import configure
from cullinan.service import service, Service, get_service_registry, reset_service_registry
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

def test_startup_error_policy_strict():
    """测试 strict 策略：Service 失败时立即退出"""
    print("\n" + "="*60)
    print("Test 1: Startup Error Policy - STRICT")
    print("="*60)

    reset_service_registry()
    configure(startup_error_policy='strict')

    # 定义一个会失败的 Service
    @service
    class FailingService(Service):
        def on_init(self):
            raise RuntimeError("Simulated initialization failure")

    @service
    class HealthyService(Service):
        def on_init(self):
            print("  HealthyService initialized")

    registry = get_service_registry()

    try:
        registry.initialize_all()
        print("  ❌ Should have raised exception!")
        return False
    except Exception as e:
        # Strict 策略应该抛出异常（可能是 RuntimeError 或 DependencyResolutionError）
        print(f"  ✓ Caught expected exception: {type(e).__name__}")
        print("  ✓ STRICT policy works: application exits on first failure")
        return True

def test_startup_error_policy_warn():
    """测试 warn 策略：Service 失败时记录警告但继续"""
    print("\n" + "="*60)
    print("Test 2: Startup Error Policy - WARN")
    print("="*60)

    reset_service_registry()
    configure(startup_error_policy='warn')

    # 定义多个 Service，其中一个会失败
    @service
    class FailingService(Service):
        def on_init(self):
            raise RuntimeError("Simulated initialization failure")

    @service
    class HealthyService1(Service):
        def on_init(self):
            print("  HealthyService1 initialized")

    @service
    class HealthyService2(Service):
        def on_init(self):
            print("  HealthyService2 initialized")

    registry = get_service_registry()

    try:
        registry.initialize_all()

        # 验证健康的 Service 已初始化
        healthy1 = registry.get_instance('HealthyService1')
        healthy2 = registry.get_instance('HealthyService2')

        if healthy1 and healthy2:
            print("  ✓ Healthy services initialized despite failure")
            print("  ✓ WARN policy works: application continues in degraded mode")
            return True
        else:
            print("  ❌ Healthy services not initialized")
            return False
    except Exception as e:
        print(f"  ❌ Unexpected exception: {e}")
        return False

def test_startup_error_policy_ignore():
    """测试 ignore 策略：完全忽略失败"""
    print("\n" + "="*60)
    print("Test 3: Startup Error Policy - IGNORE")
    print("="*60)

    reset_service_registry()
    configure(startup_error_policy='ignore')

    @service
    class FailingService(Service):
        def on_init(self):
            raise RuntimeError("Simulated initialization failure")

    @service
    class HealthyService(Service):
        def on_init(self):
            print("  HealthyService initialized")

    registry = get_service_registry()

    try:
        registry.initialize_all()

        healthy = registry.get_instance('HealthyService')
        if healthy:
            print("  ✓ Healthy service initialized")
            print("  ✓ IGNORE policy works: failures are silently ignored")
            return True
        else:
            print("  ❌ Healthy service not initialized")
            return False
    except Exception as e:
        print(f"  ❌ Unexpected exception: {e}")
        return False

def test_on_shutdown_hook():
    """测试 on_shutdown() 钩子"""
    print("\n" + "="*60)
    print("Test 4: on_shutdown() Hook")
    print("="*60)

    reset_service_registry()
    configure(startup_error_policy='strict')

    shutdown_called = []

    @service
    class DatabaseService(Service):
        def on_init(self):
            print("  DatabaseService: connecting...")
            self.connected = True

        def on_shutdown(self):
            print("  DatabaseService: disconnecting...")
            self.connected = False
            shutdown_called.append('DatabaseService')

    @service
    class CacheService(Service):
        def on_init(self):
            print("  CacheService: starting...")
            self.running = True

        def on_shutdown(self):
            print("  CacheService: stopping...")
            self.running = False
            shutdown_called.append('CacheService')

    registry = get_service_registry()

    try:
        # 初始化
        registry.initialize_all()

        # 验证服务已启动
        db = registry.get_instance('DatabaseService')
        cache = registry.get_instance('CacheService')

        if not (db and cache and db.connected and cache.running):
            print("  ❌ Services not properly initialized")
            return False

        print("  ✓ Services initialized")

        # 调用 destroy_all 触发 on_shutdown
        registry.destroy_all()

        # 验证 on_shutdown 被调用
        if 'DatabaseService' in shutdown_called and 'CacheService' in shutdown_called:
            print("  ✓ on_shutdown() hooks called")

            # 验证状态已清理
            if not db.connected and not cache.running:
                print("  ✓ Resources properly cleaned up")
                return True
            else:
                print("  ❌ Resources not properly cleaned up")
                return False
        else:
            print(f"  ❌ on_shutdown() not called. Called: {shutdown_called}")
            return False

    except Exception as e:
        print(f"  ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_on_startup_failure_with_warn():
    """测试 on_startup() 失败时的 warn 策略"""
    print("\n" + "="*60)
    print("Test 5: on_startup() Failure with WARN Policy")
    print("="*60)

    reset_service_registry()
    configure(startup_error_policy='warn')

    @service
    class ServiceWithFailingStartup(Service):
        def on_init(self):
            print("  ServiceWithFailingStartup: initialized")

        def on_startup(self):
            raise RuntimeError("Startup task failed")

    @service
    class HealthyService(Service):
        def on_init(self):
            print("  HealthyService: initialized")

        def on_startup(self):
            print("  HealthyService: startup task completed")

    registry = get_service_registry()

    try:
        registry.initialize_all()

        # 验证健康的 Service 正常启动
        healthy = registry.get_instance('HealthyService')
        if healthy:
            print("  ✓ Healthy service completed startup despite other failure")
            print("  ✓ WARN policy handles on_startup() failures")
            return True
        else:
            print("  ❌ Healthy service not available")
            return False

    except Exception as e:
        print(f"  ❌ Unexpected exception: {e}")
        return False

def test_invalid_policy():
    """测试无效的策略值"""
    print("\n" + "="*60)
    print("Test 6: Invalid Policy Validation")
    print("="*60)

    try:
        configure(startup_error_policy='invalid_policy')
        print("  ❌ Should have raised ValueError!")
        return False
    except ValueError as e:
        print(f"  ✓ Caught expected ValueError: {e}")
        print("  ✓ Policy validation works")
        return True

def main():
    print("=" * 60)
    print("Task-5.2: Startup Error Policy + on_shutdown Tests")
    print("=" * 60)

    results = []

    try:
        results.append(("Strict Policy", test_startup_error_policy_strict()))
        results.append(("Warn Policy", test_startup_error_policy_warn()))
        results.append(("Ignore Policy", test_startup_error_policy_ignore()))
        results.append(("on_shutdown Hook", test_on_shutdown_hook()))
        results.append(("on_startup Failure", test_on_startup_failure_with_warn()))
        results.append(("Invalid Policy", test_invalid_policy()))

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        all_passed = True
        for name, passed in results:
            status = "✓ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {name}")
            if not passed:
                all_passed = False

        print("="*60)

        if all_passed:
            print("🎉 ALL TESTS PASSED!")
            print("\nSummary:")
            print("  • Strict policy: exits on first failure ✓")
            print("  • Warn policy: continues with degraded mode ✓")
            print("  • Ignore policy: silently ignores failures ✓")
            print("  • on_shutdown() hook: properly called ✓")
            print("  • on_startup() failures: handled by policy ✓")
            print("  • Policy validation: invalid values rejected ✓")
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            return 1

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

