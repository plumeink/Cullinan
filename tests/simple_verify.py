# -*- coding: utf-8 -*-
"""简单验证脚本"""
import sys
import os

# 添加项目路径
project_path = r'G:\pj\Cullinan'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

print(f"Python version: {sys.version}")
print(f"Current dir: {os.getcwd()}")
print(f"Sys.path: {sys.path[:3]}")

try:
from cullinan.core import Inject, injectable, get_injection_registry, reset_injection_registry
from cullinan.core.registry import SimpleRegistry
print("[OK] Import successful")

    # 简单测试
    reset_injection_registry()
    registry = get_injection_registry()
    print(f"[OK] Registry obtained: {registry}")

    # 创建服务
    class TestService:
        def __init__(self):
            self.value = "test"

    # 注册服务
    service_registry = SimpleRegistry()
    service_registry.register('TestService', TestService())
    registry.add_provider_registry(service_registry)
    print("[OK] Service registered")

    # 测试基本注入
    @injectable
    class BaseClass:
        service: TestService = Inject()

    instance1 = BaseClass()
    print(f"[OK] BaseClass instance created: service={instance1.service.value}")

    # 测试子类继承
    class SubClass(BaseClass):
        pass

    instance2 = SubClass()
    print(f"[OK] SubClass instance created: service={instance2.service.value}")

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)

except Exception as e:
    print(f"\n[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

