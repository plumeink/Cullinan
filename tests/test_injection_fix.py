# -*- coding: utf-8 -*-
"""测试依赖注入修复

验证 InjectionExecutor 是否正确初始化，以及 Controller 能否正确注入 Service 依赖。

作者：Plumeink
"""

import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_injection_executor_initialization():
    """测试 InjectionExecutor 是否在 application.py 的 run() 函数中正确初始化"""
    logger.info("=" * 80)
    logger.info("测试 1: InjectionExecutor 初始化")
    logger.info("=" * 80)
    
    # 模拟 application.py 的初始化流程
    from cullinan.core.injection import get_injection_registry
    from cullinan.service.registry import get_service_registry
    from cullinan.core.injection_executor import InjectionExecutor, set_injection_executor, has_injection_executor
    
    # 1. 获取注册表
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    
    # 2. 初始化 InjectionExecutor
    executor = InjectionExecutor(injection_registry)
    set_injection_executor(executor)
    
    # 3. 验证初始化
    if has_injection_executor():
        logger.info("[OK] InjectionExecutor 已正确初始化")
        return True
    else:
        logger.error("[FAIL] InjectionExecutor 未正确初始化")
        return False


def test_service_registration_and_injection():
    """测试 Service 注册和依赖注入"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 2: Service 注册和依赖注入")
    logger.info("=" * 80)
    
    from cullinan.service import Service, service
    from cullinan.core import InjectByName
    
    # 定义一个测试 Service
    @service
    class TestService(Service):
        def __init__(self):
            super().__init__()
            logger.info("TestService 实例化")
        
        def on_init(self):
            logger.info("TestService.on_init() 被调用")
        
        def get_message(self):
            return "Hello from TestService"
    
    # 注册并初始化 Service
    from cullinan.service.registry import get_service_registry
    service_registry = get_service_registry()
    
    try:
        service_registry.initialize_all()
        logger.info(f"[OK] 成功初始化 {service_registry.count()} 个服务")
    except Exception as e:
        logger.error(f"[FAIL] Service 初始化失败: {e}")
        return False
    
    # 测试通过依赖注入获取 Service
    from cullinan.core.injection_executor import get_injection_executor
    executor = get_injection_executor()
    
    # 模拟 Controller 注入
    class TestController:
        test_service = InjectByName('TestService')
    
    # 扫描并注入
    from cullinan.core.injection import get_injection_registry
    injection_registry = get_injection_registry()
    injection_registry.scan_class(TestController)
    
    # 创建实例并注入
    controller = TestController()
    metadata = injection_registry.get_injection_metadata(TestController)
    
    if metadata and metadata.has_injections():
        executor.inject_instance(controller, metadata)
        logger.info("[OK] Controller 依赖注入成功")
        
        # 验证注入的 Service 是否可用
        try:
            message = controller.test_service.get_message()
            logger.info(f"[OK] 注入的 Service 可用，返回消息: {message}")
            return True
        except Exception as e:
            logger.error(f"[FAIL] 注入的 Service 不可用: {e}")
            return False
    else:
        logger.error("[FAIL] Controller 没有注入点")
        return False


def test_controller_with_injectable_decorator():
    """测试使用 @injectable 装饰器的 Controller"""
    logger.info("\n" + "=" * 80)
    logger.info("测试 3: 使用 @injectable 装饰器的 Controller")
    logger.info("=" * 80)
    
    from cullinan.service import Service, service
    from cullinan.core import InjectByName, injectable
    
    # 定义另一个测试 Service
    @service
    class AnotherTestService(Service):
        def __init__(self):
            super().__init__()
            logger.info("AnotherTestService 实例化")
        
        def on_init(self):
            logger.info("AnotherTestService.on_init() 被调用")
        
        def get_data(self):
            return {"status": "ok"}
    
    # 初始化 Service
    from cullinan.service.registry import get_service_registry
    service_registry = get_service_registry()
    
    try:
        service_registry.initialize_all()
        logger.info(f"[OK] 成功初始化 {service_registry.count()} 个服务")
    except Exception as e:
        logger.error(f"[FAIL] Service 初始化失败: {e}")
        return False
    
    # 使用 @injectable 装饰器
    @injectable
    class TestController:
        another_service = InjectByName('AnotherTestService')
    
    # 直接实例化（@injectable 会自动注入）
    try:
        controller = TestController()
        logger.info("[OK] Controller 实例化成功（@injectable 自动注入）")
        
        # 验证注入的 Service
        data = controller.another_service.get_data()
        logger.info(f"[OK] 注入的 Service 可用，返回数据: {data}")
        return True
    except Exception as e:
        logger.error(f"[FAIL] Controller 实例化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    logger.info("开始测试依赖注入修复")
    logger.info("=" * 80)
    
    results = []
    
    # 测试 1: InjectionExecutor 初始化
    results.append(("InjectionExecutor 初始化", test_injection_executor_initialization()))
    
    # 测试 2: Service 注册和注入
    results.append(("Service 注册和依赖注入", test_service_registration_and_injection()))
    
    # 测试 3: @injectable 装饰器
    results.append(("@injectable 装饰器", test_controller_with_injectable_decorator()))
    
    # 汇总结果
    logger.info("\n" + "=" * 80)
    logger.info("测试结果汇总")
    logger.info("=" * 80)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        logger.info(f"{status} {name}")
    
    # 统计
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info("=" * 80)
    logger.info(f"测试完成: {passed}/{total} 通过")
    logger.info("=" * 80)
    
    if passed == total:
        logger.info("所有测试通过！依赖注入修复成功。")
        return 0
    else:
        logger.error(f"有 {total - passed} 个测试失败。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

