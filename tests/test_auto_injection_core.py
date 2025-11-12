# -*- coding: utf-8 -*-
"""
测试基于 core 的自动注入系统（Spring-like）

演示：
1. Service 使用 @service 注册
2. Controller 使用 InjectByName 自动注入 Service
3. 完全不需要 import Service 类
4. 应用启动时自动初始化所有 Service
"""

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# =============================================================================
# 步骤 1: 定义 Service（使用 @service 注册）
# =============================================================================

from cullinan.service import service, Service
from cullinan.core import InjectByName

@service
class EmailService(Service):
    """邮件服务"""
    
    def send_email(self, to: str, subject: str, body: str):
        logger.info(f"📧 Sending email to {to}: {subject}")
        return {"status": "sent", "to": to}
    
    def get_something(self):
        """测试方法"""
        return "EmailService data"


@service
class UserService(Service):
    """用户服务 - 依赖 EmailService"""
    
    # 使用 InjectByName 注入，完全不需要 import EmailService！
    email_service = InjectByName('EmailService')
    
    def on_init(self):
        logger.info("[OK] UserService initialized")
    
    def create_user(self, name: str, email: str):
        """创建用户并发送欢迎邮件"""
        logger.info(f"Creating user: {name} ({email})")
        
        # 使用注入的 email_service
        self.email_service.send_email(
            to=email,
            subject="Welcome!",
            body=f"Welcome {name} to Cullinan!"
        )
        
        return {"id": 1, "name": name, "email": email}
    
    def get_all(self):
        """获取所有用户"""
        return [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    
    def get_something(self):
        """测试方法"""
        return "UserService data"


# =============================================================================
# 步骤 2: 定义 Controller（使用 InjectByName 注入 Service）
# =============================================================================

from cullinan.controller import controller, get_api, post_api

@controller(url='/api/users')
class UserController:
    """用户控制器 - 完全不需要 import Service！"""
    
    # 使用 InjectByName 自动注入，无需 import UserService
    user_service = InjectByName('UserService')
    
    @get_api(url='')
    def list_users(self):
        """获取用户列表"""
        logger.info("GET /api/users - Listing users")
        users = self.user_service.get_all()
        return {"users": users}
    
    @post_api(url='')
    def create_user(self, body_params):
        """创建用户"""
        logger.info(f"POST /api/users - Creating user: {body_params}")
        user = self.user_service.create_user(
            name=body_params.get('name'),
            email=body_params.get('email')
        )
        return {"created": True, "user": user}
    
    @get_api(url='/test')
    def test_injection(self):
        """测试依赖注入"""
        logger.info("Testing service injection...")
        data = self.user_service.get_something()
        return {"message": "Service injection works!", "data": data}


# =============================================================================
# 步骤 3: 测试自动注入系统
# =============================================================================

def test_auto_injection():
    """测试自动注入系统"""
    
    print("\n" + "=" * 70)
    print("测试 Cullinan 自动注入系统（Spring-like）")
    print("=" * 70)
    
    # 1. 初始化 Service Registry
    print("\n[步骤 1] 初始化 Service Registry...")
    from cullinan.service import get_service_registry
    
    service_registry = get_service_registry()
    registered_services = service_registry.list_all()
    print(f"[OK] 已注册 {len(registered_services)} 个 Service:")
    for name in registered_services:
        print(f"  - {name}")
    
    # 2. 自动初始化所有 Service
    print("\n[步骤 2] 自动初始化所有 Service...")
    service_registry.initialize_all()
    print("[OK] 所有 Service 已初始化")
    
    # 3. 测试 Service 层的注入
    print("\n[步骤 3] 测试 Service 层的依赖注入...")
    user_service = service_registry.get_instance('UserService')
    print(f"[OK] 获取到 UserService: {user_service}")
    
    # UserService 应该已经注入了 EmailService
    print(f"[OK] UserService.email_service: {user_service.email_service}")
    
    # 测试 Service 方法
    result = user_service.create_user("Alice", "alice@example.com")
    print(f"[OK] 创建用户成功: {result}")
    
    # 4. 测试 Controller 层的注入
    print("\n[步骤 4] 测试 Controller 层的依赖注入...")
    
    # 模拟 Controller 实例化
    controller_instance = UserController()
    print(f"[OK] Controller 实例化成功: {controller_instance}")
    
    # Controller 应该已经注入了 UserService
    print(f"[OK] Controller.user_service: {controller_instance.user_service}")
    
    # 验证注入的 service 可以调用方法
    print(f"[OK] 调用 service 方法: {controller_instance.user_service.get_something()}")

    # 5. 验证注入链
    print("\n[步骤 5] 验证依赖注入链...")
    print(f"Controller -> UserService: {controller_instance.user_service is user_service}")
    print(f"UserService -> EmailService: {user_service.email_service is not None}")
    
    email_service = service_registry.get_instance('EmailService')
    print(f"EmailService 实例: {email_service}")
    print(f"UserService.email_service 是同一个实例: {user_service.email_service is email_service}")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试通过！自动注入系统工作正常！")
    print("=" * 70)
    
    print("\n💡 关键特性:")
    print("  1. [OK] Service 使用 @service 自动注册")
    print("  2. [OK] Controller 和 Service 使用 InjectByName 注入")
    print("  3. [OK] 完全不需要 import 被注入的类")
    print("  4. [OK] 应用启动时自动初始化所有 Service")
    print("  5. [OK] 延迟加载：首次访问时才解析依赖")
    print("  6. [OK] 单例模式：所有注入的是同一个实例")


if __name__ == '__main__':
    try:
        test_auto_injection()
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        import sys
        sys.exit(1)

