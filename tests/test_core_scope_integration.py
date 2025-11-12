# -*- coding: utf-8 -*-
"""Scope 与其他系统的集成测试"""

import sys
import os

project_path = r'G:\pj\Cullinan'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from cullinan.core import (
    SingletonScope, TransientScope, RequestScope,
    ScopedProvider, ProviderRegistry,
    inject_constructor, injectable, Inject,
    get_injection_registry, reset_injection_registry,
    create_context
)


class Database:
    _instance_count = 0

    def __init__(self):
        Database._instance_count += 1
        self.id = Database._instance_count
        self.connected = True


class UserService:
    def __init__(self, db: Database = None):
        self.db = db
        self.name = "UserService"


class RequestHandler:
    def __init__(self):
        self.id = id(self)


def test_scope_with_provider_registry():
    """测试 Scope 与 ProviderRegistry 集成"""
    print("\n[Test 1] Scope with ProviderRegistry...")

    try:
        registry = ProviderRegistry()

        # 注册不同作用域的 provider
        singleton_scope = SingletonScope()
        transient_scope = TransientScope()

        # 单例数据库
        registry.register_provider(
            'Database',
            ScopedProvider(lambda: Database(), singleton_scope, 'Database')
        )

        # 瞬时服务
        registry.register_provider(
            'UserService',
            ScopedProvider(lambda: UserService(), transient_scope, 'UserService')
        )

        # 获取实例
        db1 = registry.get_instance('Database')
        db2 = registry.get_instance('Database')
        assert db1 is db2, "Database should be singleton"

        svc1 = registry.get_instance('UserService')
        svc2 = registry.get_instance('UserService')
        assert svc1 is not svc2, "UserService should be transient"

        print("  [PASS] Scope with ProviderRegistry integration works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scope_with_injection_registry():
    """测试 Scope 与 InjectionRegistry 集成"""
    print("\n[Test 2] Scope with InjectionRegistry...")

    try:
        reset_injection_registry()
        injection_registry = get_injection_registry()

        # 创建 provider registry
        provider_registry = ProviderRegistry()
        singleton_scope = SingletonScope()

        Database._instance_count = 0

        # 注册单例数据库
        provider_registry.register_provider(
            'Database',
            ScopedProvider(lambda: Database(), singleton_scope, 'Database')
        )

        injection_registry.add_provider_registry(provider_registry)

        # 使用属性注入
        @injectable
        class Service1:
            database: Database = Inject()

        @injectable
        class Service2:
            database: Database = Inject()

        svc1 = Service1()
        svc2 = Service2()

        # 两个服务应该共享同一个数据库实例
        assert svc1.database is svc2.database, "Should share same Database instance"
        assert Database._instance_count == 1, "Should only create one Database"

        print("  [PASS] Scope with InjectionRegistry integration works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scope_with_constructor_injection():
    """测试 Scope 与构造器注入集成"""
    print("\n[Test 3] Scope with constructor injection...")

    try:
        reset_injection_registry()
        injection_registry = get_injection_registry()

        provider_registry = ProviderRegistry()
        singleton_scope = SingletonScope()

        Database._instance_count = 0

        # 注册数据库
        provider_registry.register_provider(
            'Database',
            ScopedProvider(lambda: Database(), singleton_scope, 'Database')
        )

        injection_registry.add_provider_registry(provider_registry)

        # 使用构造器注入
        @inject_constructor
        class UserController:
            def __init__(self, database: Database):
                self.database = database

        controller1 = UserController()
        controller2 = UserController()

        # 两个控制器应该共享同一个数据库
        assert controller1.database is controller2.database, "Should share Database"
        assert Database._instance_count == 1, "Should only create one Database"

        print("  [PASS] Scope with constructor injection works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_request_scope_with_context():
    """测试请求作用域与 RequestContext 集成"""
    print("\n[Test 4] RequestScope with RequestContext...")

    try:
        reset_injection_registry()
        injection_registry = get_injection_registry()

        provider_registry = ProviderRegistry()
        request_scope = RequestScope()

        # 注册请求范围的 handler
        provider_registry.register_provider(
            'RequestHandler',
            ScopedProvider(lambda: RequestHandler(), request_scope, 'RequestHandler')
        )

        injection_registry.add_provider_registry(provider_registry)

        # 第一个请求
        with create_context():
            @injectable
            class Controller1:
                handler: RequestHandler = Inject()

            ctrl1a = Controller1()
            ctrl1b = Controller1()

            # 同一请求内应该共享
            assert ctrl1a.handler is ctrl1b.handler, "Same request should share handler"
            handler1_id = ctrl1a.handler.id

        # 第二个请求
        with create_context():
            @injectable
            class Controller2:
                handler: RequestHandler = Inject()

            ctrl2 = Controller2()

            # 不同请求应该有不同的 handler
            assert ctrl2.handler.id != handler1_id, "Different request should have different handler"

        print("  [PASS] RequestScope with RequestContext integration works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mixed_scopes():
    """测试混合使用多种作用域"""
    print("\n[Test 5] Mixed scopes...")

    try:
        reset_injection_registry()
        injection_registry = get_injection_registry()

        provider_registry = ProviderRegistry()

        Database._instance_count = 0

        # 单例数据库
        provider_registry.register_provider(
            'Database',
            ScopedProvider(lambda: Database(), SingletonScope(), 'Database')
        )

        # 瞬时服务
        provider_registry.register_provider(
            'UserService',
            ScopedProvider(lambda: UserService(), TransientScope(), 'UserService')
        )

        injection_registry.add_provider_registry(provider_registry)

        # 使用混合注入
        @inject_constructor
        @injectable
        class AppController:
            def __init__(self, database: Database):
                self.database = database

            user_service: UserService = Inject()

        ctrl1 = AppController()
        ctrl2 = AppController()

        # 数据库应该共享（单例）
        assert ctrl1.database is ctrl2.database, "Database should be shared"
        assert Database._instance_count == 1, "Only one Database"

        # 服务应该不同（瞬时）
        assert ctrl1.user_service is not ctrl2.user_service, "UserService should be different"

        print("  [PASS] Mixed scopes work correctly")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("="*70)
    print("Scope Integration Tests")
    print("="*70)

    results = []
    results.append(test_scope_with_provider_registry())
    results.append(test_scope_with_injection_registry())
    results.append(test_scope_with_constructor_injection())
    results.append(test_request_scope_with_context())
    results.append(test_mixed_scopes())

    print("\n" + "="*70)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*70)

    if all(results):
        print("\n[SUCCESS] All integration tests passed!")
        sys.exit(0)
    else:
        print(f"\n[WARNING] {len(results) - sum(results)} test(s) failed")
        sys.exit(1)

