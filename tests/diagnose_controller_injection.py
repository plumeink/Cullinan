# -*- coding: utf-8 -*-
"""
完整诊断 Controller 中 Service 注入的问题

测试场景：
1. Service 注册和初始化
2. Controller 注册（检查是否应用了 @injectable）
3. Controller 实例化时的注入
4. 实际访问 self.service 时的类型
"""

import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)

print("\n" + "=" * 80)
print("Controller Service 注入完整诊断")
print("=" * 80)

# ============================================================================
# 场景 1: 定义 Service
# ============================================================================
print("\n[场景 1] 定义 Service")

from cullinan.service import service, Service
from cullinan.core import InjectByName, Inject, get_injection_registry

@service
class TestService(Service):
    def on_init(self):
        logger.info("TestService.on_init() called")

    def get_data(self):
        return "real_service_data"

    def get_binding(self):
        return "binding_data"

print("✓ TestService 已定义并注册")

# ============================================================================
# 场景 2: 定义 Controller（模拟 @controller 装饰器）
# ============================================================================
print("\n[场景 2] 定义 Controller")

from cullinan.controller import controller

@controller(url='/test')
class TestControllerWithInjectByName:
    """使用 InjectByName 的 Controller"""
    test_service = InjectByName('TestService')

    def handle_request(self):
        logger.info(f"handle_request called")
        logger.info(f"  type(self.test_service) = {type(self.test_service)}")
        logger.info(f"  self.test_service = {self.test_service}")

        # 检查是否是 InjectByName 对象
        if type(self.test_service).__name__ == 'InjectByName':
            logger.error("  ✗ self.test_service 是 InjectByName 对象，注入失败！")
            return False

        # 尝试调用方法
        try:
            result = self.test_service.get_data()
            logger.info(f"  ✓ 调用成功: {result}")
            return True
        except AttributeError as e:
            logger.error(f"  ✗ 调用失败: {e}")
            return False

print("✓ TestController 已定义")

# ============================================================================
# 场景 3: 检查 Controller 是否被标记为 injectable
# ============================================================================
print("\n[场景 3] 检查 Controller 是否被标记为 injectable")

injection_registry = get_injection_registry()
has_injections = injection_registry.has_injections(TestControllerWithInjectByName)

print(f"  Controller 是否在 InjectionRegistry 中: {has_injections}")

if has_injections:
    injection_info = injection_registry.get_injection_info(TestControllerWithInjectByName)
    print(f"  注入信息: {injection_info}")
else:
    print("  ⚠️ Controller 未被标记为 injectable！")

# ============================================================================
# 场景 4: 初始化 Service
# ============================================================================
print("\n[场景 4] 初始化 Service")

from cullinan.service import get_service_registry

service_registry = get_service_registry()
service_registry.initialize_all()

test_service_instance = service_registry.get_instance('TestService')
print(f"✓ TestService 已初始化: {test_service_instance}")
print(f"  类型: {type(test_service_instance)}")

# ============================================================================
# 场景 5: 测试 Controller 实例化和注入
# ============================================================================
print("\n[场景 5] 测试 Controller 实例化")

# 检查类属性
print(f"  类属性 test_service: {TestControllerWithInjectByName.test_service}")
print(f"  类属性类型: {type(TestControllerWithInjectByName.test_service)}")

# 实例化 Controller
print("\n  实例化 Controller...")
controller = TestControllerWithInjectByName()

# 检查实例属性
print(f"\n  实例化后检查:")
print(f"    instance.__dict__: {controller.__dict__}")
print(f"    instance.test_service (通过属性访问): {type(controller.test_service)}")

# 直接检查 __dict__ 中的值
if 'test_service' in controller.__dict__:
    print(f"    __dict__['test_service']: {type(controller.__dict__['test_service'])}")
    print(f"    是 TestService 实例: {isinstance(controller.__dict__['test_service'], TestService)}")
else:
    print(f"    ⚠️ 'test_service' 不在 __dict__ 中")

# ============================================================================
# 场景 6: 调用 Controller 方法
# ============================================================================
print("\n[场景 6] 调用 Controller 方法")

success = controller.handle_request()

# ============================================================================
# 场景 7: 测试 Inject 方式（不使用 @controller，手动测试）
# ============================================================================
print("\n[场景 7] 测试 Inject 方式")

from cullinan.core import injectable as injectable_decorator

@injectable_decorator
class TestControllerWithInject:
    """使用 Inject 的 Controller"""
    test_service: 'TestService' = Inject()

    def handle_request(self):
        logger.info(f"handle_request called")
        logger.info(f"  type(self.test_service) = {type(self.test_service)}")

        if type(self.test_service).__name__ == 'Inject':
            logger.error("  ✗ self.test_service 是 Inject 对象，注入失败！")
            return False

        try:
            result = self.test_service.get_data()
            logger.info(f"  ✓ 调用成功: {result}")
            return True
        except AttributeError as e:
            logger.error(f"  ✗ 调用失败: {e}")
            return False

print("✓ TestControllerWithInject 已定义")

has_injections2 = injection_registry.has_injections(TestControllerWithInject)
print(f"  是否在 InjectionRegistry 中: {has_injections2}")

if has_injections2:
    injection_info2 = injection_registry.get_injection_info(TestControllerWithInject)
    print(f"  注入信息: {injection_info2}")

print("\n  实例化 Controller...")
controller2 = TestControllerWithInject()
print(f"  instance.__dict__: {controller2.__dict__}")

success2 = controller2.handle_request()

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 80)
print("诊断总结")
print("=" * 80)

if success:
    print("✓ InjectByName 方式: 成功")
else:
    print("✗ InjectByName 方式: 失败")

if success2:
    print("✓ Inject 方式: 成功")
else:
    print("✗ Inject 方式: 失败")

if not success or not success2:
    print("\n⚠️ 发现问题，需要修复！")
    sys.exit(1)
else:
    print("\n✓ 所有测试通过！")
    sys.exit(0)

