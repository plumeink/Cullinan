# -*- coding: utf-8 -*-
"""
验证 Controller 中 Service 注入的实际类型

测试 self.some_service 是否真的是 Service 实例
"""

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from cullinan.service import service, Service
from cullinan.core import InjectByName, Inject
from cullinan.controller import controller, get_api

# 定义 Service
@service
class TestService(Service):
    def get_something(self):
        return "TestService.get_something() works!"

# 定义 Controller（使用 InjectByName）
@controller(url='/test1')
class TestController1:
    test_service = InjectByName('TestService')

    @get_api(url='/check')
    def check(self):
        return self.test_service.get_something()

# 定义 Controller（使用 Inject）
@controller(url='/test2')
class TestController2:
    test_service: 'TestService' = Inject()

    @get_api(url='/check')
    def check(self):
        return self.test_service.get_something()

# 测试
def test_injection_types():
    print("\n" + "=" * 70)
    print("测试 Controller 中的注入类型")
    print("=" * 70)

    # 1. 配置依赖注入
    from cullinan.core import get_injection_registry
    from cullinan.service import get_service_registry

    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    # 2. 初始化 Service
    service_registry.initialize_all()
    test_service_instance = service_registry.get_instance('TestService')

    print(f"\n[Service 实例]")
    print(f"  类型: {type(test_service_instance)}")
    print(f"  是 TestService: {isinstance(test_service_instance, TestService)}")
    print(f"  有 get_something 方法: {hasattr(test_service_instance, 'get_something')}")

    # 3. 测试 Controller1 (InjectByName)
    print(f"\n[Controller1 - InjectByName]")
    print(f"  类属性 TestController1.test_service:")
    print(f"    类型: {type(TestController1.test_service)}")
    print(f"    是否是 InjectByName: {type(TestController1.test_service).__name__}")

    # 创建实例
    controller1 = TestController1()
    print(f"\n  实例属性 controller1.test_service:")
    print(f"    类型: {type(controller1.test_service)}")
    print(f"    是 TestService: {isinstance(controller1.test_service, TestService)}")
    print(f"    是同一个实例: {controller1.test_service is test_service_instance}")

    # 尝试调用方法
    try:
        result = controller1.test_service.get_something()
        print(f"    [OK] 调用方法成功: {result}")
    except AttributeError as e:
        print(f"    [FAIL] 调用方法失败: {e}")
        print(f"    实际对象: {controller1.test_service}")
        print(f"    dir(对象): {[m for m in dir(controller1.test_service) if not m.startswith('_')][:10]}")

    # 4. 测试 Controller2 (Inject)
    print(f"\n[Controller2 - Inject]")
    print(f"  类属性 TestController2.test_service:")
    print(f"    类型: {type(TestController2.test_service)}")
    print(f"    是否是 Inject: {type(TestController2.test_service).__name__}")

    # 创建实例
    controller2 = TestController2()
    print(f"\n  实例属性 controller2.test_service:")
    print(f"    类型: {type(controller2.test_service)}")
    print(f"    是 TestService: {isinstance(controller2.test_service, TestService)}")
    print(f"    是同一个实例: {controller2.test_service is test_service_instance}")

    # 尝试调用方法
    try:
        result = controller2.test_service.get_something()
        print(f"    [OK] 调用方法成功: {result}")
    except AttributeError as e:
        print(f"    [FAIL] 调用方法失败: {e}")
        print(f"    实际对象: {controller2.test_service}")

    # 5. 检查 __dict__
    print(f"\n[实例 __dict__ 检查]")
    print(f"  controller1.__dict__: {controller1.__dict__}")
    print(f"  controller2.__dict__: {controller2.__dict__}")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_injection_types()

