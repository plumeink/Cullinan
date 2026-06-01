# -*- coding: utf-8 -*-
"""测试 Service 生命周期集成到应用启动流程 (使用 ApplicationContext)"""

import asyncio
import logging

from cullinan.core import Inject, ApplicationContext, set_application_context
from cullinan.core.pending import PendingRegistry
from cullinan.core.services import service, Service
from cullinan.core.lifecycle_enhanced import reset_lifecycle_manager

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_service_lifecycle_with_phase():
    """测试 Service 生命周期按 phase 顺序执行"""

    # Reset
    PendingRegistry.reset()
    reset_lifecycle_manager()

    print("\n" + "="*70)
    print("Service 生命周期测试（使用 ApplicationContext）")
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
        database: DatabaseService = Inject()

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
    print("[1] 创建 ApplicationContext 并 refresh...")
    ctx = ApplicationContext()
    set_application_context(ctx)
    try:
        ctx.refresh()

        definitions = ctx.list_definitions()
        print(f"    已注册 {len(definitions)} 个组件: {definitions}\n")

        print("[2] 验证启动顺序...")
        expected_order = ['DatabaseService', 'BotService', 'UserService']
        assert startup_log == expected_order, f"启动顺序错误: {startup_log}"
        print(f"    [OK] 启动顺序正确: {' -> '.join(startup_log)}")

        print("\n[3] 模拟 Web 服务器运行...")
        print("    (在实际应用中，这里会启动 Tornado)")
    finally:
        print("\n[4] 执行 shutdown...")
        ctx.shutdown()
        set_application_context(None)
        PendingRegistry.reset()
        reset_lifecycle_manager()

    print("\n[5] 验证关闭顺序（逆序）...")
    expected_shutdown = ['UserService', 'BotService', 'DatabaseService']
    assert shutdown_log == expected_shutdown, f"关闭顺序错误: {shutdown_log}"
    print(f"    [OK] 关闭顺序正确: {' -> '.join(shutdown_log)}")


def test_async_lifecycle_hooks():
    """测试异步生命周期钩子"""

    PendingRegistry.reset()
    reset_lifecycle_manager()

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

    # 创建 ApplicationContext
    print("[1] 创建 ApplicationContext 并 refresh...")
    ctx = ApplicationContext()
    set_application_context(ctx)
    try:
        ctx.refresh()

        assert 'startup_begin' in async_log
        assert 'startup_complete' in async_log
        print("    [OK] 异步启动钩子执行成功")
    finally:
        print("\n[2] 执行 shutdown...")
        ctx.shutdown()
        set_application_context(None)
        PendingRegistry.reset()
        reset_lifecycle_manager()

    assert 'shutdown_begin' in async_log
    assert 'shutdown_complete' in async_log
    print("    [OK] 异步关闭钩子执行成功")
