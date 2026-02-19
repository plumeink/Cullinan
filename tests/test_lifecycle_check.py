# -*- coding: utf-8 -*-
"""
验证 Service 生命周期方法是否被调用

Updated to use ApplicationContext (IoC 2.0 unified lifecycle).
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from cullinan.core import InjectByName, ApplicationContext, set_application_context
from cullinan.core.pending import PendingRegistry
from cullinan.service import service, Service


def test_lifecycle():
    """测试 Service 生命周期"""
    print("\n" + "=" * 70)
    print("测试 Service 生命周期 (使用 ApplicationContext)")
    print("=" * 70)

    # Reset state at the beginning of each test
    PendingRegistry.reset()

    # 定义 Service 并实现生命周期方法（在函数内定义避免跨测试污染）
    @service
    class EmailService(Service):
        def on_post_construct(self):
            print("  → EmailService.on_post_construct() called")
            self.initialized = True

        def on_pre_destroy(self):
            print("  → EmailService.on_pre_destroy() called")

        def send_email(self, to):
            return f"Email sent to {to}"

    @service
    class UserService(Service):
        email_service = InjectByName('EmailService')

        def on_post_construct(self):
            print("  → UserService.on_post_construct() called")
            print(f"    - email_service 已注入: {self.email_service is not None}")
            self.initialized = True

        def on_pre_destroy(self):
            print("  → UserService.on_pre_destroy() called")

        def create_user(self, email):
            return self.email_service.send_email(email)

    print("\n[步骤 1] Service 已定义并注册到 PendingRegistry")

    # 创建 ApplicationContext
    print("\n[步骤 2] 创建 ApplicationContext 并 refresh()")
    ctx = ApplicationContext()
    set_application_context(ctx)
    ctx.refresh()

    print(f"\n  已注册: {ctx.list_definitions()}")

    # 获取实例
    print("\n[步骤 3] 获取服务实例...")
    email_service = ctx.get('EmailService')
    user_service = ctx.get('UserService')

    # 验证实例化
    print("\n[步骤 4] 验证实例化和生命周期...")
    print(f"  EmailService 实例: {email_service}")
    print(f"  EmailService.initialized: {getattr(email_service, 'initialized', False)}")
    print(f"  UserService 实例: {user_service}")
    print(f"  UserService.initialized: {getattr(user_service, 'initialized', False)}")

    # 测试功能
    print("\n[步骤 5] 测试 Service 功能...")
    result = user_service.create_user("test@example.com")
    print(f"  结果: {result}")

    # 关闭 ApplicationContext
    print("\n[步骤 6] 关闭 ApplicationContext...")
    ctx.shutdown()

    print("\n" + "=" * 70)
    print("✅ 生命周期方法正常工作！")
    print("=" * 70)


if __name__ == '__main__':
    test_lifecycle()
