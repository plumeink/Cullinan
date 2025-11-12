# -*- coding: utf-8 -*-
"""
测试 Controller 实例化修复

验证：
1. Controller 类被实例化
2. self.service 是真正的 Service 实例
3. 可以调用 self.service.get_method()
"""

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from cullinan.service import service, Service, get_service_registry
from cullinan.controller import controller, post_api
from cullinan.core import InjectByName, get_injection_registry

print("\n" + "=" * 80)
print("测试 Controller 实例化修复")
print("=" * 80)

# 1. 定义 Service
@service
class ChannelService(Service):
    def on_init(self):
        print("  → ChannelService initialized")

    def get_binding(self, repo_name):
        """模拟 get_binding 方法"""
        return f"binding_for_{repo_name}"

# 2. 定义 Controller
@controller(url='/api')
class TestController:
    channel_service = InjectByName('ChannelService')

    @post_api(url='/test')
    def handle_request(self):
        print(f"\n在 handle_request 中:")
        print(f"  type(self) = {type(self)}")
        print(f"  type(self.channel_service) = {type(self.channel_service)}")
        print(f"  self.channel_service = {self.channel_service}")

        # 检查是否是实例
        if type(self).__name__ == 'TestController':
            print(f"  [OK] self 是 TestController 实例")
        else:
            print(f"  [FAIL] self 不是实例，是类: {type(self)}")

        # 检查 service 是否正确注入
        if type(self.channel_service).__name__ == 'ChannelService':
            print(f"  [OK] self.channel_service 是 ChannelService 实例")
        else:
            print(f"  [FAIL] self.channel_service 不是实例: {type(self.channel_service)}")
            return False

        # 尝试调用方法
        try:
            result = self.channel_service.get_binding('test/repo')
            print(f"  [OK] 调用 get_binding 成功: {result}")
            return True
        except AttributeError as e:
            print(f"  [FAIL] 调用 get_binding 失败: {e}")
            return False

print("\n[步骤 1] Service 和 Controller 已定义")

# 3. 初始化 Service
print("\n[步骤 2] 初始化 Service")
injection_registry = get_injection_registry()
service_registry = get_service_registry()

service_registry.initialize_all()
print("  [OK] Service 已初始化")

# 4. 模拟请求处理 - 直接实例化 Controller 测试
print("\n[步骤 3] 测试直接实例化 Controller")

controller_instance = TestController()
print(f"  Controller 实例: {controller_instance}")
print(f"  type(controller_instance): {type(controller_instance)}")
print(f"  type(controller_instance.channel_service): {type(controller_instance.channel_service)}")

# 调用方法
success = controller_instance.handle_request()

print("\n" + "=" * 80)
if success:
    print("✅ 测试通过！Controller 实例化后 Service 注入正常")
else:
    print("[ERROR] 测试失败！Service 注入有问题")
print("=" * 80)

