# -*- coding: utf-8 -*-
"""测试依赖注入的回退机制

验证当 InjectionExecutor 失败时，自动回退到 ServiceRegistry。
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cullinan.core import (
    injectable,
    InjectByName
)
from cullinan.service import service, get_service_registry


@service
class TestService:
    """测试服务"""
    def __init__(self):
        self.name = "TestService"
        print(f"[DEBUG] TestService initialized")
    
    def get_data(self):
        return "test data"


@injectable
class TestController:
    """测试控制器 - 不初始化 InjectionExecutor"""
    test_service = InjectByName('TestService')
    
    def get_test_data(self):
        if self.test_service:
            return self.test_service.get_data()
        return None


def test_fallback_injection():
    """测试回退注入机制"""
    print("\n" + "="*60)
    print("Fallback Injection Test")
    print("="*60)
    
    # 1. 初始化服务（不初始化 InjectionExecutor）
    print("\n[Step 1] Initialize services (without InjectionExecutor)...")
    service_registry = get_service_registry()
    service_registry.initialize_all()
    print(f"  ✓ Services initialized: {service_registry.count()}")
    
    # 2. 实例化 Controller（应该触发回退机制）
    print("\n[Step 2] Create controller instance (should fallback)...")
    try:
        controller = TestController()
        print(f"  ✓ Controller created: {controller}")
    except Exception as e:
        print(f"  ✗ Controller creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 验证依赖注入（通过回退机制）
    print("\n[Step 3] Verify dependency injection (via fallback)...")
    try:
        # 访问注入的服务（应该触发回退）
        service = controller.test_service
        print(f"  ✓ Service injected via fallback: {service}")
        
        # 调用方法
        data = controller.get_test_data()
        print(f"  ✓ Method call successful: {data}")
        
        assert data == "test data", "Should get correct data"
        return True
        
    except Exception as e:
        print(f"  ✗ Fallback injection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\nStarting fallback injection test...")
    
    try:
        success = test_fallback_injection()
        
        print("\n" + "="*60)
        if success:
            print("✓ Fallback mechanism works correctly!")
            print("="*60)
            sys.exit(0)
        else:
            print("✗ Fallback mechanism failed!")
            print("="*60)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

