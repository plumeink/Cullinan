# -*- coding: utf-8 -*-
"""测试构造器注入装饰器

验证 @inject_constructor 的各种使用场景
"""

import pytest
from cullinan.core import (
    inject_constructor, injectable, Inject,
    get_injection_registry, reset_injection_registry
)
from cullinan.core.registry import SimpleRegistry
from cullinan.core.exceptions import RegistryError


class ServiceA:
    """模拟服务 A"""
    def __init__(self):
        self.name = "ServiceA"


class ServiceB:
    """模拟服务 B"""
    def __init__(self):
        self.name = "ServiceB"


class Config:
    """模拟配置"""
    def __init__(self):
        self.value = "test_config"


def setup_function():
    """每个测试前重置"""
    reset_injection_registry()


def test_inject_constructor_basic():
    """测试：基本构造器注入"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    service_registry.register('ServiceA', service_a)

    @inject_constructor
    class Controller:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    controller = Controller()

    assert controller.service_a is service_a


def test_inject_constructor_multiple_params():
    """测试：多个参数注入"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    service_b = ServiceB()
    config = Config()

    service_registry.register('ServiceA', service_a)
    service_registry.register('ServiceB', service_b)
    service_registry.register('Config', config)

    @inject_constructor
    class Controller:
        def __init__(self, service_a: ServiceA, service_b: ServiceB, config: Config):
            self.service_a = service_a
            self.service_b = service_b
            self.config = config

    controller = Controller()

    assert controller.service_a is service_a
    assert controller.service_b is service_b
    assert controller.config is config


def test_inject_constructor_with_manual_args():
    """测试：部分参数手动传入，部分自动注入"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    service_registry.register('ServiceA', service_a)

    @inject_constructor
    class Controller:
        def __init__(self, name: str, service_a: ServiceA):
            self.name = name
            self.service_a = service_a

    controller = Controller("test_controller")

    assert controller.name == "test_controller"
    assert controller.service_a is service_a


def test_inject_constructor_optional_params():
    """测试：可选参数（有默认值）"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    service_registry.register('ServiceA', service_a)

    @inject_constructor
    class Controller:
        def __init__(self, service_a: ServiceA, service_b: ServiceB = None):
            self.service_a = service_a
            self.service_b = service_b

    # ServiceB 不存在，但有默认值，不应抛错
    controller = Controller()

    assert controller.service_a is service_a
    assert controller.service_b is None


def test_inject_constructor_required_missing():
    """测试：必需参数缺失时抛出错误"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    @inject_constructor
    class Controller:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    # ServiceA 未注册
    with pytest.raises(RegistryError) as exc_info:
        Controller()

    assert "Cannot inject required parameter" in str(exc_info.value)
    assert "service_a" in str(exc_info.value)
    assert "ServiceA" in str(exc_info.value)


def test_inject_constructor_with_kwargs():
    """测试：使用 kwargs 传参"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    service_registry.register('ServiceA', service_a)

    @inject_constructor
    class Controller:
        def __init__(self, service_a: ServiceA, name: str = "default"):
            self.service_a = service_a
            self.name = name

    controller = Controller(name="custom")

    assert controller.service_a is service_a
    assert controller.name == "custom"


def test_inject_constructor_mixed_with_injectable():
    """测试：与 @injectable 混合使用"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    service_b = ServiceB()
    config = Config()

    service_registry.register('ServiceA', service_a)
    service_registry.register('ServiceB', service_b)
    service_registry.register('Config', config)

    @inject_constructor
    @injectable
    class Controller:
        # 构造器注入
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

        # 属性注入
        service_b: ServiceB = Inject()
        config: Config = Inject()

    controller = Controller()

    assert controller.service_a is service_a
    assert controller.service_b is service_b
    assert controller.config is config


def test_inject_constructor_no_type_hints():
    """测试：没有类型提示的参数不注入"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    service_registry.register('ServiceA', service_a)

    @inject_constructor
    class Controller:
        def __init__(self, service_a: ServiceA, plain_param):
            self.service_a = service_a
            self.plain_param = plain_param

    # plain_param 没有类型提示，必须手动传入
    controller = Controller(plain_param="manual_value")

    assert controller.service_a is service_a
    assert controller.plain_param == "manual_value"


def test_inject_constructor_no_injectable_params():
    """测试：没有可注入参数时装饰器无操作"""

    @inject_constructor
    class Controller:
        def __init__(self, name: str):
            self.name = name

    # 应该正常工作，装饰器不影响
    controller = Controller("test")
    assert controller.name == "test"


def test_inject_constructor_override_injection():
    """测试：手动传参可以覆盖自动注入"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    manual_service = ServiceA()
    manual_service.name = "manual"

    service_registry.register('ServiceA', service_a)

    @inject_constructor
    class Controller:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    # 手动传入参数
    controller = Controller(service_a=manual_service)

    # 应该使用手动传入的实例
    assert controller.service_a is manual_service
    assert controller.service_a.name == "manual"


def test_inject_constructor_with_string_annotations():
    """测试：字符���类型注解（前向引用）"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    service_registry.register('ServiceA', service_a)

    @inject_constructor
    class Controller:
        def __init__(self, service_a: 'ServiceA'):
            self.service_a = service_a

    controller = Controller()

    assert controller.service_a is service_a


def test_inject_constructor_syntax_both_forms():
    """测试：两种装饰器语法都支持"""

    injection_registry = get_injection_registry()
    service_registry = SimpleRegistry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    service_a = ServiceA()
    service_registry.register('ServiceA', service_a)

    # 形式1：@inject_constructor
    @inject_constructor
    class Controller1:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    # 形式2：@inject_constructor()
    @inject_constructor()
    class Controller2:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    c1 = Controller1()
    c2 = Controller2()

    assert c1.service_a is service_a
    assert c2.service_a is service_a


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

