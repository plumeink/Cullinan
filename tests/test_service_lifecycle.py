# -*- coding: utf-8 -*-
"""
测试 Service 生命周期方法

验证：
1. on_init() 被调用
2. on_startup() 被调用
3. on_shutdown() 被调用
"""

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from cullinan.service import service, Service, get_service_registry
from cullinan.core import get_injection_registry

print("\n" + "=" * 80)
print("测试 Service 生命周期方法")
print("=" * 80)

# 记录调用的方法
lifecycle_calls = []

@service
class TestService(Service):
    def on_init(self):
        """初始化时调用"""
        lifecycle_calls.append('on_init')
        print("  → on_init() called")

    def on_startup(self):
        """启动时调用"""
        lifecycle_calls.append('on_startup')
        print("  → on_startup() called")

    def on_shutdown(self):
        """关闭时调用"""
        lifecycle_calls.append('on_shutdown')
        print("  → on_shutdown() called")

    def on_destroy(self):
        """销毁时调用"""
        lifecycle_calls.append('on_destroy')
        print("  → on_destroy() called")

@service
class DependentService(Service):
    """依赖 TestService 的 Service"""
    from cullinan.core import InjectByName
    test_service = InjectByName('TestService')

    def on_init(self):
        lifecycle_calls.append('DependentService.on_init')
        print("  → DependentService.on_init() called")

    def on_startup(self):
        lifecycle_calls.append('DependentService.on_startup')
        print("  → DependentService.on_startup() called")

print("\n[步骤 1] Service 已定义并注册")

# 初始化
print("\n[步骤 2] 调用 initialize_all()")
injection_registry = get_injection_registry()
service_registry = get_service_registry()

service_registry.initialize_all()

print("\n[步骤 3] 检查生命周期方法调用")
print(f"  调用的方法: {lifecycle_calls}")

# 验证
print("\n[步骤 4] 验证结果")
errors = []

if 'on_init' not in lifecycle_calls:
    errors.append("[ERROR] on_init() 未被调用")
else:
    print("  [OK] on_init() 已调用")

if 'on_startup' not in lifecycle_calls:
    errors.append("[ERROR] on_startup() 未被调用")
else:
    print("  [OK] on_startup() 已调用")

# 检查顺序
if 'on_init' in lifecycle_calls and 'on_startup' in lifecycle_calls:
    init_idx = lifecycle_calls.index('on_init')
    startup_idx = lifecycle_calls.index('on_startup')
    if init_idx < startup_idx:
        print("  [OK] 调用顺序正确：on_init → on_startup")
    else:
        errors.append("[ERROR] 调用顺序错误：应该是 on_init → on_startup")

# 检查依赖顺序
if 'on_init' in lifecycle_calls and 'DependentService.on_init' in lifecycle_calls:
    test_idx = lifecycle_calls.index('on_init')
    dep_idx = lifecycle_calls.index('DependentService.on_init')
    if test_idx < dep_idx:
        print("  [OK] 依赖顺序正确：TestService → DependentService")
    else:
        errors.append("[ERROR] 依赖顺序错误")

print("\n[步骤 5] 测试 destroy_all()")
lifecycle_calls.clear()
service_registry.destroy_all()

print(f"  调用的方法: {lifecycle_calls}")

if 'on_shutdown' in lifecycle_calls:
    print("  [OK] on_shutdown() 已调用")
else:
    errors.append("[ERROR] on_shutdown() 未被调用")

if 'on_destroy' in lifecycle_calls:
    print("  [OK] on_destroy() 已调用")
else:
    errors.append("[ERROR] on_destroy() 未被调用")

print("\n" + "=" * 80)
if errors:
    print("[ERROR] 测试失败：")
    for error in errors:
        print(f"  {error}")
else:
    print("✅ 所有生命周期方法都被正确调用！")
print("=" * 80)

