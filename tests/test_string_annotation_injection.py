# -*- coding: utf-8 -*-
"""测试字符串类型注解注入（像 SpringBoot 一样无需 import）"""

from cullinan.core import Inject, get_injection_registry, reset_injection_registry
from cullinan.service import service, Service, get_service_registry, reset_service_registry
from cullinan.controller import controller, get_api, reset_controller_registry


def test_string_annotation_injection():
    """测试字符串类型注解（无需 import Service 类）"""

    # Reset
    reset_injection_registry()
    reset_service_registry()
    reset_controller_registry()

    # Configure
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n=== 字符串注解测试（像 SpringBoot 一样无需 import）===\n")

    # 1. 先定义 Controller（使用字符串注解，此时 Service 还不存在）
    @controller(url='/api')
    class UserController:
        # 使用字符串注解，无需 import EmailService 和 UserService
        email_service: 'EmailService' = Inject()
        user_service: 'UserService' = Inject()

        @get_api(url='/test')
        def test_method(self, query_params):
            return {
                'email': self.email_service.send_email('test@example.com'),
                'user': self.user_service.get_user(1)
            }

    print("[1] Controller 已定义（使用字符串注解）")
    print(f"    email_service 注解: {UserController.__annotations__.get('email_service')}")
    print(f"    user_service 注解: {UserController.__annotations__.get('user_service')}")

    # 2. 后定义 Service（证明顺序无关）
    @service
    class EmailService(Service):
        def send_email(self, to):
            return f"Email sent to {to}"

    @service
    class UserService(Service):
        def get_user(self, user_id):
            return f"User {user_id}"

    print("\n[2] Service 已定义（在 Controller 之后）")

    # 3. 验证注入
    print("\n[3] 验证注入结果")

    # 检查类属性（可能是 property 或直接是实例）
    email_attr = getattr(UserController, 'email_service')
    user_attr = getattr(UserController, 'user_service')

    print(f"    UserController.email_service type: {type(email_attr).__name__}")
    print(f"    UserController.user_service type: {type(user_attr).__name__}")

    # 如果是 property（延迟加载），需要通过模拟实例访问
    if isinstance(email_attr, property):
        print("    使用了延迟加载（property）")

        # 创建模拟实例来触发 property
        class MockController:
            pass

        # 复制 properties
        for attr_name in ['email_service', 'user_service']:
            attr = getattr(UserController, attr_name)
            if isinstance(attr, property):
                setattr(MockController, attr_name, attr)

        mock = MockController()
        email_svc = mock.email_service
        user_svc = mock.user_service
    else:
        # 直接注入
        print("    使用了直接注入")
        email_svc = email_attr
        user_svc = user_attr

    print(f"    实际 email_service type: {type(email_svc).__name__}")
    print(f"    实际 user_service type: {type(user_svc).__name__}")

    # 验证是实际的 Service 实例
    assert isinstance(email_svc, EmailService), \
        f"email_service 应该是 EmailService 实例，但是：{type(email_svc)}"
    assert isinstance(user_svc, UserService), \
        f"user_service 应该是 UserService 实例，但是：{type(user_svc)}"

    print("    [OK] 两个 Service 都已正确注入")

    # 4. 测试功能
    print("\n[4] 测试功能")
    result_email = email_svc.send_email('user@test.com')
    result_user = user_svc.get_user(123)

    print(f"    email_service.send_email(): {result_email}")
    print(f"    user_service.get_user(): {result_user}")

    assert result_email == "Email sent to user@test.com"
    assert result_user == "User 123"
    print("    [OK] 功能正常")

    print("\n" + "="*60)
    print("SUCCESS: 字符串注解注入完全正常！")
    print("="*60)
    print("\n[INFO] 现在可以像 SpringBoot 一样使用依赖注入：")
    print("   - 无需 import Service 类")
    print("   - 无需担心循环导入")
    print("   - Controller 可以在 Service 之前定义")
    print("="*60 + "\n")

    return True


def test_mixed_annotations():
    """测试混合使用字符串和实际类型"""

    reset_injection_registry()
    reset_service_registry()
    reset_controller_registry()

    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n=== 混合注解测试 ===\n")

    # 定义 Services
    @service
    class ServiceA(Service):
        def method_a(self):
            return "A"

    @service
    class ServiceB(Service):
        def method_b(self):
            return "B"

    # 定义 Controller（混合使用）
    @controller(url='/api')
    class MixedController:
        # 字符串注解
        svc_a: 'ServiceA' = Inject()
        # 实际类型
        svc_b: ServiceB = Inject()

    # 验证
    assert isinstance(MixedController.svc_a, ServiceA)
    assert isinstance(MixedController.svc_b, ServiceB)

    print("[OK] 字符串注解和实际类型可以混合使用")

    return True


if __name__ == '__main__':
    try:
        print("\n" + "="*70)
        print("字符串类型注解注入测试（SpringBoot 风格）")
        print("="*70)

        success1 = test_string_annotation_injection()
        success2 = test_mixed_annotations()

        if success1 and success2:
            print("\n" + "="*70)
            print("🎉 所有测试通过！")
            print("="*70)
            print("\n现在您可以：")
            print("  1. 使用字符串注解：channel_service: 'ChannelService' = Inject()")
            print("  2. 无需 import Service 类")
            print("  3. 像 SpringBoot 一样自由使用依赖注入")
            print("\n示例代码：")
            print("""
    @controller(url='/api')
    class BotController:
        # 无需 import BotService 和 ChannelService
        bot_service: 'BotService' = Inject()
        channel_service: 'ChannelService' = Inject()
        
        @post_api(url='/webhook')
        def handle(self, body_params):
            # 直接使用
            binding = self.channel_service.get_binding(repo)
            """)
            print("="*70 + "\n")
            exit(0)
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

