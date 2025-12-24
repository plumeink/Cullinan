# -*- coding: utf-8 -*-
"""测试基本的依赖注入功能

验证 InjectionExecutor 是否正确初始化并且可以解析依赖。
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cullinan.core import (
    get_injection_registry,
    injectable,
    Inject,
    InjectByName
)
from cullinan.core.injection_executor import (
    InjectionExecutor,
    set_injection_executor,
    has_injection_executor,
    get_injection_executor
)
from cullinan.service import service, get_service_registry


@service
class TestService:
    """测试服务"""
    def __init__(self):
        self.name = "TestService"

    def get_data(self):
        return "test data"


@injectable
class TestController:
    """测试控制器"""
    # 使用 Inject
    test_service: TestService = Inject()

    # 使用 InjectByName
    another_service = InjectByName('TestService', required=False)

    def get_test_data(self):
        if self.test_service:
            return self.test_service.get_data()
        return None


def test_injection_executor_initialization():
    """测试 InjectionExecutor 初始化"""
    print("\n=== Test 1: InjectionExecutor Initialization ===")

    # 获取 InjectionRegistry
    injection_registry = get_injection_registry()

    # 创建并设置 InjectionExecutor
    executor = InjectionExecutor(injection_registry)
    set_injection_executor(executor)

    # 验证
    assert has_injection_executor(), "InjectionExecutor should be initialized"
    assert get_injection_executor() is executor, "Should get the same executor"

    print("✓ InjectionExecutor initialized successfully")


def test_service_registration():
    """测试 Service 注册"""
    print("\n=== Test 2: Service Registration ===")

    service_registry = get_service_registry()

    # 初始化服务
    service_registry.initialize_all()

    # 验证服务已注册
    assert service_registry.has('TestService'), "TestService should be registered"

    # get_instance 返回实例，get 返回类
    test_service = service_registry.get_instance('TestService')
    assert test_service is not None, "Should get TestService instance"
    assert test_service.name == "TestService", "Service should have correct name"

    print(f"✓ TestService registered: {test_service}")


def test_controller_injection():
    """测试 Controller 依赖注入"""
    print("\n=== Test 3: Controller Dependency Injection ===")

    try:
        # 实例化 Controller
        controller = TestController()

        # 验证依赖注入
        assert controller.test_service is not None, "test_service should be injected"
        assert controller.test_service.name == "TestService", "Should inject correct service"

        # 验证方法调用
        data = controller.get_test_data()
        assert data == "test data", "Should get correct data from service"

        print(f"✓ Controller injection successful")
        print(f"  - test_service: {controller.test_service}")
        print(f"  - another_service: {controller.another_service}")
        print(f"  - get_test_data(): {data}")

        return True
    except Exception as e:
        print(f"✗ Controller injection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Starting basic injection tests...")

    try:
        test_injection_executor_initialization()
        test_service_registration()
        success = test_controller_injection()

        if success:
            print("\n" + "="*50)
            print("All tests passed! ✓")
            print("="*50)
        else:
            print("\n" + "="*50)
            print("Some tests failed! ✗")
            print("="*50)
            sys.exit(1)

    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

