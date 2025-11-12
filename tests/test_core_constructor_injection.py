# -*- coding: utf-8 -*-
"""测试修复 #07: 构造器注入支持

测试 inject_constructor 装饰器的所有功能。
"""

import sys
import os

project_path = r'G:\pj\Cullinan'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from cullinan.core import (
    inject_constructor, injectable, Inject,
    get_injection_registry, reset_injection_registry
)
from cullinan.core.registry import SimpleRegistry
from cullinan.core.exceptions import RegistryError


# 测试用的类
class TestService:
    def __init__(self, name="TestService"):
        self.name = name


class Config:
    def __init__(self):
        self.value = "config_value"


class Database:
    def __init__(self):
        self.connected = True


def test_basic_constructor_injection():
    """测试基本构造器注入"""
    print("\n[Test 1] Basic constructor injection...")

    try:
        reset_injection_registry()
        registry = get_injection_registry()

        # 注册依赖
        service_registry = SimpleRegistry()
        service_registry.register('TestService', TestService())
        service_registry.register('Config', Config())
        registry.add_provider_registry(service_registry)

        # 定义使用构造器注入的类
        @inject_constructor
        class Controller:
            def __init__(self, test_service: TestService, config: Config):
                self.test_service = test_service
                self.config = config

        # 创建实例（不传参数，应该自动注入）
        instance = Controller()

        assert hasattr(instance, 'test_service'), "Should have test_service"
        assert hasattr(instance, 'config'), "Should have config"
        assert isinstance(instance.test_service, TestService), "test_service should be TestService instance"
        assert isinstance(instance.config, Config), "config should be Config instance"

        print("  [PASS] Basic constructor injection works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mixed_injection():
    """测试混合注入（构造器 + 属性）"""
    print("\n[Test 2] Mixed injection (constructor + property)...")

    try:
        reset_injection_registry()
        registry = get_injection_registry()

        # 注册依赖
        service_registry = SimpleRegistry()
        service_registry.register('TestService', TestService())
        service_registry.register('Config', Config())
        service_registry.register('Database', Database())
        registry.add_provider_registry(service_registry)

        # 定义混合注入的类
        @inject_constructor
        @injectable
        class Controller:
            # 构造器注入
            def __init__(self, test_service: TestService):
                self.test_service = test_service

            # 属性注入
            config: Config = Inject()
            database: Database = Inject(required=False)

        # 创建实例
        instance = Controller()

        assert hasattr(instance, 'test_service'), "Should have test_service (constructor)"
        assert hasattr(instance, 'config'), "Should have config (property)"
        assert hasattr(instance, 'database'), "Should have database (property)"

        print("  [PASS] Mixed injection works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_partial_manual_injection():
    """测试部分手动传参"""
    print("\n[Test 3] Partial manual injection...")

    try:
        reset_injection_registry()
        registry = get_injection_registry()

        # 注册依赖
        service_registry = SimpleRegistry()
        service_registry.register('Config', Config())
        registry.add_provider_registry(service_registry)

        # 定义类
        @inject_constructor
        class Controller:
            def __init__(self, test_service: TestService, config: Config):
                self.test_service = test_service
                self.config = config

        # 手动传入部分参数
        manual_service = TestService("manual")
        instance = Controller(manual_service)

        assert instance.test_service.name == "manual", "Should use manual service"
        assert isinstance(instance.config, Config), "Should inject config"

        print("  [PASS] Partial manual injection works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_optional_dependency():
    """测试可选依赖"""
    print("\n[Test 4] Optional dependency...")

    try:
        reset_injection_registry()
        registry = get_injection_registry()

        # 注册部分依赖（故意不注册 Config）
        service_registry = SimpleRegistry()
        service_registry.register('TestService', TestService())
        registry.add_provider_registry(service_registry)

        # 定义类（Config 有默认值，是可选的）
        @inject_constructor
        class Controller:
            def __init__(self, test_service: TestService, config: Config = None):
                self.test_service = test_service
                self.config = config if config else Config()

        # 创建实例（Config 未注册，应该使用默认值）
        instance = Controller()

        assert hasattr(instance, 'test_service'), "Should have test_service"
        assert isinstance(instance.test_service, TestService), "test_service should be injected"
        assert isinstance(instance.config, Config), "config should use default"

        print("  [PASS] Optional dependency works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_required_dependency_missing():
    """测试必需依赖缺失（应该抛出异常）"""
    print("\n[Test 5] Required dependency missing...")

    try:
        reset_injection_registry()
        registry = get_injection_registry()

        # 不注册任何依赖
        service_registry = SimpleRegistry()
        registry.add_provider_registry(service_registry)

        # 定义类
        @inject_constructor
        class Controller:
            def __init__(self, test_service: TestService):
                self.test_service = test_service

        # 尝试创建实例（应该抛出异常）
        try:
            instance = Controller()
            print("  [FAIL] Should raise RegistryError")
            return False
        except RegistryError as e:
            if "Cannot inject required parameter" in str(e):
                print(f"  [PASS] Correctly raised error: {e}")
                return True
            else:
                print(f"  [FAIL] Wrong error message: {e}")
                return False
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_type_hints():
    """测试没有类型提示的参数（应该跳过）"""
    print("\n[Test 6] No type hints...")

    try:
        reset_injection_registry()

        # 定义没有类型提示的类
        @inject_constructor
        class Controller:
            def __init__(self, test_service):
                self.test_service = test_service

        # 必须手动传参（因为没有类型提示）
        try:
            instance = Controller(TestService())
            print("  [PASS] No type hints handled correctly")
            return True
        except:
            print("  [FAIL] Should allow manual parameters")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_immutable_object():
    """测试不可变对象（构造器注入的典型场景）"""
    print("\n[Test 7] Immutable object...")

    try:
        reset_injection_registry()
        registry = get_injection_registry()

        # 注册依赖
        service_registry = SimpleRegistry()
        service_registry.register('TestService', TestService("injected"))
        registry.add_provider_registry(service_registry)

        # 定义不可变对象（所有属性在构造时设置）
        @inject_constructor
        class ImmutableController:
            def __init__(self, test_service: TestService):
                self._service = test_service  # 私有属性，不可变

            @property
            def service(self):
                return self._service

        instance = ImmutableController()
        assert instance.service.name == "injected", "Should inject correctly"

        print("  [PASS] Immutable object works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_decorator_order():
    """测试装饰器顺序"""
    print("\n[Test 8] Decorator order...")

    try:
        reset_injection_registry()
        registry = get_injection_registry()

        # 注册依赖
        service_registry = SimpleRegistry()
        service_registry.register('TestService', TestService())
        service_registry.register('Config', Config())
        registry.add_provider_registry(service_registry)

        # inject_constructor 在外层
        @inject_constructor
        @injectable
        class Controller1:
            def __init__(self, test_service: TestService):
                self.test_service = test_service
            config: Config = Inject()

        instance1 = Controller1()
        assert hasattr(instance1, 'test_service'), "Should have test_service"
        assert hasattr(instance1, 'config'), "Should have config"

        print("  [PASS] Decorator order works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("="*70)
    print("Test Fix #07: Constructor Injection")
    print("="*70)

    results = []
    results.append(test_basic_constructor_injection())
    results.append(test_mixed_injection())
    results.append(test_partial_manual_injection())
    results.append(test_optional_dependency())
    results.append(test_required_dependency_missing())
    results.append(test_no_type_hints())
    results.append(test_immutable_object())
    results.append(test_decorator_order())

    print("\n" + "="*70)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*70)

    if all(results):
        print("\n[SUCCESS] All tests passed! Fix #07 verified.")
        sys.exit(0)
    else:
        print(f"\n[WARNING] {len(results) - sum(results)} test(s) failed")
        sys.exit(1)

