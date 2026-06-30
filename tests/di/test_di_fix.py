# -*- coding: utf-8 -*-
"""测试 ControllerRegistry 依赖注入修复

Author: Cullinan
"""

import pytest

pytestmark = pytest.mark.filterwarnings(
    "ignore::cullinan.core.semantic_rules.ComponentDiscoveryWarning"
)


def reset_all_registries():
    """重置所有注册表以便独立测试"""
    from cullinan.web.controller.registry import reset_controller_registry
    from cullinan.core.pending import PendingRegistry
    from cullinan.core import set_application_context

    reset_controller_registry()
    PendingRegistry.reset()
    set_application_context(None)


def test_controller_di():
    """测试 Controller 依赖注入"""
    reset_all_registries()

    from cullinan.core import (
        ApplicationContext, 
        set_application_context, 
        get_application_context, 
        service, 
        controller, 
        Inject
    )

    # 创建一个测试服务
    @service
    class TestService:
        def get_message(self):
            return 'Hello from TestService'

    # 创建一个测试控制器
    @controller(url='/test')
    class TestController:
        test_service: TestService = Inject()
        
        def test_method(self):
            return self.test_service.get_message()

    # 创建 ApplicationContext 并设置全局引用
    ctx = ApplicationContext()
    set_application_context(ctx)
    try:
        ctx.refresh()
        assert get_application_context() is not None
        assert ctx.is_refreshed is True

        from cullinan.web.controller.registry import get_controller_registry
        controller_registry = get_controller_registry()
        controller_registry.register('TestController', TestController, url_prefix='/test')

        instance = controller_registry.get_instance('TestController')

        assert isinstance(instance.test_service, Inject) is False
        assert hasattr(instance.test_service, 'get_message')
        assert instance.test_method() == 'Hello from TestService'
    finally:
        ctx.shutdown()
        reset_all_registries()


def test_multiple_services():
    """测试多个服务注入"""
    reset_all_registries()

    from cullinan.core import (
        ApplicationContext,
        set_application_context,
        service,
        controller,
        Inject
    )

    @service
    class ServiceA:
        def name(self):
            return 'ServiceA'

    @service
    class ServiceB:
        def name(self):
            return 'ServiceB'

    @controller(url='/multi')
    class MultiServiceController:
        service_a: ServiceA = Inject()
        service_b: ServiceB = Inject()

        def get_names(self):
            return f'{self.service_a.name()} + {self.service_b.name()}'

    # 新建 ApplicationContext
    ctx = ApplicationContext()
    set_application_context(ctx)
    try:
        ctx.refresh()

        from cullinan.web.controller.registry import get_controller_registry
        controller_registry = get_controller_registry()
        controller_registry.register('MultiServiceController', MultiServiceController, url_prefix='/multi')

        instance = controller_registry.get_instance('MultiServiceController')
        assert hasattr(instance.service_a, 'name')
        assert hasattr(instance.service_b, 'name')
        assert instance.get_names() == 'ServiceA + ServiceB'
    finally:
        ctx.shutdown()
        reset_all_registries()


def test_optional_injection():
    """测试可选依赖注入"""
    reset_all_registries()

    from cullinan.core import (
        ApplicationContext,
        set_application_context,
        service,
        controller,
        Inject
    )

    @service
    class ExistingService:
        def exists(self):
            return True

    # 注意：MissingService 没有被 @service 装饰，所以不会被注册
    class MissingService:
        pass

    @controller(url='/optional')
    class OptionalController:
        existing: ExistingService = Inject()
        missing: MissingService = Inject(required=False)  # 可选依赖

    ctx = ApplicationContext()
    set_application_context(ctx)
    try:
        ctx.refresh()

        from cullinan.web.controller.registry import get_controller_registry
        controller_registry = get_controller_registry()
        controller_registry.register('OptionalController', OptionalController, url_prefix='/optional')

        instance = controller_registry.get_instance('OptionalController')
        assert hasattr(instance.existing, 'exists')
        assert instance.missing is None
    finally:
        ctx.shutdown()
        reset_all_registries()
