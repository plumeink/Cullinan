#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Service 模块重命名验证脚本
快速验证重命名是否成功
"""

import sys

print("=" * 70)
print("🔍 Service 模块重命名验证")
print("=" * 70)

tests_passed = 0
tests_total = 0

def test(name):
    def decorator(func):
        def wrapper():
            global tests_passed, tests_total
            tests_total += 1
            try:
                func()
                tests_passed += 1
                print(f"✅ {name}")
                return True
            except Exception as e:
                print(f"❌ {name}: {e}")
                return False
        return wrapper
    return decorator


@test("导入 Service 基类")
def test_import_service():
    from cullinan import Service
    assert Service.__module__ == 'cullinan.service.base'


@test("导入 @service 装饰器")
def test_import_decorator():
    from cullinan import service
    assert callable(service)


@test("导入 ServiceRegistry")
def test_import_registry():
    from cullinan import ServiceRegistry
    assert ServiceRegistry.__module__ == 'cullinan.service.registry'


@test("导入辅助函数")
def test_import_helpers():
    from cullinan import get_service_registry, reset_service_registry
    assert callable(get_service_registry)
    assert callable(reset_service_registry)


@test("验证 service_new 不存在")
def test_no_service_new():
    try:
        import cullinan.service_new
        raise AssertionError("service_new should not exist")
    except (ImportError, ModuleNotFoundError):
        pass


@test("创建和使用 Service")
def test_use_service():
    from cullinan import Service, service, get_service_registry, reset_service_registry
    
    reset_service_registry()
    
    @service
    class TestService(Service):
        def test(self):
            return "works"
    
    registry = get_service_registry()
    registry.initialize_all()
    instance = registry.get_instance('TestService')
    assert instance.test() == "works"


@test("依赖注入")
def test_dependency_injection():
    from cullinan import Service, service, get_service_registry, reset_service_registry
    
    reset_service_registry()
    
    @service
    class ServiceA(Service):
        def get_value(self):
            return "A"
    
    @service(dependencies=['ServiceA'])
    class ServiceB(Service):
        def on_init(self):
            self.a = self.dependencies['ServiceA']
        
        def get_value(self):
            return f"B+{self.a.get_value()}"
    
    registry = get_service_registry()
    registry.initialize_all()
    b = registry.get_instance('ServiceB')
    assert b.get_value() == "B+A"


# 运行所有测试
print()
test_import_service()
test_import_decorator()
test_import_registry()
test_import_helpers()
test_no_service_new()
test_use_service()
test_dependency_injection()

# 输出结果
print()
print("=" * 70)
print(f"测试结果: {tests_passed}/{tests_total} 通过")
print("=" * 70)

if tests_passed == tests_total:
    print("✅ Service 模块重命名完全成功！")
    print()
    print("📦 新的导入方式:")
    print("   from cullinan import Service, service, ServiceRegistry")
    print()
    print("📚 相关文档:")
    print("   - SERVICE_RENAME_SUMMARY.md (总结)")
    print("   - SERVICE_MIGRATION_TEST_REPORT.md (详细测试报告)")
    print("   - SERVICE_RENAME_QUICKREF.md (快速参考)")
    print()
    sys.exit(0)
else:
    print(f"❌ {tests_total - tests_passed} 个测试失败")
    sys.exit(1)

