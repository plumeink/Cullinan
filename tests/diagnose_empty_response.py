# -*- coding: utf-8 -*-
"""诊断接口返回 200 空 body 问题

作者：Plumeink
日期：2025-12-24
"""

import sys
import logging
import asyncio

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_controller_handler():
    """测试 Controller 和 Handler 的基本功能"""
    logger.info("=" * 80)
    logger.info("诊断：Controller Handler 问题")
    logger.info("=" * 80)

    # 1. 导入并注册服务
    logger.info("\n[1] 导入框架组件...")
    from cullinan.service import service, ServiceRegistry, get_service_registry
    from cullinan.controller import controller, get_controller_registry
    from cullinan.core import Inject, injectable
    from cullinan.core.injection_executor import InjectionExecutor, set_injection_executor
    from cullinan.core import get_injection_registry

    # 2. 初始化依赖注入
    logger.info("\n[2] 初始化依赖注入系统...")
    injection_registry = get_injection_registry()
    executor = InjectionExecutor(injection_registry)
    set_injection_executor(executor)
    logger.info("✓ InjectionExecutor 已初始化")

    # 3. 创建测试服务
    logger.info("\n[3] 创建测试服务...")
    @service
    class TestService:
        def __init__(self):
            self.name = "TestService"
            logger.info(f"✓ {self.name} 已初始化")

        def get_data(self):
            result = {"message": "Hello from TestService", "status": "ok"}
            logger.info(f"TestService.get_data() 返回: {result}")
            return result

    # 注册服务
    service_registry = get_service_registry()
    service_registry.register('TestService', TestService)
    logger.info("✓ TestService 已注册")

    # 4. 创建测试 Controller
    logger.info("\n[4] 创建测试 Controller...")
    @controller(url='/api/test')
    @injectable
    class TestController:
        test_service: TestService = Inject()

        def __init__(self):
            logger.info("TestController.__init__() 调用")

        async def get(self):
            """GET /api/test"""
            logger.info("TestController.get() 被调用")
            logger.info(f"test_service 是否注入: {self.test_service is not None}")

            if self.test_service:
                data = self.test_service.get_data()
                logger.info(f"从服务获取数据: {data}")
                return data
            else:
                logger.error("test_service 未注入！")
                return {"error": "Service not injected"}

    # 5. 检查注册情况
    logger.info("\n[5] 检查注册情况...")
    controller_registry = get_controller_registry()

    logger.info(f"已注册的 Controller 数量: {controller_registry.count()}")
    logger.info(f"已注册的 Service 数量: {service_registry.count()}")

    # 检查 Controller 是否注册
    if 'TestController' in controller_registry._items:
        logger.info("✓ TestController 已在注册表中")
    else:
        logger.error("✗ TestController 未在注册表中！")
        return False

    # 6. 测试 Controller 实例化
    logger.info("\n[6] 测试 Controller 实例化...")
    try:
        controller_instance = controller_registry.get_instance('TestController')
        logger.info(f"✓ Controller 实例化成功: {controller_instance}")
        logger.info(f"Controller 类型: {type(controller_instance)}")
        logger.info(f"test_service 属性: {getattr(controller_instance, 'test_service', 'NOT FOUND')}")

        # 检查是否有 get 方法
        if hasattr(controller_instance, 'get'):
            logger.info("✓ Controller 有 get() 方法")
        else:
            logger.error("✗ Controller 没有 get() 方法！")
            return False
    except Exception as e:
        logger.error(f"✗ Controller 实例化失败: {e}", exc_info=True)
        return False

    # 7. 测试方法调用
    logger.info("\n[7] 测试方法调用...")
    try:
        # 检查方法是否是协程
        import inspect
        if inspect.iscoroutinefunction(controller_instance.get):
            logger.info("✓ get() 是异步方法，使用 asyncio.run()")
            result = asyncio.run(controller_instance.get())
        else:
            logger.info("✓ get() 是同步方法，直接调用")
            result = controller_instance.get()

        logger.info(f"✓ 方法调用成功！")
        logger.info(f"返回结果: {result}")
        logger.info(f"返回类型: {type(result)}")

        # 验证结果
        if result and isinstance(result, dict):
            logger.info("✓ 返回了字典对象")
            if 'message' in result:
                logger.info("✓ 字典包含 'message' 键")
            else:
                logger.warning("⚠ 字典不包含 'message' 键")
        else:
            logger.warning(f"⚠ 返回类型不是字典: {type(result)}")

    except Exception as e:
        logger.error(f"✗ 方法调用失败: {e}", exc_info=True)
        return False

    # 8. 检查 Handler 注册
    logger.info("\n[8] 检查 Handler 方法注册...")
    methods = controller_registry.get_methods('TestController')
    logger.info(f"已注册的方法数量: {len(methods)}")
    for url, http_method, handler_func in methods:
        logger.info(f"  - {http_method.upper()} {url} -> {handler_func}")

    if not methods:
        logger.warning("⚠ 没有注册任何 Handler 方法！这可能是问题所在！")

    logger.info("\n" + "=" * 80)
    logger.info("诊断完成")
    logger.info("=" * 80)

    return True


if __name__ == '__main__':
    try:
        success = test_controller_handler()
        if success:
            logger.info("\n✅ 诊断测试通过")
        else:
            logger.error("\n❌ 诊断测试失败")
            sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 诊断过程出错: {e}", exc_info=True)
        sys.exit(1)

