# -*- coding: utf-8 -*-
"""模拟原仓库的使用场景

模拟 BotController 使用 ChannelService 的场景，验证依赖注入是否正常工作。

作者：Plumeink
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_bot_controller_scenario():
    """模拟 BotController 场景"""
    logger.info("=" * 80)
    logger.info("模拟原仓库场景：BotController 注入 ChannelService")
    logger.info("=" * 80)

    # 1. 初始化依赖注入系统（模拟 application.py 的启动流程）
    logger.info("\n步骤 1: 初始化依赖注入系统...")
    from cullinan.core.injection import get_injection_registry
    from cullinan.service.registry import get_service_registry
    from cullinan.core.injection_executor import InjectionExecutor, set_injection_executor

    injection_registry = get_injection_registry()
    service_registry = get_service_registry()

    # 关键修复：初始化 InjectionExecutor
    executor = InjectionExecutor(injection_registry)
    set_injection_executor(executor)

    logger.info("✓ InjectionExecutor 已初始化")

    # 2. 定义 Service（模拟 ChannelService）
    logger.info("\n步骤 2: 定义 ChannelService...")
    from cullinan.service import Service, service

    @service
    class ChannelService(Service):
        def __init__(self):
            super().__init__()
            self.channels = {}

        def on_init(self):
            logger.info("ChannelService 初始化完成")

        def get_channel(self, channel_id: str):
            return self.channels.get(channel_id)

        def register_channel(self, channel_id: str, channel_info: dict):
            self.channels[channel_id] = channel_info
            return True

    logger.info("✓ ChannelService 已定义")

    # 3. 定义另一个 Service（模拟 BotService）
    logger.info("\n步骤 3: 定义 BotService...")

    @service
    class BotService(Service):
        def __init__(self):
            super().__init__()
            self.bot_name = "TestBot"

        def on_init(self):
            logger.info("BotService 初始化完成")

        def get_bot_name(self):
            return self.bot_name

    logger.info("✓ BotService 已定义")

    # 4. 初始化所有 Service
    logger.info("\n步骤 4: 初始化所有 Service...")
    service_registry.initialize_all()
    logger.info(f"✓ 成功初始化 {service_registry.count()} 个服务")

    # 5. 定义 Controller（模拟 BotController）
    logger.info("\n步骤 5: 定义 BotController...")
    from cullinan.controller.core import controller, post_api
    from cullinan.core import InjectByName
    import json

    @controller(url='/api')
    class BotController:
        # 依赖注入 - 这里之前会失败
        channel_service = InjectByName('ChannelService')
        bot_service = InjectByName('BotService')

        @post_api(url='/web-hook', get_request_body=True)
        async def handle_webhook(self, request_body):
            """处理 webhook"""
            logger.info("处理 webhook 请求...")

            # 访问注入的 service - 之前会抛出 RegistryError
            try:
                # 注册一个测试频道
                self.channel_service.register_channel('test_channel', {'name': 'Test Channel'})

                # 获取频道信息
                channel = self.channel_service.get_channel('test_channel')

                # 获取 bot 名称
                bot_name = self.bot_service.get_bot_name()

                logger.info(f"✓ 成功访问 channel_service: {channel}")
                logger.info(f"✓ 成功访问 bot_service: {bot_name}")

                return {
                    "success": True,
                    "channel": channel,
                    "bot": bot_name
                }
            except Exception as e:
                logger.error(f"✗ 访问 service 失败: {e}")
                import traceback
                traceback.print_exc()
                raise

    logger.info("✓ BotController 已定义")

    # 6. 测试 Controller 实例化和依赖注入
    logger.info("\n步骤 6: 测试 Controller 实例化...")
    from cullinan.controller.registry import get_controller_registry

    controller_registry = get_controller_registry()

    # 获取 Controller 实例（这里之前会失败）
    try:
        bot_controller = controller_registry.get_instance('BotController')
        logger.info("✓ BotController 实例化成功")

        # 验证依赖注入
        if bot_controller.channel_service is not None:
            logger.info("✓ channel_service 注入成功")
        else:
            logger.error("✗ channel_service 为 None")
            return False

        if bot_controller.bot_service is not None:
            logger.info("✓ bot_service 注入成功")
        else:
            logger.error("✗ bot_service 为 None")
            return False

        # 7. 直接测试注入的 service 是否可用
        logger.info("\n步骤 7: 直接测试注入的 service 功能...")

        # 测试 channel_service
        bot_controller.channel_service.register_channel('test_channel', {'name': 'Test Channel'})
        channel = bot_controller.channel_service.get_channel('test_channel')
        logger.info(f"✓ channel_service 工作正常: {channel}")

        # 测试 bot_service
        bot_name = bot_controller.bot_service.get_bot_name()
        logger.info(f"✓ bot_service 工作正常: {bot_name}")

        # 8. 验证结果
        logger.info("\n步骤 8: 验证结果...")
        if channel is not None and bot_name == "TestBot":
            logger.info("✓ 所有 service 都正常工作")
            logger.info(f"✓ 频道信息: {channel}")
            logger.info(f"✓ Bot 名称: {bot_name}")
            return True
        else:
            logger.error("✗ service 功能异常")
            return False

    except Exception as e:
        logger.error(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger.info("开始测试原仓库场景...")

    try:
        success = test_bot_controller_scenario()

        logger.info("\n" + "=" * 80)
        if success:
            logger.info("✅ 测试通过！依赖注入问题已修复。")
            logger.info("=" * 80)
            return 0
        else:
            logger.error("❌ 测试失败！")
            logger.info("=" * 80)
            return 1
    except Exception as e:
        logger.error(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        logger.info("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

