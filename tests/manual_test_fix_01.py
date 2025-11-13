# -*- coding: utf-8 -*-
"""手动验证修复 #01: 子类注入元数据 MRO 查找"""

import sys
sys.path.insert(0, 'g:/pj/Cullinan')

from cullinan.core import (
    Inject,
    injectable,
    get_injection_registry,
    reset_injection_registry
)
from cullinan.core.registry import SimpleRegistry


class MockService:
    def __init__(self):
        self.name = "MockService"


def test_subclass_inherits_injection():
    """测试子类继承父类的注入声明"""
    print("测试: 子类继承父类的注入声明...")
    
    # 清理并设置
    reset_injection_registry()
    registry = get_injection_registry()
    
    service_registry = SimpleRegistry()
    service_registry.register('MockService', MockService())
    registry.add_provider_registry(service_registry)
    
    # 父类声明注入
    @injectable
    class BaseClass:
        service: MockService = Inject()
    
    # 子类不声明注入
    class SubClass(BaseClass):
        pass
    
    # 测试
    try:
        instance = SubClass()
        assert hasattr(instance, 'service'), "子类实例应该有 service 属性"
        assert isinstance(instance.service, MockService), "service 应该是 MockService 实例"
        print("[OK] 测试通过: 子类成功继承父类的注入")
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_level_inheritance():
    """测试多层继承"""
    print("\n测试: 多层继承...")
    
    reset_injection_registry()
    registry = get_injection_registry()
    
    service_registry = SimpleRegistry()
    service_registry.register('MockService', MockService())
    registry.add_provider_registry(service_registry)
    
    @injectable
    class GrandParent:
        service: MockService = Inject()
    
    class Parent(GrandParent):
        pass
    
    class Child(Parent):
        pass
    
    try:
        instance = Child()
        assert hasattr(instance, 'service'), "孙子类应该有 service 属性"
        assert isinstance(instance.service, MockService), "service 应该是 MockService 实例"
        print("[OK] 测试通过: 多层继承正常工作")
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_class_injection():
    """测试直接类注入（基准测试）"""
    print("\n测试: 直接类注入（基准）...")
    
    reset_injection_registry()
    registry = get_injection_registry()
    
    service_registry = SimpleRegistry()
    service_registry.register('MockService', MockService())
    registry.add_provider_registry(service_registry)
    
    @injectable
    class DirectClass:
        service: MockService = Inject()
    
    try:
        instance = DirectClass()
        assert hasattr(instance, 'service'), "应该有 service 属性"
        assert isinstance(instance.service, MockService), "service 应该是 MockService 实例"
        print("[OK] 测试通过: 直接注入正常工作")
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("验证修复 #01: 子类注入元数据 MRO 查找")
    print("=" * 70)
    
    results = []
    results.append(test_direct_class_injection())
    results.append(test_subclass_inherits_injection())
    results.append(test_multi_level_inheritance())
    
    print("\n" + "=" * 70)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 70)
    
    if all(results):
        print("\n[OK] 所有测试通过！修复 #01 验证成功。")
        sys.exit(0)
    else:
        print("\n[FAIL] 部分测试失败，需要修复。")
        sys.exit(1)

