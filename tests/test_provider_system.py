# -*- coding: utf-8 -*-
"""测试 Provider/Binding 抽象系统

验证 InstanceProvider, ClassProvider, FactoryProvider, ScopedProvider
"""

import pytest
from cullinan.core import (
    Provider, InstanceProvider, ClassProvider, FactoryProvider,
    ScopedProvider, ProviderRegistry,
    SingletonScope, TransientScope, get_singleton_scope
)


class MockService:
    """模拟服务类"""
    instance_count = 0

    def __init__(self, name="default"):
        self.name = name
        MockService.instance_count += 1
        self.id = MockService.instance_count

    def __repr__(self):
        return f"MockService({self.name}, id={self.id})"


def setup_function():
    """每个测试前重置计数器"""
    MockService.instance_count = 0


def test_instance_provider():
    """测试：InstanceProvider 直接返回实例"""

    service = MockService("test")
    provider = InstanceProvider(service)

    assert provider.is_singleton()
    assert provider.get() is service
    assert provider.get() is service  # 始终返回同一个实例


def test_instance_provider_rejects_none():
    """测试：InstanceProvider 拒绝 None"""

    with pytest.raises(ValueError) as exc_info:
        InstanceProvider(None)

    assert "cannot be None" in str(exc_info.value).lower()


def test_class_provider_singleton():
    """测试：ClassProvider 单例模式"""

    provider = ClassProvider(MockService, singleton=True)

    assert provider.is_singleton()

    s1 = provider.get()
    s2 = provider.get()

    assert isinstance(s1, MockService)
    assert s1 is s2  # 同一个实例
    assert MockService.instance_count == 1


def test_class_provider_transient():
    """测试：ClassProvider 瞬时模式"""

    provider = ClassProvider(MockService, singleton=False)

    assert not provider.is_singleton()

    s1 = provider.get()
    s2 = provider.get()

    assert isinstance(s1, MockService)
    assert isinstance(s2, MockService)
    assert s1 is not s2  # 不同实例
    assert MockService.instance_count == 2


def test_class_provider_requires_type():
    """测试：ClassProvider 要求传入类型"""

    with pytest.raises(TypeError) as exc_info:
        ClassProvider("not a class")

    assert "Expected type" in str(exc_info.value)


def test_factory_provider_singleton():
    """测试：FactoryProvider 单例模式"""

    provider = FactoryProvider(
        lambda: MockService("factory"),
        singleton=True
    )

    assert provider.is_singleton()

    s1 = provider.get()
    s2 = provider.get()

    assert s1 is s2
    assert s1.name == "factory"
    assert MockService.instance_count == 1


def test_factory_provider_transient():
    """测试：FactoryProvider 瞬时模式"""

    provider = FactoryProvider(
        lambda: MockService("factory"),
        singleton=False
    )

    assert not provider.is_singleton()

    s1 = provider.get()
    s2 = provider.get()

    assert s1 is not s2
    assert MockService.instance_count == 2


def test_factory_provider_requires_callable():
    """测试：FactoryProvider 要求可调用对象"""

    with pytest.raises(TypeError) as exc_info:
        FactoryProvider("not callable")

    assert "must be callable" in str(exc_info.value).lower()


def test_scoped_provider_singleton():
    """测试：ScopedProvider 与 SingletonScope"""

    scope = SingletonScope()
    provider = ScopedProvider(
        lambda: MockService("scoped"),
        scope,
        "test_service"
    )

    assert provider.is_singleton()

    s1 = provider.get()
    s2 = provider.get()

    assert s1 is s2
    assert MockService.instance_count == 1


def test_scoped_provider_transient():
    """测试：ScopedProvider 与 TransientScope"""

    scope = TransientScope()
    provider = ScopedProvider(
        lambda: MockService("scoped"),
        scope,
        "test_service"
    )

    assert not provider.is_singleton()

    s1 = provider.get()
    s2 = provider.get()

    assert s1 is not s2
    assert MockService.instance_count == 2


def test_scoped_provider_validation():
    """测试：ScopedProvider 参数验证"""

    scope = get_singleton_scope()

    # 工厂不可调用
    with pytest.raises(TypeError):
        ScopedProvider("not callable", scope, "key")

    # Scope 为 None
    with pytest.raises(ValueError):
        ScopedProvider(lambda: None, None, "key")

    # Key 为空
    with pytest.raises(ValueError):
        ScopedProvider(lambda: None, scope, "")


def test_provider_registry_register():
    """测试：ProviderRegistry 注册"""

    registry = ProviderRegistry()
    service = MockService("test")
    provider = InstanceProvider(service)

    registry.register_provider("test_service", provider)

    assert registry.has_provider("test_service")
    assert registry.get_provider("test_service") is provider
    assert registry.count() == 1


def test_provider_registry_register_instance():
    """测试：ProviderRegistry 快捷注册实例"""

    registry = ProviderRegistry()
    service = MockService("test")

    registry.register_instance("test_service", service)

    retrieved = registry.get_instance("test_service")
    assert retrieved is service


def test_provider_registry_register_class():
    """测试：ProviderRegistry 快捷注册类"""

    registry = ProviderRegistry()

    registry.register_class("test_service", MockService, singleton=True)

    s1 = registry.get_instance("test_service")
    s2 = registry.get_instance("test_service")

    assert s1 is s2
    assert isinstance(s1, MockService)


def test_provider_registry_register_factory():
    """测试：ProviderRegistry 快捷注册工厂"""

    registry = ProviderRegistry()

    registry.register_factory(
        "test_service",
        lambda: MockService("factory"),
        singleton=False
    )

    s1 = registry.get_instance("test_service")
    s2 = registry.get_instance("test_service")

    assert s1 is not s2


def test_provider_registry_unregister():
    """测试：ProviderRegistry 取消注册"""

    registry = ProviderRegistry()
    registry.register_instance("test", MockService("test"))

    assert registry.unregister("test")
    assert not registry.has_provider("test")
    assert not registry.unregister("test")  # 再次删除返回 False


def test_provider_registry_clear():
    """测试：ProviderRegistry 清空"""

    registry = ProviderRegistry()
    registry.register_instance("s1", MockService("1"))
    registry.register_instance("s2", MockService("2"))

    assert registry.count() == 2

    registry.clear()

    assert registry.count() == 0
    assert not registry.has_provider("s1")


def test_provider_registry_list_names():
    """测试：ProviderRegistry 列出名称"""

    registry = ProviderRegistry()
    registry.register_instance("service1", MockService("1"))
    registry.register_instance("service2", MockService("2"))

    names = registry.list_names()

    assert len(names) == 2
    assert "service1" in names
    assert "service2" in names


def test_provider_registry_get_nonexistent():
    """测试：获取不存在的 Provider 返回 None"""

    registry = ProviderRegistry()

    assert registry.get_provider("nonexistent") is None
    assert registry.get_instance("nonexistent") is None


def test_provider_registry_replace_warning():
    """测试：重复注册会警告并替换"""

    registry = ProviderRegistry()
    s1 = MockService("first")
    s2 = MockService("second")

    registry.register_instance("test", s1)
    registry.register_instance("test", s2)

    # 应该是第二个实例
    assert registry.get_instance("test") is s2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

