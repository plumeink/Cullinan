# -*- coding: utf-8 -*-
"""
诊断 Controller 中 Service 注入问题

测试场景:
1. Service 是否正确初始化
2. InjectByName 是否能解析到 Service 实例
3. Controller 实例化时注入是否正常
"""

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# =============================================================================
# 步骤 1: 定义 Service
# =============================================================================

from cullinan.service import service, Service
from cullinan.core import InjectByName

@service
class TestService(Service):
    """测试服务"""

    def on_startup(self):
        logger.info("[OK] TestService.on_startup() called")

    def get_binding(self):
        """测试方法"""
        return "TestService.get_binding() called successfully!"

# =============================================================================
# 步骤 2: 定义 Controller
# =============================================================================

from cullinan.controller import controller, get_api

@controller(url='/api/test')
class TestController:
    """测试控制器"""

    # 使用 InjectByName 注入
    test_service = InjectByName('TestService')

    @get_api(url='/check')
    def check_injection(self):
        """检查注入是否正常"""
        logger.info("=== Checking injection ===")

        # 1. 检查属性类型
        logger.info(f"type(self.test_service) = {type(self.test_service)}")
        logger.info(f"self.test_service = {self.test_service}")

        # 2. 尝试调用方法
        try:
            result = self.test_service.get_binding()
            logger.info(f"[OK] Method call successful: {result}")
            return {"status": "ok", "result": result}
        except AttributeError as e:
            logger.error(f"[FAIL] AttributeError: {e}")
            logger.error(f"  test_service type: {type(self.test_service)}")
            logger.error(f"  test_service dir: {dir(self.test_service)[:10]}")
            raise

# =============================================================================
# 步骤 3: 诊断测试
# =============================================================================

def diagnose():
    """诊断注入问题"""

    print("\n" + "=" * 70)
    print("诊断 Controller Service 注入问题")
    print("=" * 70)

    # 1. 检查 Service 是否注册
    print("\n[步骤 1] 检查 Service 注册...")
    from cullinan.service import get_service_registry

    service_registry = get_service_registry()
    services = service_registry.list_all()
    print(f"[OK] 已注册 Service: {services}")

    # 2. 初始化 Service（通过 ApplicationContext）
    print("\n[步骤 2] 初始化 Service（通过 ApplicationContext）...")
    from cullinan.core import ApplicationContext, set_application_context
    ctx = ApplicationContext()
    set_application_context(ctx)
    ctx.refresh()
    print("[OK] Service 初始化完成（通过统一生命周期）")

    # 3. 检查 Service 实例
    print("\n[步骤 3] 检查 Service 实例...")
    test_service = service_registry.get_instance('TestService')
    print(f"[OK] TestService 实例: {test_service}")
    print(f"  类型: {type(test_service)}")
    print(f"  有 get_binding 方法: {hasattr(test_service, 'get_binding')}")

    if test_service:
        result = test_service.get_binding()
        print(f"  调用 get_binding(): {result}")

    # 4. 检查 InjectionRegistry
    print("\n[步骤 4] 检查 InjectionRegistry...")
    from cullinan.core import get_injection_registry

    injection_registry = get_injection_registry()

    # 检查是否有 provider
    print(f"  Provider registries: {len(injection_registry._provider_registries)}")
    for priority, registry in injection_registry._provider_registries:
        print(f"    - Priority {priority}: {type(registry).__name__}")

    # 尝试手动解析依赖
    print("\n[步骤 5] 手动解析依赖...")
    resolved = injection_registry._resolve_dependency('TestService')
    print(f"  Resolved 'TestService': {resolved}")
    print(f"  类型: {type(resolved)}")

    # 5. 测试 InjectByName 描述符
    print("\n[步骤 6] 测试 InjectByName 描述符...")

    # 检查类属性
    print(f"  TestController.test_service (类属性): {TestController.test_service}")
    print(f"  类型: {type(TestController.test_service)}")

    # 创建实例
    print("\n[步骤 7] 创建 Controller 实例...")
    controller_instance = TestController()
    print(f"[OK] Controller 实例创建: {controller_instance}")

    # 检查实例属性
    print("\n[步骤 8] 检查实例属性...")
    print(f"  type(controller_instance.test_service): {type(controller_instance.test_service)}")
    print(f"  controller_instance.test_service: {controller_instance.test_service}")

    # 检查实例字典
    print(f"  'test_service' in instance.__dict__: {'test_service' in controller_instance.__dict__}")
    if 'test_service' in controller_instance.__dict__:
        print(f"  instance.__dict__['test_service']: {controller_instance.__dict__['test_service']}")

    # 尝试调用方法
    print("\n[步骤 9] 尝试调用 Service 方法...")
    try:
        result = controller_instance.test_service.get_binding()
        print(f"[OK] 成功！结果: {result}")
    except AttributeError as e:
        print(f"[FAIL] 失败！错误: {e}")
        print(f"  实际类型: {type(controller_instance.test_service)}")
        print(f"  实际值: {controller_instance.test_service}")

        # 深入检查
        obj = controller_instance.test_service
        print(f"\n  对象详情:")
        print(f"    __class__: {obj.__class__}")
        print(f"    __module__: {getattr(obj, '__module__', 'N/A')}")
        print(f"    dir(obj)[:20]: {dir(obj)[:20]}")

        raise

    print("\n" + "=" * 70)
    print("✅ 诊断完成")
    print("=" * 70)


if __name__ == '__main__':
    try:
        diagnose()
    except Exception as e:
        logger.error(f"\n[ERROR] 诊断失败: {e}", exc_info=True)
        import sys
        sys.exit(1)

