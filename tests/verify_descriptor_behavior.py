# -*- coding: utf-8 -*-
"""
验证修复：测试 InjectByName 在类和实例上的行为
"""

from cullinan.core import InjectByName
from cullinan.service import service, Service, get_service_registry

print("=" * 80)
print("验证 InjectByName 描述符行为")
print("=" * 80)

# 1. 定义 Service
@service
class TestService(Service):
    def get_data(self):
        return "real_data"

# 2. 初始化 Service
service_registry = get_service_registry()
service_registry.initialize_all()

# 3. 定义 Controller
class TestController:
    test_service = InjectByName('TestService')

print("\n[测试 1] 类属性访问")
print(f"  TestController.test_service = {TestController.test_service}")
print(f"  type = {type(TestController.test_service)}")
print(f"  是 InjectByName: {type(TestController.test_service).__name__ == 'InjectByName'}")

print("\n[测试 2] 实例属性访问")
instance = TestController()
print(f"  instance.test_service = {instance.test_service}")
print(f"  type = {type(instance.test_service)}")
print(f"  是 TestService: {type(instance.test_service).__name__ == 'TestService'}")

print("\n[测试 3] 调用方法")
try:
    result = instance.test_service.get_data()
    print(f"  [OK] 调用成功: {result}")
except AttributeError as e:
    print(f"  [FAIL] 调用失败: {e}")

print("\n[关键结论]")
print("  • 类属性访问返回 InjectByName 对象（描述符本身）")
print("  • 实例属性访问返回 TestService 实例（通过 __get__ 方法）")
print("  • 修复前：request_handler 使用类，所以是 InjectByName")
print("  • 修复后：request_handler 实例化类，所以是 TestService")
print("=" * 80)

