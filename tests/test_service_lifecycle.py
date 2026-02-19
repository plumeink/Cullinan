# -*- coding: utf-8 -*-
"""
测试 Service 生命周期方法 (使用 ApplicationContext)

验证：
1. on_post_construct() 被调用
2. on_startup() 被调用
3. on_shutdown() 被调用
4. on_pre_destroy() 被调用
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from cullinan.core import ApplicationContext, set_application_context, InjectByName
from cullinan.core.pending import PendingRegistry
from cullinan.service import service, Service


def test_service_lifecycle():
    print("\n" + "=" * 80)
    print("测试 Service 生命周期方法 (使用 ApplicationContext)")
    print("=" * 80)

    # Reset state
    PendingRegistry.reset()

    # 记录调用的方法
    lifecycle_calls = []

    @service
    class TestService(Service):
        def on_post_construct(self):
            """构造后调用"""
            lifecycle_calls.append('on_post_construct')
            print("  → on_post_construct() called")

        def on_startup(self):
            """启动时调用"""
            lifecycle_calls.append('on_startup')
            print("  → on_startup() called")

        def on_shutdown(self):
            """关闭时调用"""
            lifecycle_calls.append('on_shutdown')
            print("  → on_shutdown() called")

        def on_pre_destroy(self):
            """销毁前调用"""
            lifecycle_calls.append('on_pre_destroy')
            print("  → on_pre_destroy() called")

    @service
    class DependentService(Service):
        """依赖 TestService 的 Service"""
        test_service = InjectByName('TestService')

        def on_post_construct(self):
            lifecycle_calls.append('DependentService.on_post_construct')
            print("  → DependentService.on_post_construct() called")

        def on_startup(self):
            lifecycle_calls.append('DependentService.on_startup')
            print("  → DependentService.on_startup() called")

    print("\n[步骤 1] Service 已定义并注册到 PendingRegistry")

    # 创建 ApplicationContext
    print("\n[步骤 2] 创建 ApplicationContext 并 refresh()")
    ctx = ApplicationContext()
    set_application_context(ctx)
    ctx.refresh()

    print("\n[步骤 3] 检查生命周期方法调用")
    print(f"  调用的方法: {lifecycle_calls}")

    # 验证
    print("\n[步骤 4] 验证结果")
    errors = []

    if 'on_post_construct' not in lifecycle_calls:
        errors.append("[ERROR] on_post_construct() 未被调用")
    else:
        print("  [OK] on_post_construct() 已调用")

    if 'on_startup' not in lifecycle_calls:
        errors.append("[ERROR] on_startup() 未被调用")
    else:
        print("  [OK] on_startup() 已调用")

    # 检查顺序
    if 'on_post_construct' in lifecycle_calls and 'on_startup' in lifecycle_calls:
        init_idx = lifecycle_calls.index('on_post_construct')
        startup_idx = lifecycle_calls.index('on_startup')
        if init_idx < startup_idx:
            print("  [OK] 调用顺序正确：on_post_construct → on_startup")
        else:
            errors.append("[ERROR] 调用顺序错误：应该是 on_post_construct → on_startup")

    # 检查依赖顺序
    if 'on_post_construct' in lifecycle_calls and 'DependentService.on_post_construct' in lifecycle_calls:
        test_idx = lifecycle_calls.index('on_post_construct')
        dep_idx = lifecycle_calls.index('DependentService.on_post_construct')
        if test_idx < dep_idx:
            print("  [OK] 依赖顺序正确：TestService → DependentService")
        else:
            errors.append("[ERROR] 依赖顺序错误")

    print("\n[步骤 5] 测试 shutdown()")
    lifecycle_calls.clear()
    ctx.shutdown()

    print(f"  调用的方法: {lifecycle_calls}")

    if 'on_shutdown' in lifecycle_calls:
        print("  [OK] on_shutdown() 已调用")
    else:
        errors.append("[ERROR] on_shutdown() 未被调用")

    if 'on_pre_destroy' in lifecycle_calls:
        print("  [OK] on_pre_destroy() 已调用")
    else:
        errors.append("[ERROR] on_pre_destroy() 未被调用")

    print("\n" + "=" * 80)
    if errors:
        print("[ERROR] 测试失败：")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("✅ 所有生命周期方法都被正确调用！")
        print("=" * 80)
        return True


if __name__ == '__main__':
    success = test_service_lifecycle()
    exit(0 if success else 1)
