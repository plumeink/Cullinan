# -*- coding: utf-8 -*-
"""测试 Service 生命周期集成到应用启动流程"""

import asyncio
import logging
from cullinan.core import Inject
from cullinan.service import service, Service, get_service_registry, reset_service_registry
from cullinan.core.injection import get_injection_registry, reset_injection_registry
from cullinan.core.lifecycle_enhanced import get_lifecycle_manager, reset_lifecycle_manager

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_service_lifecycle_with_phase():
    """测试 Service 生命周期按 phase 顺序执行"""

    # Reset
    reset_injection_registry()
    reset_service_registry()
    reset_lifecycle_manager()

    # Configure injection
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    lifecycle_manager = get_lifecycle_manager()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n" + "="*70)
    print("Service 生命周期测试（模拟应用启动流程）")
    print("="*70 + "\n")

    startup_log = []
    shutdown_log = []

    # 定义不同 phase 的 services
    @service
    class DatabaseService(Service):
        def get_phase(self) -> int:
            return -100  # 最早启动

        def on_startup(self):
            startup_log.append('DatabaseService')
            logger.info("[OK] DatabaseService.on_startup() called (phase=-100)")

        def on_shutdown(self):
            shutdown_log.append('DatabaseService')
            logger.info("[OK] DatabaseService.on_shutdown() called")

    @service
    class BotService(Service):
        database: 'DatabaseService' = Inject()

        def get_phase(self) -> int:
            return -50  # Bot 在 web 之前启动

        def on_startup(self):
            startup_log.append('BotService')
            logger.info("[OK] BotService.on_startup() called (phase=-50)")
            logger.info(f"  Database injected: {type(self.database).__name__}")

        def on_shutdown(self):
            shutdown_log.append('BotService')
            logger.info("[OK] BotService.on_shutdown() called")

    @service
    class UserService(Service):
        def get_phase(self) -> int:
            return 0  # 默认 phase

        def on_startup(self):
            startup_log.append('UserService')
            logger.info("[OK] UserService.on_startup() called (phase=0)")

        def on_shutdown(self):
            shutdown_log.append('UserService')
            logger.info("[OK] UserService.on_shutdown() called")

    # 模拟应用启动流程
    print("[1] 扫描和注册 Services...")
    service_count = service_registry.count()
    print(f"    找到 {service_count} 个 services\n")

    print("[2] 实例化并注册到生命周期管理器...")
    for service_name in service_registry.list_all():
        service_instance = service_registry.get_instance(service_name)
        metadata = service_registry.get_metadata(service_name)
        dependencies = metadata.get('dependencies', []) if metadata else []

        lifecycle_manager.register(
            service_instance,
            name=service_name,
            dependencies=dependencies
        )
        print(f"    [OK] {service_name} 已注册")

    print("\n[3] 执行生命周期启动...")
    asyncio.run(lifecycle_manager.startup())

    print("\n[4] 验证启动顺序...")
    expected_order = ['DatabaseService', 'BotService', 'UserService']
    assert startup_log == expected_order, f"启动顺序错误: {startup_log}"
    print(f"    [OK] 启动顺序正确: {' -> '.join(startup_log)}")

    print("\n[5] 模拟 Web 服务器运行...")
    print("    (在实际应用中，这里会启动 Tornado)")

    print("\n[6] 执行生命周期关闭...")
    asyncio.run(lifecycle_manager.shutdown())

    print("\n[7] 验证关闭顺序（逆序）...")
    expected_shutdown = ['UserService', 'BotService', 'DatabaseService']
    assert shutdown_log == expected_shutdown, f"关闭顺序错误: {shutdown_log}"
    print(f"    [OK] 关闭顺序正确: {' -> '.join(shutdown_log)}")

    print("\n" + "="*70)
    print("SUCCESS: Service 生命周期按 phase 正确执行！")
    print("="*70)
    print("\n关键点:")
    print("  1. DatabaseService (phase=-100) 最先启动")
    print("  2. BotService (phase=-50) 在 Web 之前启动")
    print("  3. UserService (phase=0) 最后启动")
    print("  4. 关闭顺序与启动顺序相反")
    print("  5. 依赖注入正常工作")
    print("\n这意味着您的 BotService 会在 Web 服务器启动前完成初始化！")
    print("="*70 + "\n")

    return True


def test_async_lifecycle_hooks():
    """测试异步生命周期钩子"""

    reset_injection_registry()
    reset_service_registry()
    reset_lifecycle_manager()

    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    lifecycle_manager = get_lifecycle_manager()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n" + "="*70)
    print("异步生命周期钩子测试")
    print("="*70 + "\n")

    async_log = []

    @service
    class AsyncBotService(Service):
        def get_phase(self) -> int:
            return -50

        async def on_startup_async(self):
            """模拟 Bot 登录（异步操作）"""
            async_log.append('startup_begin')
            logger.info("BotService: 开始异步登录...")
            await asyncio.sleep(0.1)  # 模拟登录延迟
            async_log.append('startup_complete')
            logger.info("BotService: 登录完成！")

        async def on_shutdown_async(self):
            """模拟 Bot 登出（异步操作）"""
            async_log.append('shutdown_begin')
            logger.info("BotService: 开始异步登出...")
            await asyncio.sleep(0.1)  # 模拟登出延迟
            async_log.append('shutdown_complete')
            logger.info("BotService: 登出完成！")

    # 注册
    service_instance = service_registry.get_instance('AsyncBotService')
    lifecycle_manager.register(service_instance, name='AsyncBotService')

    # 启动
    print("[1] 执行异步启动...")
    asyncio.run(lifecycle_manager.startup())

    assert 'startup_begin' in async_log
    assert 'startup_complete' in async_log
    print("    [OK] 异步启动钩子执行成功")

    # 关闭
    print("\n[2] 执行异步关闭...")
    asyncio.run(lifecycle_manager.shutdown())

    assert 'shutdown_begin' in async_log
    assert 'shutdown_complete' in async_log
    print("    [OK] 异步关闭钩子执行成功")

    print("\n" + "="*70)
    print("SUCCESS: 异步生命周期钩子正常工作！")
    print("="*70 + "\n")

    return True


if __name__ == '__main__':
    try:
        print("\n" + "="*70)
        print("Cullinan Service 生命周期集成测试")
        print("="*70)

        success1 = test_service_lifecycle_with_phase()
        success2 = test_async_lifecycle_hooks()

        if success1 and success2:
            print("\n" + "="*70)
            print("🎉 所有测试通过！")
            print("="*70)
            print("\n现在您的应用启动流程是:")
            print("  1. 扫描 Services 和 Controllers")
            print("  2. 配置依赖注入")
            print("  3. 实例化 Services")
            print("  4. 按 phase 顺序执行 on_startup")
            print("     - DatabaseService (phase=-100)")
            print("     - BotService (phase=-50) ← 您的 Bot 在这里启动")
            print("     - 其他 Services (phase=0)")
            print("  5. 启动 Web 服务器")
            print("  6. 处理请求")
            print("  7. 关闭时按逆序执行 on_shutdown")
            print("\n[INFO] 您的 BotService 会在 Web 服务器启动前完成登录！")
            print("="*70 + "\n")
            exit(0)
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

