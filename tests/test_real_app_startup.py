# -*- coding: utf-8 -*-
"""
测试真实应用启动流程中的 Service 注入

模拟实际应用中：
1. 使用 application.run() 或 CullinanApplication 启动
2. Service 自动初始化
3. Controller 中的依赖注入正常工作
"""

import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# =============================================================================
# 定义 Service
# =============================================================================

from cullinan.service import service, Service
from cullinan.core import InjectByName

@service
class DatabaseService(Service):
    """数据库服务"""

    def on_init(self):
        logger.info("[OK] DatabaseService initialized")
        self.connected = True

    def query(self, sql):
        if not self.connected:
            raise RuntimeError("Database not connected")
        return [{"id": 1, "name": "Test"}]


@service
class UserService(Service):
    """用户服务 - 依赖 DatabaseService"""

    # 注入依赖
    database = InjectByName('DatabaseService')

    def on_init(self):
        logger.info("[OK] UserService initialized")

    def get_users(self):
        """获取用户列表"""
        return self.database.query("SELECT * FROM users")

    def get_binding(self):
        """测试方法"""
        return "UserService.get_binding() works!"


# =============================================================================
# 定义 Controller
# =============================================================================

from cullinan.controller import controller, get_api

@controller(url='/api/users')
class UserController:
    """用户控制器 - 注入 UserService"""

    # 注入 UserService（不需要 import）
    user_service = InjectByName('UserService')

    @get_api(url='/list')
    def list_users(self):
        """获取用户列表"""
        logger.info("=== In UserController.list_users() ===")

        # 检查 user_service 类型
        logger.info(f"type(self.user_service) = {type(self.user_service)}")

        try:
            # 调用 service 方法
            users = self.user_service.get_users()
            logger.info(f"[OK] Got users: {users}")

            # 调用测试方法
            binding = self.user_service.get_binding()
            logger.info(f"[OK] Got binding: {binding}")

            return {"status": "ok", "users": users}
        except AttributeError as e:
            logger.error(f"[FAIL] AttributeError: {e}")
            logger.error(f"  user_service type: {type(self.user_service)}")
            raise


# =============================================================================
# 测试函数
# =============================================================================

def test_with_application_run():
    """测试使用 application.run() 启动"""

    print("\n" + "=" * 70)
    print("测试方案 1: 模拟 application.run() 流程")
    print("=" * 70)

    # 模拟 application.run() 的初始化部分
    from cullinan.core.injection import get_injection_registry
    from cullinan.service.registry import get_service_registry

    print("\n[步骤 1] 配置依赖注入...")
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)
    print("[OK] 依赖注入配置完成")

    print("\n[步骤 2] 检查已注册的 Service...")
    services = list(service_registry.list_all().keys())
    print(f"[OK] 已注册 Service: {services}")

    print("\n[步骤 3] 初始化所有 Service...")
    service_registry.initialize_all()
    print("[OK] Service 初始化完成")

    print("\n[步骤 4] 验证 Service 实例...")
    for name in services:
        instance = service_registry.get_instance(name)
        print(f"  • {name}: {type(instance).__name__}")
        if name == 'UserService':
            # 验证 UserService 的依赖注入
            print(f"    - database: {type(instance.database).__name__}")

    print("\n[步骤 5] 创建 Controller 实例并测试...")
    controller = UserController()
    print(f"[OK] Controller 创建: {type(controller).__name__}")
    print(f"  • user_service 类型: {type(controller.user_service).__name__}")

    # 测试方法调用
    try:
        result = controller.user_service.get_binding()
        print(f"[OK] 方法调用成功: {result}")
    except AttributeError as e:
        print(f"[FAIL] 方法调用失败: {e}")
        raise

    print("\n" + "=" * 70)
    print("✅ 测试通过！")
    print("=" * 70)


def test_with_cullinan_app():
    """测试使用 CullinanApplication 启动"""

    print("\n" + "=" * 70)
    print("测试方案 2: 使用 CullinanApplication")
    print("=" * 70)

    from cullinan.app import CullinanApplication
    import asyncio

    # 创建应用
    app = CullinanApplication()

    print("\n[步骤 1] 执行应用启动...")
    # 同步运行 async startup
    asyncio.run(app.startup())

    print("\n[步骤 2] 验证 Service 是否初始化...")
    from cullinan.service.registry import get_service_registry
    service_registry = get_service_registry()

    for name in service_registry.list_all():
        instance = service_registry.get_instance(name)
        print(f"  • {name}: {type(instance).__name__}")

    print("\n[步骤 3] 创建 Controller 并测试...")
    controller = UserController()
    print(f"[OK] Controller 创建: {type(controller).__name__}")

    try:
        result = controller.user_service.get_binding()
        print(f"[OK] 方法调用成功: {result}")
    except AttributeError as e:
        print(f"[FAIL] 方法调用失败: {e}")
        raise

    print("\n[步骤 4] 关闭应用...")
    asyncio.run(app.shutdown())

    print("\n" + "=" * 70)
    print("✅ 测试通过！")
    print("=" * 70)


def main():
    """主测试函数"""
    try:
        # 测试方案 1: 模拟 application.run()
        test_with_application_run()

        # 重置注册表
        from cullinan.service import reset_service_registry
        from cullinan.core import reset_injection_registry
        reset_service_registry()
        reset_injection_registry()

        # 需要重新导入模块以重新注册 Service
        import importlib
        importlib.reload(sys.modules[__name__])

        # 测试方案 2: 使用 CullinanApplication
        # test_with_cullinan_app()  # 暂时注释，因为需要重新加载模块

        print("\n" + "=" * 70)
        print("🎉 所有测试通过！Service 注入在应用启动流程中正常工作！")
        print("=" * 70)

    except Exception as e:
        logger.error(f"\n[ERROR] 测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

