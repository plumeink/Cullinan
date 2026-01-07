# -*- coding: utf-8 -*-
"""
专项回归测试：BotController 依赖注入 Bug

Author: Plumeink

此测试模拟原始 Bug 场景：
- BotController 注入 MultiChannelService
- 调用 handle_secondary_bot_notification 接口
- 验证 hasattr 检查和方法调用正常工作
"""

import sys
import json

sys.path.insert(0, '.')


def reset_all_registries():
    """重置所有注册表"""
    from cullinan.controller.registry import reset_controller_registry
    from cullinan.core.pending import PendingRegistry
    from cullinan.core import set_application_context
    
    reset_controller_registry()
    
    pending = PendingRegistry.get_instance()
    pending._registrations.clear()
    pending._frozen = False
    
    set_application_context(None)


def test_bot_controller_regression():
    """
    回归测试：模拟 BotController 的原始 Bug 场景
    
    原始错误：
    AttributeError: 'Inject' object has no attribute 'get_binding'
    
    原因：
    ControllerRegistry.get_instance() 直接实例化 Controller，
    没有通过 ApplicationContext 进行依赖注入
    """
    print("=" * 70)
    print("专项回归测试：BotController 依赖注入 Bug")
    print("=" * 70)
    
    reset_all_registries()
    
    from cullinan.core import (
        ApplicationContext, set_application_context,
        service, controller, Inject
    )
    from cullinan.controller.registry import get_controller_registry

    # ========== 模拟服务层 ==========
    
    class ChannelBinding:
        """模拟 channel 绑定数据"""
        def __init__(self, channel_id: str, webhook_secret: str):
            self.channel_id = channel_id
            self.webhook_secret = webhook_secret

    @service
    class MultiChannelService:
        """模拟 MultiChannelService"""
        
        def __init__(self):
            self._bindings = {
                "owner/repo": ChannelBinding("123456789", "secret123"),
                "test/project": ChannelBinding("987654321", "secret456"),
            }
        
        def get_binding(self, repo_full_name: str, bot_id: str = None):
            """获取仓库的 channel 绑定"""
            return self._bindings.get(repo_full_name)

    @service
    class MultiBotManager:
        """模拟 MultiBotManager"""
        
        def __init__(self):
            self._ready = {"secondary": True, "primary": True}
        
        def is_ready(self, bot_id: str = None) -> bool:
            """检查 bot 是否就绪"""
            if bot_id is None:
                bot_id = "primary"
            return self._ready.get(bot_id, False)
        
        def send_message(self, channel_id: str, content: str = None, 
                        embed: dict = None, bot_id: str = None) -> dict:
            """发送消息"""
            return {"ok": True, "msg": "sent"}

    # ========== 模拟 Controller 层 ==========
    
    @controller(url='/api')
    class BotController:
        """模拟 BotController - 原始 Bug 发生的位置"""
        
        multi_channel_service: MultiChannelService = Inject()
        multi_bot_manager: MultiBotManager = Inject()
        
        def handle_secondary_bot_notification(self, request_body: bytes):
            """
            处理自定义通知请求 - 原始 Bug 触发点
            
            原始错误发生在这里：
            if not self.multi_channel_service or not hasattr(self.multi_channel_service, 'get_binding'):
                这里 hasattr 返回 False 因为 self.multi_channel_service 是 Inject 对象
            """
            bot_id = "secondary"
            
            # 解析请求体
            try:
                if isinstance(request_body, bytes):
                    body_str = request_body.decode("utf-8")
                else:
                    body_str = str(request_body)
                payload = json.loads(body_str)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                return {"error": f"Invalid JSON: {e}"}
            
            # 提取字段
            title = payload.get('title')
            content = payload.get('content')
            time_str = payload.get('time')
            repo_full_name = payload.get('repo')
            
            # 验证必需字段
            missing_fields = []
            if not title:
                missing_fields.append('title')
            if not content:
                missing_fields.append('content')
            if not time_str:
                missing_fields.append('time')
            if not repo_full_name:
                missing_fields.append('repo')
            
            if missing_fields:
                return {"error": f"Missing fields: {', '.join(missing_fields)}"}
            
            # ========== 原始 Bug 触发点 ==========
            # 这里的 hasattr 检查在 Bug 修复前会失败
            if not self.multi_channel_service or not hasattr(self.multi_channel_service, 'get_binding'):
                return {"error": "MultiChannelService not available or not properly injected"}
            
            binding = self.multi_channel_service.get_binding(repo_full_name, bot_id=bot_id)
            
            if not binding:
                return {"error": f"Repository '{repo_full_name}' is not configured"}
            
            channel_id = binding.channel_id
            
            # ========== 第二个检查点 ==========
            if not self.multi_bot_manager or not hasattr(self.multi_bot_manager, 'is_ready'):
                return {"error": "MultiBotManager not available or not properly injected"}
            
            if not self.multi_bot_manager.is_ready(bot_id):
                return {"error": f"Bot '{bot_id}' is not ready"}
            
            # 发送消息
            resp = self.multi_bot_manager.send_message(
                channel_id=channel_id,
                content=f"**{title}**\n{content}\n_Time: {time_str}_",
                bot_id=bot_id
            )
            
            if resp.get('ok', False):
                return {"ok": True, "message": "Notification sent successfully"}
            else:
                return {"error": f"Failed to send: {resp.get('msg', 'unknown')}"}

    # ========== 初始化框架 ==========
    
    ctx = ApplicationContext()
    set_application_context(ctx)
    ctx.refresh()

    registry = get_controller_registry()
    registry.register('BotController', BotController, url_prefix='/api')

    # ========== 获取 Controller 实例 ==========
    
    bot_controller = registry.get_instance('BotController')
    
    print("\n[检查] 依赖注入状态:")
    print(f"  multi_channel_service 类型: {type(bot_controller.multi_channel_service).__name__}")
    print(f"  multi_bot_manager 类型: {type(bot_controller.multi_bot_manager).__name__}")
    
    # 验证注入状态
    is_inject_mcs = isinstance(bot_controller.multi_channel_service, Inject)
    is_inject_mbm = isinstance(bot_controller.multi_bot_manager, Inject)
    
    print(f"  multi_channel_service 是 Inject 对象: {is_inject_mcs}")
    print(f"  multi_bot_manager 是 Inject 对象: {is_inject_mbm}")
    
    if is_inject_mcs or is_inject_mbm:
        print("\n[FAIL] 依赖注入失败！这是原始 Bug 的表现。")
        return False
    
    print("\n[OK] 依赖注入成功！")
    
    # ========== 测试场景 1：正常请求 ==========
    
    print("\n[测试场景 1] 正常请求:")
    request_body = json.dumps({
        "title": "测试通知",
        "content": "这是一条测试消息",
        "time": "2026-01-07 12:00:00",
        "repo": "owner/repo"
    }).encode('utf-8')
    
    result = bot_controller.handle_secondary_bot_notification(request_body)
    print(f"  请求: repo=owner/repo")
    print(f"  响应: {result}")
    
    if result.get('ok'):
        print("  [PASS] 正常请求成功")
    else:
        print(f"  [FAIL] 正常请求失败: {result}")
        return False
    
    # ========== 测试场景 2：未配置的仓库 ==========
    
    print("\n[测试场景 2] 未配置的仓库:")
    request_body = json.dumps({
        "title": "测试",
        "content": "内容",
        "time": "2026-01-07 12:00:00",
        "repo": "unknown/repo"
    }).encode('utf-8')
    
    result = bot_controller.handle_secondary_bot_notification(request_body)
    print(f"  请求: repo=unknown/repo")
    print(f"  响应: {result}")
    
    if "not configured" in result.get('error', ''):
        print("  [PASS] 正确处理未配置仓库")
    else:
        print(f"  [FAIL] 未正确处理: {result}")
        return False
    
    # ========== 测试场景 3：缺少必需字段 ==========
    
    print("\n[测试场景 3] 缺少必需字段:")
    request_body = json.dumps({
        "title": "测试",
        # 缺少 content, time, repo
    }).encode('utf-8')
    
    result = bot_controller.handle_secondary_bot_notification(request_body)
    print(f"  请求: 只有 title")
    print(f"  响应: {result}")
    
    if "Missing fields" in result.get('error', ''):
        print("  [PASS] 正确处理缺少字段")
    else:
        print(f"  [FAIL] 未正确处理: {result}")
        return False
    
    # ========== 测试场景 4：hasattr 验证 ==========
    
    print("\n[测试场景 4] hasattr 验证（原 Bug 关键点）:")
    has_get_binding = hasattr(bot_controller.multi_channel_service, 'get_binding')
    has_is_ready = hasattr(bot_controller.multi_bot_manager, 'is_ready')
    
    print(f"  hasattr(multi_channel_service, 'get_binding'): {has_get_binding}")
    print(f"  hasattr(multi_bot_manager, 'is_ready'): {has_is_ready}")
    
    if has_get_binding and has_is_ready:
        print("  [PASS] hasattr 检查通过")
    else:
        print("  [FAIL] hasattr 检查失败 - 这是原始 Bug！")
        return False
    
    # ========== 总结 ==========
    
    print("\n" + "=" * 70)
    print("回归测试结果: 全部通过")
    print("=" * 70)
    print("原始 Bug 已修复:")
    print("  - Controller 依赖注入正常工作")
    print("  - hasattr 检查返回正确结果")
    print("  - 服务方法可以正常调用")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    success = test_bot_controller_regression()
    sys.exit(0 if success else 1)

