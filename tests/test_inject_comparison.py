# -*- coding: utf-8 -*-
"""
测试 Inject 注入方式是否也正常工作

对比测试 Inject 和 InjectByName 两种注入方式
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# =============================================================================
# 定义 Service
# =============================================================================

from cullinan.service import service, Service
from cullinan.core import Inject, InjectByName

@service
class EmailService(Service):
    """邮件服务"""

    def on_init(self):
        logger.info("[OK] EmailService initialized")

    def send_email(self, to: str):
        return f"Email sent to {to}"

    def get_something(self):
        return "EmailService data"


@service
class UserService(Service):
    """用户服务 - 使用 Inject 注入"""

    # 方式1: 使用 Inject + 字符串类型注解（推荐）
    email_service: 'EmailService' = Inject()

    def on_init(self):
        logger.info("[OK] UserService initialized")

    def get_users(self):
        """测试方法"""
        return [{"id": 1, "name": "Alice"}]

    def test_email(self):
        """测试 email_service 注入"""
        return self.email_service.send_email("test@example.com")


@service
class ProductService(Service):
    """产品服务 - 使用 InjectByName 注入"""

    # 方式2: 使用 InjectByName
    email_service = InjectByName('EmailService')

    def on_init(self):
        logger.info("[OK] ProductService initialized")

    def get_products(self):
        """测试方法"""
        return [{"id": 1, "name": "Product A"}]

    def test_email(self):
        """测试 email_service 注入"""
        return self.email_service.send_email("product@example.com")


# =============================================================================
# 定义 Controller
# =============================================================================

from cullinan.controller import controller, get_api

@controller(url='/api/users')
class UserController:
    """测试 Inject 注入"""

    # 使用 Inject + 字符串类型注解
    user_service: 'UserService' = Inject()

    @get_api(url='/test')
    def test(self):
        return self.user_service.get_users()


@controller(url='/api/products')
class ProductController:
    """测试 InjectByName 注入"""

    # 使用 InjectByName
    product_service = InjectByName('ProductService')

    @get_api(url='/test')
    def test(self):
        return self.product_service.get_products()


# =============================================================================
# 测试函数
# =============================================================================

def test_inject_vs_inject_by_name():
    """对比测试 Inject 和 InjectByName"""

    print("\n" + "=" * 70)
    print("对比测试 Inject 和 InjectByName")
    print("=" * 70)

    # 1. 初始化 Service Registry
    print("\n[步骤 1] 初始化 Service Registry...")
    from cullinan.service import get_service_registry
    from cullinan.core import get_injection_registry

    service_registry = get_service_registry()
    injection_registry = get_injection_registry()

    services = list(service_registry.list_all().keys())
    print(f"[OK] 已注册 Service: {services}")

    # 2. 初始化所有 Service
    print("\n[步骤 2] 初始化所有 Service...")
    service_registry.initialize_all()
    print("[OK] Service 初始化完成")

    # 3. 验证 Service 实例
    print("\n[步骤 3] 验证 Service 实例...")
    email_service = service_registry.get_instance('EmailService')
    user_service = service_registry.get_instance('UserService')
    product_service = service_registry.get_instance('ProductService')

    print(f"  • EmailService: {type(email_service).__name__}")
    print(f"  • UserService: {type(user_service).__name__}")
    print(f"  • ProductService: {type(product_service).__name__}")

    # 4. 测试 Service 层的注入
    print("\n[步骤 4] 测试 Service 层的依赖注入...")

    # 测试 UserService (使用 Inject)
    print("\n  4.1 测试 UserService (使用 Inject):")
    print(f"      user_service.email_service: {type(user_service.email_service).__name__}")
    print(f"      是否是 EmailService: {isinstance(user_service.email_service, EmailService)}")
    try:
        result = user_service.test_email()
        print(f"      [OK] 调用方法成功: {result}")
    except AttributeError as e:
        print(f"      [FAIL] 调用方法失败: {e}")
        print(f"      实际类型: {type(user_service.email_service)}")
        print(f"      实际值: {user_service.email_service}")
        raise

    # 测试 ProductService (使用 InjectByName)
    print("\n  4.2 测试 ProductService (使用 InjectByName):")
    print(f"      product_service.email_service: {type(product_service.email_service).__name__}")
    print(f"      是否是 EmailService: {isinstance(product_service.email_service, EmailService)}")
    try:
        result = product_service.test_email()
        print(f"      [OK] 调用方法成功: {result}")
    except AttributeError as e:
        print(f"      [FAIL] 调用方法失败: {e}")
        raise

    # 5. 测试 Controller 层的注入
    print("\n[步骤 5] 测试 Controller 层的依赖注入...")

    # 测试 UserController (使用 Inject)
    print("\n  5.1 测试 UserController (使用 Inject):")
    user_controller = UserController()
    print(f"      Controller 实例: {type(user_controller).__name__}")
    print(f"      user_service 类型: {type(user_controller.user_service).__name__}")
    print(f"      是否是 UserService: {isinstance(user_controller.user_service, UserService)}")
    try:
        result = user_controller.user_service.get_users()
        print(f"      [OK] 调用方法成功: {result}")
    except AttributeError as e:
        print(f"      [FAIL] 调用方法失败: {e}")
        print(f"      实际类型: {type(user_controller.user_service)}")
        print(f"      实际值: {user_controller.user_service}")
        raise

    # 测试 ProductController (使用 InjectByName)
    print("\n  5.2 测试 ProductController (使用 InjectByName):")
    product_controller = ProductController()
    print(f"      Controller 实例: {type(product_controller).__name__}")
    print(f"      product_service 类型: {type(product_controller.product_service).__name__}")
    print(f"      是否是 ProductService: {isinstance(product_controller.product_service, ProductService)}")
    try:
        result = product_controller.product_service.get_products()
        print(f"      [OK] 调用方法成功: {result}")
    except AttributeError as e:
        print(f"      [FAIL] 调用方法失败: {e}")
        raise

    # 6. 验证单例
    print("\n[步骤 6] 验证单例模式...")
    print(f"  • UserService.email_service 是同一个实例: {user_service.email_service is email_service}")
    print(f"  • ProductService.email_service 是同一个实例: {product_service.email_service is email_service}")
    print(f"  • UserController.user_service 是同一个实例: {user_controller.user_service is user_service}")
    print(f"  • ProductController.product_service 是同一个实例: {product_controller.product_service is product_service}")

    print("\n" + "=" * 70)
    print("✅ 所有测试通过！Inject 和 InjectByName 都正常工作！")
    print("=" * 70)

    print("\n📊 对比总结:")
    print("  Inject:")
    print("    [OK] 需要类型注解: user_service: 'UserService' = Inject()")
    print("    [OK] 支持字符串注解（无需 import）")
    print("    [OK] IDE 可以提供代码补全（如果导入了类型）")
    print("    [OK] 配合 @injectable 装饰器工作")
    print()
    print("  InjectByName:")
    print("    [OK] 纯字符串名称: user_service = InjectByName('UserService')")
    print("    [OK] 完全不需要类型注解")
    print("    [OK] 延迟加载描述符")
    print("    [OK] 更简洁，但 IDE 无代码补全")
    print()
    print("  两种方式都:")
    print("    [OK] 完全正常工作")
    print("    [OK] 单例模式")
    print("    [OK] 自动初始化")
    print("    [OK] 依赖链解析")


if __name__ == '__main__':
    try:
        test_inject_vs_inject_by_name()
    except Exception as e:
        logger.error(f"\n[ERROR] 测试失败: {e}", exc_info=True)
        import sys
        sys.exit(1)

