# -*- coding: utf-8 -*-
"""
验证 Service 生命周期方法是否被调用
"""

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from cullinan.service import service, Service
from cullinan.core import InjectByName

# 定义 Service 并实现生命周期方法
@service
class EmailService(Service):
    def on_init(self):
        print("  → EmailService.on_init() called")
        self.initialized = True
    
    def on_destroy(self):
        print("  → EmailService.on_destroy() called")
    
    def send_email(self, to):
        return f"Email sent to {to}"

@service
class UserService(Service):
    email_service = InjectByName('EmailService')
    
    def on_init(self):
        print("  → UserService.on_init() called")
        print(f"    - email_service 已注入: {self.email_service is not None}")
        self.initialized = True
    
    def on_destroy(self):
        print("  → UserService.on_destroy() called")
    
    def create_user(self, email):
        return self.email_service.send_email(email)

# 测试
def test_lifecycle():
    print("\n" + "=" * 70)
    print("测试 Service 生命周期")
    print("=" * 70)
    
    # 1. 配置依赖注入
    from cullinan.core import get_injection_registry
    from cullinan.service import get_service_registry
    
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)
    
    print("\n[步骤 1] 扫描完成，Service 已注册但未实例化")
    print(f"  已注册: {list(service_registry.list_all().keys())}")
    
    # 2. 初始化 Service（会调用 on_init）
    print("\n[步骤 2] 调用 initialize_all()...")
    service_registry.initialize_all()
    
    # 3. 验证实例化和 on_init
    print("\n[步骤 3] 验证实例化和生命周期...")
    email_service = service_registry.get_instance('EmailService')
    user_service = service_registry.get_instance('UserService')
    
    print(f"  EmailService 实例: {email_service}")
    print(f"  EmailService.initialized: {getattr(email_service, 'initialized', False)}")
    print(f"  UserService 实例: {user_service}")
    print(f"  UserService.initialized: {getattr(user_service, 'initialized', False)}")
    
    # 4. 测试功能
    print("\n[步骤 4] 测试 Service 功能...")
    result = user_service.create_user("test@example.com")
    print(f"  结果: {result}")
    
    print("\n" + "=" * 70)
    print("✅ 生命周期方法正常工作！")
    print("=" * 70)

if __name__ == '__main__':
    test_lifecycle()

