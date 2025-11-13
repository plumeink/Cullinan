# -*- coding: utf-8 -*-
"""测试修复 #01: 子类注入元数据 MRO 查找

验证子类能够继承父类声明的注入。
"""

import pytest
from cullinan.core import (
    Inject,
    injectable,
    InjectionRegistry,
    get_injection_registry,
    reset_injection_registry
)
from cullinan.core.registry import SimpleRegistry
from cullinan.core.exceptions import RegistryError


class MockService:
    """模拟服务"""
    def __init__(self, name="MockService"):
        self.name = name


class AnotherService:
    """另一个模拟服务"""
    def __init__(self, name="AnotherService"):
        self.name = name


@pytest.fixture
def clean_registry():
    """每个测试前清理注入注册表"""
    reset_injection_registry()
    yield get_injection_registry()
    reset_injection_registry()


@pytest.fixture
def service_registry():
    """提供服务的注册表"""
    registry = SimpleRegistry()
    registry.register('MockService', MockService())
    registry.register('AnotherService', AnotherService())
    return registry


class TestMROMetadataLookup:
    """测试 MRO 元数据查找"""

    def test_direct_class_injection(self, clean_registry, service_registry):
        """测试直接类注入（基准测试）"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class DirectClass:
            service: MockService = Inject()

        instance = DirectClass()
        assert hasattr(instance, 'service')
        assert isinstance(instance.service, MockService)

    def test_subclass_inherits_injection_from_parent(self, clean_registry, service_registry):
        """测试子类继承父类的注入声明"""
        clean_registry.add_provider_registry(service_registry)

        # 父类声明注入
        @injectable
        class BaseClass:
            service: MockService = Inject()

        # 子类不声明注入
        class SubClass(BaseClass):
            pass

        # 子类实例应该能够获得注入
        instance = SubClass()
        assert hasattr(instance, 'service')
        assert isinstance(instance.service, MockService)
        assert instance.service.name == "MockService"

    def test_multi_level_inheritance(self, clean_registry, service_registry):
        """测试多层继承"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class GrandParent:
            service: MockService = Inject()

        class Parent(GrandParent):
            pass

        class Child(Parent):
            pass

        instance = Child()
        assert hasattr(instance, 'service')
        assert isinstance(instance.service, MockService)

    def test_subclass_overrides_injection(self, clean_registry, service_registry):
        """测试子类覆盖父类的注入"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class BaseClass:
            service: MockService = Inject()

        # 子类自己声明注入（应该优先使用子类的）
        @injectable
        class SubClass(BaseClass):
            service: AnotherService = Inject()

        instance = SubClass()
        # 应该注入 AnotherService 而不是 MockService
        assert hasattr(instance, 'service')
        assert isinstance(instance.service, AnotherService)

    def test_mixed_injection_inheritance(self, clean_registry, service_registry):
        """测试混合注入继承（父类和子类都有注入）"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class BaseClass:
            service: MockService = Inject()

        @injectable
        class SubClass(BaseClass):
            another: AnotherService = Inject()

        instance = SubClass()
        # 应该同时有两个注入
        assert hasattr(instance, 'service')
        assert hasattr(instance, 'another')
        assert isinstance(instance.service, MockService)
        assert isinstance(instance.another, AnotherService)

    def test_no_parent_metadata(self, clean_registry, service_registry):
        """测试父类没有注入元数据的情况"""
        clean_registry.add_provider_registry(service_registry)

        # 父类没有注入
        class BaseClass:
            pass

        # 子类有注入
        @injectable
        class SubClass(BaseClass):
            service: MockService = Inject()

        instance = SubClass()
        assert hasattr(instance, 'service')
        assert isinstance(instance.service, MockService)

    def test_mro_with_multiple_inheritance(self, clean_registry, service_registry):
        """测试多重继承的 MRO 查找"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class Mixin1:
            service: MockService = Inject()

        class Mixin2:
            pass

        # 多重继承
        class Combined(Mixin2, Mixin1):
            pass

        instance = Combined()
        # 应该从 Mixin1 继承注入
        assert hasattr(instance, 'service')
        assert isinstance(instance.service, MockService)

    def test_optional_dependency_inheritance(self, clean_registry):
        """测试可选依赖的继承"""
        # 不添加 provider registry，导致依赖无法解析

        @injectable
        class BaseClass:
            service: MockService = Inject(required=False)

        class SubClass(BaseClass):
            pass

        # 应该不抛出异常，且 service 为 None
        instance = SubClass()
        # 注意：Inject 描述符会返回 None，但不会设置属性
        assert not hasattr(instance, 'service') or instance.service is None

    def test_required_dependency_inheritance_fails(self, clean_registry):
        """测试必需依赖的继承（失败情况）"""
        # 不添加 provider registry

        @injectable
        class BaseClass:
            service: MockService = Inject(required=True)

        class SubClass(BaseClass):
            pass

        # 应该抛出 RegistryError
        with pytest.raises(RegistryError):
            instance = SubClass()

    def test_mro_search_stops_at_first_match(self, clean_registry, service_registry):
        """测试 MRO 搜索在第一个匹配处停止"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class GrandParent:
            service: MockService = Inject()

        @injectable
        class Parent(GrandParent):
            another: AnotherService = Inject()

        class Child(Parent):
            pass

        instance = Child()
        # 应该从 Parent 获取元数据（第一个匹配）
        # 因此同时有 service 和 another
        assert hasattr(instance, 'service')
        assert hasattr(instance, 'another')


class TestMROEdgeCases:
    """测试 MRO 边界情况"""

    def test_empty_mro(self, clean_registry, service_registry):
        """测试没有父类的情况"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class StandaloneClass:
            service: MockService = Inject()

        instance = StandaloneClass()
        assert hasattr(instance, 'service')

    def test_object_in_mro(self, clean_registry, service_registry):
        """测试 MRO 包含 object 的情况"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class BaseClass(object):
            service: MockService = Inject()

        class SubClass(BaseClass):
            pass

        instance = SubClass()
        assert hasattr(instance, 'service')

    def test_no_metadata_in_entire_mro(self, clean_registry, service_registry):
        """测试整个 MRO 链都没有元数据"""
        clean_registry.add_provider_registry(service_registry)

        class A:
            pass

        class B(A):
            pass

        class C(B):
            pass

        # 不应该抛出异常，注入应该直接返回
        instance = C()
        # 验证 inject 被调用但没有做任何事
        clean_registry.inject(instance)


class TestMROPerformance:
    """测试 MRO 查找的性能"""

    def test_mro_lookup_caches_result(self, clean_registry, service_registry):
        """测试 MRO 查找结果被缓存"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class BaseClass:
            service: MockService = Inject()

        class SubClass(BaseClass):
            pass

        # 第一次注入
        instance1 = SubClass()
        # 第二次注入应该使用缓存的服务实例
        instance2 = SubClass()

        # 两个实例应该得到相同的服务实例（因为 SimpleRegistry 返回同一个）
        assert instance1.service is instance2.service

    def test_deep_mro_chain(self, clean_registry, service_registry):
        """测试深层 MRO 链的性能"""
        clean_registry.add_provider_registry(service_registry)

        @injectable
        class L0:
            service: MockService = Inject()

        # 创建 10 层继承
        current = L0
        for i in range(1, 11):
            current = type(f'L{i}', (current,), {})

        DeepClass = current

        # 应该能够找到并注入
        instance = DeepClass()
        assert hasattr(instance, 'service')
        assert isinstance(instance.service, MockService)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

