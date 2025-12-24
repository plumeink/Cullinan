# -*- coding: utf-8 -*-
"""诊断 Provider Sources 问题

检查依赖注入系统的 provider sources 是否正确配置。
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cullinan.core import get_injection_registry
from cullinan.service import get_service_registry, service
from cullinan.core.injection_executor import (
    InjectionExecutor,
    set_injection_executor,
    get_injection_executor
)


@service
class ChannelService:
    """模拟原仓库的 ChannelService"""
    def __init__(self):
        self.name = "ChannelService"
        print(f"[DEBUG] ChannelService initialized")


def diagnose_provider_sources():
    """诊断 provider sources 配置"""
    print("\n=== Diagnosing Provider Sources ===\n")

    # 1. 获取注册表
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()

    print(f"1. InjectionRegistry: {injection_registry}")
    print(f"2. ServiceRegistry: {service_registry}")

    # 2. 初始化 InjectionExecutor
    executor = InjectionExecutor(injection_registry)
    set_injection_executor(executor)
    print(f"3. InjectionExecutor initialized: {executor}")

    # 3. 初始化服务
    service_registry.initialize_all()
    print(f"4. Services initialized")

    # 4. 检查 provider sources
    print(f"\n=== Provider Sources ===")
    if hasattr(injection_registry, '_provider_sources'):
        sources = injection_registry._provider_sources
        print(f"Provider sources count: {len(sources)}")
        for priority, source in sources:
            print(f"  - Priority {priority}: {source.__class__.__name__}")
            print(f"    Can provide 'ChannelService': {source.can_provide('ChannelService')}")
    else:
        print("ERROR: InjectionRegistry has no _provider_sources attribute!")

    # 5. 尝试解析依赖
    print(f"\n=== Dependency Resolution ===")
    try:
        dep = injection_registry._resolve_dependency('ChannelService')
        if dep:
            print(f"✓ Successfully resolved 'ChannelService': {dep}")
        else:
            print(f"✗ Failed to resolve 'ChannelService': returned None")

            # 更详细的诊断
            print(f"\n=== Detailed Diagnosis ===")

            # 检查服务是否注册
            if service_registry.has('ChannelService'):
                print(f"✓ ChannelService is registered in ServiceRegistry")
                instance = service_registry.get_instance('ChannelService')
                print(f"  Instance: {instance}")
            else:
                print(f"✗ ChannelService is NOT registered in ServiceRegistry")

            # 检查 ServiceRegistry 是否作为 provider
            from cullinan.core.provider_source import ProviderSource
            if isinstance(service_registry, ProviderSource):
                print(f"✓ ServiceRegistry implements ProviderSource")
                can_provide = service_registry.can_provide('ChannelService')
                print(f"  can_provide('ChannelService'): {can_provide}")
                if can_provide:
                    try:
                        provided = service_registry.provide('ChannelService')
                        print(f"  provide('ChannelService'): {provided}")
                    except Exception as e:
                        print(f"  provide('ChannelService') error: {e}")
            else:
                print(f"✗ ServiceRegistry does NOT implement ProviderSource")

    except Exception as e:
        print(f"✗ Exception during resolution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    try:
        diagnose_provider_sources()
    except Exception as e:
        print(f"\nDiagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

