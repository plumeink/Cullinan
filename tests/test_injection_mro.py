# -*- coding: utf-8 -*-
"""测试 MRO-aware 注入元数据查找

验证子类能够继承基类声明的注入属性
"""

import pytest
from cullinan.core import (
    Inject, injectable, get_injection_registry, reset_injection_registry
)
from cullinan.core.registry import SimpleRegistry
from cullinan.core.exceptions import RegistryError


class MockService:
    """模拟服务"""
    def __init__(self, name):
        self.name = name


def setup_function():
    """每个测试前重置"""
    reset_injection_registry()


def test_subclass_inherits_base_injection():
    """测试：子类继承基类的注入声明"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_registry.register('ServiceA', MockService('A'))

    @injectable
    class BaseController:
        service_a: 'ServiceA' = Inject()

    class SubController(BaseController):
        pass

    sub_instance = SubController()

    assert hasattr(sub_instance, 'service_a')
    assert isinstance(sub_instance.service_a, MockService)
    assert sub_instance.service_a.name == 'A'


def test_multi_level_inheritance():
    """测试：多级继承场景"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_registry.register('ServiceA', MockService('A'))
    service_registry.register('ServiceB', MockService('B'))

    @injectable
    class GrandParent:
        service_a: 'ServiceA' = Inject()

    @injectable
    class Parent(GrandParent):
        service_b: 'ServiceB' = Inject()

    class Child(Parent):
        pass

    child = Child()

    assert hasattr(child, 'service_a')
    assert hasattr(child, 'service_b')
    assert child.service_a.name == 'A'
    assert child.service_b.name == 'B'


def test_required_dependency_inheritance():
    """测试：继承的必需依赖缺失时抛出错误"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    @injectable
    class BaseController:
        required_svc: 'RequiredService' = Inject(required=True)

    class SubController(BaseController):
        pass

    with pytest.raises(RegistryError) as exc_info:
        SubController()

    assert 'RequiredService' in str(exc_info.value)
    assert 'not found' in str(exc_info.value).lower()


def test_optional_dependency_inheritance():
    """测试：继承的可选依赖缺失时返回 None"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    @injectable
    class BaseController:
        optional_svc: 'OptionalService' = Inject(required=False)

    class SubController(BaseController):
        pass

    sub = SubController()

    assert hasattr(sub, 'optional_svc')
    assert sub.optional_svc is None


def test_subclass_override_injection():
    """测试：子类可以覆盖基类的注入声明"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_registry.register('ServiceA', MockService('A'))
    service_registry.register('ServiceB', MockService('B'))

    @injectable
    class BaseController:
        service: 'ServiceA' = Inject()

    @injectable
    class SubController(BaseController):
        service: 'ServiceB' = Inject()

    base = BaseController()
    sub = SubController()

    assert base.service.name == 'A'
    assert sub.service.name == 'B'


def test_mixed_required_optional_inheritance():
    """测试：混合必需/可选依赖继承"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_registry.register('Required', MockService('req'))

    @injectable
    class BaseController:
        required: 'Required' = Inject(required=True)
        optional: 'Optional' = Inject(required=False)

    class SubController(BaseController):
        pass

    sub = SubController()

    assert sub.required.name == 'req'
    assert sub.optional is None


def test_no_injection_without_provider():
    """测试：没有 provider registry 时不会注入但也不抛错"""

    reset_injection_registry()

    @injectable
    class TestController:
        service: 'Service' = Inject(required=False)

    instance = TestController()

    assert not hasattr(instance, 'service') or instance.service is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

