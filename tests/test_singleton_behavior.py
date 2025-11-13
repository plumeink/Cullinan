# -*- coding: utf-8 -*-
"""测试 Controller 和 Service 的单例行为

验证：
1. Service 是单例（每个 Service 类只有一个实例）
2. Controller 是单例（每个 Controller 类只有一个实例）
3. 多次请求使用同一个 Controller 实例
4. Controller 的依赖注入正常工作
"""

import pytest
from cullinan.controller.registry import get_controller_registry
from cullinan.service.registry import get_service_registry
from cullinan.service.base import Service
from cullinan.controller.core import controller, get_api
from cullinan.core import InjectByName, get_injection_registry


class TestService(Service):
    """测试用 Service"""

    def __init__(self):
        super().__init__()
        self.init_count = 0
        self.call_count = 0

    def on_init(self):
        self.init_count += 1

    def do_something(self):
        self.call_count += 1
        return f"Service called {self.call_count} times"


class TestSingletonBehavior:
    """测试单例行为"""

    def setup_method(self):
        """每个测试前清理注册表"""
        # 清理 Injection 注册表（会清除所有 provider）
        injection_registry = get_injection_registry()
        injection_registry.clear()

        # 清理 Service 注册表
        service_registry = get_service_registry()
        service_registry.clear()
        service_registry._instances.clear()
        service_registry._initialized.clear()

        # 清理 Controller 注册表
        controller_registry = get_controller_registry()
        controller_registry.clear()
        controller_registry._controller_instances.clear()

        # 重新注册 ServiceRegistry 和 ControllerRegistry 为 providers
        # 因为 clear() 清除了 provider 列表
        injection_registry.add_provider_registry(service_registry, priority=10)
        injection_registry.add_provider_registry(controller_registry, priority=5)

        # 注册 Service
        from cullinan.service.decorators import service
        service_cls = service(TestService)

        # 初始化 Service
        service_registry.initialize_all()

        # 注册 TestController（在清理后重新注册）
        @controller(url='/test')
        class TestController:
            """测试用 Controller"""
            test_service = InjectByName('TestService')

            def __init__(self):
                self.init_count = 0
                self.request_count = 0

            @get_api(url='/action')
            def do_action(self):
                self.request_count += 1
                result = self.test_service.do_something()
                return {
                    "controller_init": self.init_count,
                    "controller_requests": self.request_count,
                    "service_result": result
                }

        # 保存 Controller 类供测试使用
        self.TestController = TestController

    def test_service_is_singleton(self):
        """测试：Service 是单例"""
        service_registry = get_service_registry()

        # 多次获取应该返回同一个实例
        instance1 = service_registry.get_instance('TestService')
        instance2 = service_registry.get_instance('TestService')
        instance3 = service_registry.get_instance('TestService')

        # 验证是同一个对象
        assert instance1 is instance2
        assert instance2 is instance3

        # 验证 on_init 只调用一次
        assert instance1.init_count == 1

    def test_controller_is_singleton(self):
        """测试：Controller 是单例"""
        controller_registry = get_controller_registry()

        # 多次获取应该返回同一个实例
        instance1 = controller_registry.get_instance('TestController')
        instance2 = controller_registry.get_instance('TestController')
        instance3 = controller_registry.get_instance('TestController')

        # 验证是同一个对象
        assert instance1 is not None
        assert instance1 is instance2
        assert instance2 is instance3

        # 验证是同一个 Python 对象
        assert id(instance1) == id(instance2) == id(instance3)

    def test_controller_dependency_injection(self):
        """测试：Controller 的依赖注入正常工作"""
        controller_registry = get_controller_registry()
        service_registry = get_service_registry()

        # 获取 Controller 实例
        controller = controller_registry.get_instance('TestController')
        assert controller is not None

        # 验证 Service 被注入
        assert hasattr(controller, 'test_service')
        assert controller.test_service is not None

        # 验证注入的是单例 Service
        service_instance = service_registry.get_instance('TestService')
        assert controller.test_service is service_instance

    def test_multiple_requests_share_same_controller(self):
        """测试：多个请求共享同一个 Controller 实例"""
        controller_registry = get_controller_registry()

        # 模拟多次请求
        controller1 = controller_registry.get_instance('TestController')
        controller1.request_count = 1

        controller2 = controller_registry.get_instance('TestController')
        controller2.request_count = 2

        controller3 = controller_registry.get_instance('TestController')

        # 验证是同一个实例
        assert controller1 is controller2 is controller3

        # 验证状态被共享（这说明 Controller 必须设计为无状态）
        assert controller3.request_count == 2

        print("⚠️ Warning: Controller is stateful, this demonstrates why it must be stateless!")

    def test_service_state_is_shared(self):
        """测试：Service 状态在所有请求间共享"""
        service_registry = get_service_registry()

        service = service_registry.get_instance('TestService')

        # 第一次调用
        result1 = service.do_something()
        assert "called 1 times" in result1

        # 第二次调用（使用同一个实例）
        result2 = service.do_something()
        assert "called 2 times" in result2

        # 验证计数器累加
        assert service.call_count == 2

    def test_thread_safety_service(self):
        """测试：Service 单例的线程安全性"""
        import threading
        service_registry = get_service_registry()

        instances = []

        def get_service():
            instance = service_registry.get_instance('TestService')
            instances.append(instance)

        # 创建多个线程同时获取 Service
        threads = [threading.Thread(target=get_service) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证所有线程获取的是同一个实例
        assert len(instances) == 10
        first_instance = instances[0]
        for instance in instances:
            assert instance is first_instance

    def test_thread_safety_controller(self):
        """测试：Controller 单例的线程安全性"""
        import threading
        controller_registry = get_controller_registry()

        instances = []

        def get_controller():
            instance = controller_registry.get_instance('TestController')
            instances.append(instance)

        # 创建多个线程同时获取 Controller
        threads = [threading.Thread(target=get_controller) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证所有线程获取的是同一个实例
        assert len(instances) == 10
        first_instance = instances[0]
        for instance in instances:
            assert instance is first_instance


class TestStatelessControllerDesign:
    """测试无状态 Controller 设计指南"""

    def test_correct_stateless_controller(self):
        """演示：正确的无状态 Controller 设计"""

        @controller(url='/api/stateless')
        class StatelessController:
            service = InjectByName('SomeService')

            @get_api(url='/data')
            def get_data(self, query_params):
                # ✅ 正确：不使用实例变量存储请求数据
                user_id = query_params.get('user_id')
                # ✅ 正确：请求数据通过参数传递
                result = self.service.get_data(user_id)
                return {"result": result}

        print("✅ Stateless Controller: Data passed via parameters")

    def test_incorrect_stateful_controller(self):
        """演示：错误的有状态 Controller 设计"""

        @controller(url='/api/stateful')
        class StatefulController:
            def __init__(self):
                self.current_user = None  # ❌ 错误：在实例变量存储请求数据

            @get_api(url='/login')
            def login(self, body_params):
                # ❌ 错误：请求数据存储在实例变量
                self.current_user = body_params.get('user')
                return {"status": "logged in"}

            @get_api(url='/me')
            def get_me(self):
                # ❌ 错误：从实例变量读取请求数据（并发会出问题）
                return {"user": self.current_user}

        print("❌ Stateful Controller: Will cause race conditions!")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

