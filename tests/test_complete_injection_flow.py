# -*- coding: utf-8 -*-
"""完整的依赖注入流程测试

模拟原仓库的场景：Controller 注入 Service
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cullinan.core import (
    get_injection_registry,
    injectable,
    Inject,
    InjectByName
)
from cullinan.core.injection_executor import (
    InjectionExecutor,
    set_injection_executor
)
from cullinan.service import service, get_service_registry
from cullinan.controller.registry import get_controller_registry
from cullinan.controller import controller


# ========== 模拟原仓库的服务 ==========

@service
class ChannelService:
    """频道服务"""
    def __init__(self):
        self.name = "ChannelService"
        print(f"[DEBUG] ChannelService initialized")
    
    def get_channels(self):
        return ["channel1", "channel2"]


@service
class BotService:
    """机器人服务"""
    def __init__(self):
        self.name = "BotService"
        print(f"[DEBUG] BotService initialized")
    
    def send_message(self, channel, message):
        return f"Sent to {channel}: {message}"


# ========== 模拟原仓库的控制器 ==========

@controller(url='/api')
class BotController:
    """机器人控制器 - 使用依赖注入"""
    
    # 使用 InjectByName（原仓库的方式）
    channel_service = InjectByName('ChannelService')
    bot_service = InjectByName('BotService')
    
    def handle_webhook(self):
        """处理 webhook（模拟原仓库的场景）"""
        print(f"\n[DEBUG] handle_webhook called")
        print(f"  - channel_service: {self.channel_service}")
        print(f"  - bot_service: {self.bot_service}")
        
        # 使用注入的服务
        channels = self.channel_service.get_channels()
        print(f"  - channels: {channels}")
        
        result = self.bot_service.send_message(channels[0], "test message")
        print(f"  - result: {result}")
        
        return result


def test_complete_flow():
    """测试完整的依赖注入流程"""
    print("\n" + "="*60)
    print("Complete Injection Flow Test")
    print("="*60)
    
    # ========== 1. 初始化依赖注入系统 ==========
    print("\n[Step 1] Initialize dependency injection system...")
    
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    controller_registry = get_controller_registry()
    
    # 初始化 InjectionExecutor
    executor = InjectionExecutor(injection_registry)
    set_injection_executor(executor)
    
    print(f"  ✓ InjectionRegistry: {injection_registry}")
    print(f"  ✓ ServiceRegistry: {service_registry}")
    print(f"  ✓ ControllerRegistry: {controller_registry}")
    print(f"  ✓ InjectionExecutor: {executor}")
    
    # ========== 2. 初始化服务 ==========
    print("\n[Step 2] Initialize services...")
    
    service_count = service_registry.count()
    print(f"  - Registered services: {service_count}")
    
    service_registry.initialize_all()
    print(f"  ✓ All services initialized")
    
    # 验证服务
    channel_service = service_registry.get_instance('ChannelService')
    bot_service = service_registry.get_instance('BotService')
    print(f"  - ChannelService: {channel_service}")
    print(f"  - BotService: {bot_service}")
    
    # ========== 3. 获取 Controller 实例 ==========
    print("\n[Step 3] Get controller instance...")
    
    # 检查 controller 是否注册
    if not controller_registry.has('BotController'):
        print("  ✗ BotController not registered!")
        return False
    
    print(f"  ✓ BotController registered")
    
    # 获取 controller 实例（会触发依赖注入）
    try:
        bot_controller = controller_registry.get_instance('BotController')
        print(f"  ✓ BotController instance: {bot_controller}")
    except Exception as e:
        print(f"  ✗ Failed to get BotController instance: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========== 4. 验证依赖注入 ==========
    print("\n[Step 4] Verify dependency injection...")
    
    try:
        # 检查注入的属性
        print(f"  - bot_controller.channel_service: {bot_controller.channel_service}")
        print(f"  - bot_controller.bot_service: {bot_controller.bot_service}")
        
        assert bot_controller.channel_service is not None, "channel_service should be injected"
        assert bot_controller.bot_service is not None, "bot_service should be injected"
        
        print(f"  ✓ Dependencies injected successfully")
    except Exception as e:
        print(f"  ✗ Dependency injection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========== 5. 调用 Controller 方法 ==========
    print("\n[Step 5] Call controller method...")
    
    try:
        result = bot_controller.handle_webhook()
        print(f"  ✓ Method executed successfully")
        print(f"  - Result: {result}")
    except Exception as e:
        print(f"  ✗ Method execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    print("\nStarting complete injection flow test...")
    
    try:
        success = test_complete_flow()
        
        print("\n" + "="*60)
        if success:
            print("✓ All tests passed!")
            print("="*60)
            sys.exit(0)
        else:
            print("✗ Some tests failed!")
            print("="*60)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

