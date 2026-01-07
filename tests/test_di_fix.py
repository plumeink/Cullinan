# -*- coding: utf-8 -*-
"""测试 ControllerRegistry 依赖注入修复

Author: Plumeink
"""

import sys
sys.path.insert(0, '.')


def reset_all_registries():
    """重置所有注册表以便独立测试"""
    from cullinan.controller.registry import reset_controller_registry
    from cullinan.core.pending import PendingRegistry
    from cullinan.core import set_application_context

    reset_controller_registry()

    # 重置 PendingRegistry
    pending = PendingRegistry.get_instance()
    pending._registrations.clear()
    pending._frozen = False

    # 清除全局 ApplicationContext
    set_application_context(None)


def test_controller_di():
    """测试 Controller 依赖注入"""
    print("=" * 60)
    print("测试 1: 基础依赖注入")
    print("=" * 60)

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
    ctx.refresh()

    print(f'[OK] ApplicationContext created and refreshed')
    print(f'[OK] Global context set: {get_application_context() is not None}')
    print(f'[OK] Is refreshed: {ctx.is_refreshed}')

    # 测试通过 ControllerRegistry 获取实例
    from cullinan.controller.registry import get_controller_registry
    controller_registry = get_controller_registry()

    # 注册控制器
    controller_registry.register('TestController', TestController, url_prefix='/test')

    # 获取实例
    instance = controller_registry.get_instance('TestController')
    print(f'[OK] Controller instance created: {instance}')
    print(f'[INFO] test_service type: {type(instance.test_service).__name__}')

    is_inject_object = isinstance(instance.test_service, Inject)
    print(f'[INFO] test_service is Inject object: {is_inject_object}')

    # 如果注入成功，调用方法
    if hasattr(instance.test_service, 'get_message'):
        message = instance.test_service.get_message()
        print(f'[OK] Message: {message}')
        print('[SUCCESS] Test 1 passed: Dependency injection works!')
        return True
    else:
        print('[FAILED] Test 1 failed: Dependency injection did not work')
        print(f'[DEBUG] instance.test_service = {instance.test_service}')
        print(f'[DEBUG] type = {type(instance.test_service)}')
        return False


def test_multiple_services():
    """测试多个服务注入"""
    print("\n" + "=" * 60)
    print("测试 2: 多服务依赖注入")
    print("=" * 60)

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
    ctx.refresh()

    from cullinan.controller.registry import get_controller_registry
    controller_registry = get_controller_registry()
    controller_registry.register('MultiServiceController', MultiServiceController, url_prefix='/multi')

    instance = controller_registry.get_instance('MultiServiceController')

    # 检查所有服务是否正确注入
    a_ok = hasattr(instance.service_a, 'name')
    b_ok = hasattr(instance.service_b, 'name')

    print(f'[INFO] service_a injected correctly: {a_ok}')
    print(f'[INFO] service_b injected correctly: {b_ok}')

    if a_ok and b_ok:
        result = instance.get_names()
        print(f'[OK] Combined result: {result}')
        print('[SUCCESS] Test 2 passed: Multiple service injection works!')
        return True
    else:
        print('[FAILED] Test 2 failed')
        return False


def test_optional_injection():
    """测试可选依赖注入"""
    print("\n" + "=" * 60)
    print("测试 3: 可选依赖注入 (required=False)")
    print("=" * 60)

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
    ctx.refresh()

    from cullinan.controller.registry import get_controller_registry
    controller_registry = get_controller_registry()
    controller_registry.register('OptionalController', OptionalController, url_prefix='/optional')

    instance = controller_registry.get_instance('OptionalController')

    existing_ok = hasattr(instance.existing, 'exists')
    missing_is_none = instance.missing is None

    print(f'[INFO] existing service injected: {existing_ok}')
    print(f'[INFO] missing service is None: {missing_is_none}')

    if existing_ok and missing_is_none:
        print('[SUCCESS] Test 3 passed: Optional injection works!')
        return True
    else:
        print('[FAILED] Test 3 failed')
        return False


if __name__ == '__main__':
    results = []

    results.append(test_controller_di())
    results.append(test_multiple_services())
    results.append(test_optional_injection())

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f'通过: {passed}/{total}')

    sys.exit(0 if all(results) else 1)

