# -*- coding: utf-8 -*-
"""测试统一 DI 架构重构

验证：
1. Service 通过 @service 和 @injectable 正确注册
2. Controller 通过 @controller 和 @injectable 正确注册
3. Service 之间可以相互注入
4. Controller 可以注入 Service
5. ServiceRegistry 和 ControllerRegistry 作为 provider 正常工作
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_service_registration():
    """测试 Service 注册和注入"""
    print("\n" + "="*80)
    print("测试 1: Service 注册和注入")
    print("="*80)

    from cullinan.service import service, Service, get_service_registry
    from cullinan.core import Inject, InjectByName, get_injection_registry

    # 1. 定义服务
    @service
    class EmailService(Service):
        def send_email(self, to, subject):
            return f"Email sent to {to}: {subject}"

    @service
    class UserService(Service):
        # 使用类型注入
        email_service: EmailService = Inject()

        def create_user(self, name):
            result = self.email_service.send_email(name, "Welcome!")
            return f"User {name} created. {result}"

    # 2. 验证注册
    service_registry = get_service_registry()
    assert 'EmailService' in service_registry.list_all(), "EmailService 应该被注册"
    assert 'UserService' in service_registry.list_all(), "UserService 应该被注册"
    print("✓ Service 类已注册到 ServiceRegistry")

    # 3. 验证 provider 注册
    injection_registry = get_injection_registry()
    assert len(injection_registry._provider_registries) > 0, "应该有 provider"
    print("✓ ServiceRegistry 已注册为 InjectionRegistry 的 provider")

    # 4. 获取实例并测试注入
    user_service = service_registry.get_instance('UserService')
    assert user_service is not None, "应该能获取 UserService 实例"
    assert hasattr(user_service, 'email_service'), "应该有 email_service 属性"
    assert user_service.email_service is not None, "email_service 应该被注入"
    print("✓ UserService.email_service 已自动注入")

    # 5. 测试业务逻辑
    result = user_service.create_user("Alice")
    assert "Alice" in result, "应该包含用户名"
    assert "Email sent" in result, "应该包含邮件发送信息"
    print(f"✓ 业务逻辑正常: {result}")

    print("\n✅ 测试 1 通过: Service 注册和注入正常\n")
    return True


def test_inject_by_name():
    """测试 InjectByName（字符串注入）"""
    print("\n" + "="*80)
    print("测试 2: InjectByName 字符串注入")
    print("="*80)

    from cullinan.service import service, Service, get_service_registry
    from cullinan.core import InjectByName

    @service
    class SmsService(Service):
        def send_sms(self, phone, message):
            return f"SMS sent to {phone}: {message}"

    @service
    class NotificationService(Service):
        # 使用字符串注入（无需 import SmsService）
        sms_service = InjectByName('SmsService')

        def notify(self, phone, message):
            return self.sms_service.send_sms(phone, message)

    # 获取实例并测试
    service_registry = get_service_registry()
    notification_service = service_registry.get_instance('NotificationService')

    assert notification_service.sms_service is not None, "sms_service 应该被注入"
    result = notification_service.notify("1234567890", "Hello!")
    assert "SMS sent" in result, "应该包含 SMS 发送信息"
    print(f"✓ InjectByName 正常工作: {result}")

    print("\n✅ 测试 2 通过: InjectByName 正常\n")
    return True


def test_controller_injection():
    """测试 Controller 注入 Service"""
    print("\n" + "="*80)
    print("测试 3: Controller 注入 Service")
    print("="*80)

    from cullinan.controller import controller, get_controller_registry
    from cullinan.service import service, Service, get_service_registry
    from cullinan.core import Inject

    # 确保 Service 已注册
    @service
    class ProductService(Service):
        def get_products(self):
            return ["Product A", "Product B"]

    # 定义 Controller（简化版，不包含实际的路由装饰器）
    @controller(url='/api/products')
    class ProductController:
        # 注入 Service
        product_service: ProductService = Inject()

        def list_products(self):
            return self.product_service.get_products()

    # 验证注册
    controller_registry = get_controller_registry()
    assert 'ProductController' in controller_registry.list_all(), "ProductController 应该被注册"
    print("✓ Controller 已注册到 ControllerRegistry")

    # 创建 Controller 实例并测试注入
    controller_instance = controller_registry.get_instance('ProductController')
    assert controller_instance is not None, "应该能创建 Controller 实例"
    assert hasattr(controller_instance, 'product_service'), "应该有 product_service 属性"
    assert controller_instance.product_service is not None, "product_service 应该被注入"
    print("✓ ProductController.product_service 已自动注入")

    # 测试方法调用
    products = controller_instance.list_products()
    assert len(products) == 2, "应该有 2 个产品"
    print(f"✓ Controller 方法调用正常: {products}")

    print("\n✅ 测试 3 通过: Controller 注入 Service 正常\n")
    return True


def test_optional_dependency():
    """测试可选依赖"""
    print("\n" + "="*80)
    print("测试 4: 可选依赖")
    print("="*80)

    from cullinan.service import service, Service, get_service_registry
    from cullinan.core import Inject
    from typing import Optional

    @service
    class LogService(Service):
        # 可选依赖：CacheService 不存在也不会报错
        cache_service: Optional[Service] = Inject(name='NonExistentCache', required=False)

        def log(self, message):
            if self.cache_service:
                return f"Logged with cache: {message}"
            return f"Logged without cache: {message}"

    service_registry = get_service_registry()
    log_service = service_registry.get_instance('LogService')

    # cache_service 应该是 None（因为不存在）
    assert log_service.cache_service is None, "不存在的可选依赖应该是 None"
    result = log_service.log("Test message")
    assert "without cache" in result, "应该走无缓存的逻辑"
    print(f"✓ 可选依赖正常工作: {result}")

    print("\n✅ 测试 4 通过: 可选依赖正常\n")
    return True


def test_lifecycle():
    """测试生命周期钩子"""
    print("\n" + "="*80)
    print("测试 5: 生命周期钩子")
    print("="*80)

    from cullinan.service import service, Service, get_service_registry

    init_called = []

    @service
    class LifecycleService(Service):
        def on_init(self):
            init_called.append('on_init')
            print("  LifecycleService.on_init() 被调用")

    service_registry = get_service_registry()
    instance = service_registry.get_instance('LifecycleService')

    assert 'on_init' in init_called, "on_init 应该被调用"
    print("✓ on_init 生命周期钩子正常")

    print("\n✅ 测试 5 通过: 生命周期钩子正常\n")
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("Cullinan 统一 DI 架构重构测试")
    print("="*80)

    try:
        results = []

        # 运行测试
        results.append(("Service 注册和注入", test_service_registration()))
        results.append(("InjectByName 字符串注入", test_inject_by_name()))
        results.append(("Controller 注入 Service", test_controller_injection()))
        results.append(("可选依赖", test_optional_dependency()))
        results.append(("生命周期钩子", test_lifecycle()))

        # 汇总结果
        print("\n" + "="*80)
        print("测试结果汇总")
        print("="*80)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status}: {name}")

        print(f"\n总计: {passed}/{total} 测试通过")

        if passed == total:
            print("\n🎉 所有测试通过！统一 DI 架构重构成功！")
            return 0
        else:
            print(f"\n⚠️ 有 {total - passed} 个测试失败")
            return 1

    except Exception as e:
        logger.error(f"测试执行失败: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

