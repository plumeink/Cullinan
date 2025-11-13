# -*- coding: utf-8 -*-
"""测试 Controller 无状态验证器

验证：
1. 有状态 Controller 会触发警告
2. 无状态 Controller 不会触发警告
3. 注入的依赖不会触发警告
4. 严格模式会抛出异常
"""

import pytest
import warnings
from cullinan.controller.core import controller, get_api, post_api
from cullinan.controller.stateless_validator import (
    validate_stateless_controller,
    StatefulControllerWarning,
    StatefulControllerError
)
from cullinan.core import InjectByName


class TestStatelessValidator:
    """测试无状态验证器"""

    def test_stateless_controller_no_warning(self):
        """测试：无状态 Controller 不触发警告"""

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @controller(url='/api/stateless')
            class StatelessController:
                """正确的无状态 Controller"""
                service = InjectByName('SomeService')  # 注入是安全的

                @get_api(url='/data')
                def get_data(self, query_params):
                    return {"data": "ok"}

            # 实例化 Controller
            instance = StatelessController()

            # 不应该有警告
            stateful_warnings = [warning for warning in w if issubclass(warning.category, StatefulControllerWarning)]
            assert len(stateful_warnings) == 0, "Stateless controller should not trigger warnings"

    def test_stateful_controller_triggers_warning(self):
        """测试：有状态 Controller 触发警告"""

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @controller(url='/api/stateful')
            class StatefulController:
                """错误的有状态 Controller"""

                def __init__(self):
                    self.current_user = None  # ❌ 这会触发警告
                    self.request_id = 0        # ❌ 这会触发警告

                @get_api(url='/data')
                def get_data(self):
                    return {"user": self.current_user}

            # 实例化 Controller（触发验证）
            instance = StatefulController()

            # 应该有警告
            stateful_warnings = [warning for warning in w if issubclass(warning.category, StatefulControllerWarning)]
            assert len(stateful_warnings) > 0, "Stateful controller should trigger warning"

            # 检查警告消息内容
            warning_message = str(stateful_warnings[0].message)
            assert 'STATEFUL' in warning_message
            assert 'current_user' in warning_message or 'request_id' in warning_message
            assert 'SINGLETON' in warning_message

    def test_injection_descriptors_allowed(self):
        """测试：注入描述符不会触发警告"""

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @controller(url='/api/inject')
            class InjectionController:
                """使用依赖注入的 Controller"""
                user_service = InjectByName('UserService')
                auth_service = InjectByName('AuthService')

                def __init__(self):
                    # 注入的属性不应该触发警告
                    pass

                @get_api(url='/data')
                def get_data(self):
                    return {"data": "ok"}

            # 实例化
            instance = InjectionController()

            # 不应该有警告
            stateful_warnings = [warning for warning in w if issubclass(warning.category, StatefulControllerWarning)]
            assert len(stateful_warnings) == 0

    def test_strict_mode_raises_exception(self):
        """测试：严格模式抛出异常"""

        class StrictStatefulController:
            def __init__(self):
                self.bad_state = "dangerous"

        # 应用严格验证
        StrictStatefulController = validate_stateless_controller(StrictStatefulController, strict=True)

        # 实例化应该抛出异常
        with pytest.raises(StatefulControllerError) as exc_info:
            instance = StrictStatefulController()

        # 检查异常消息
        assert 'STATEFUL' in str(exc_info.value)
        assert 'bad_state' in str(exc_info.value)

    def test_allowed_framework_attributes(self):
        """测试：框架管理的属性不触发警告"""

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @controller(url='/api/framework')
            class FrameworkController:
                def __init__(self):
                    # 这些是框架管理的属性，应该被允许
                    self.dependencies = {}
                    self.service = {}
                    self.response = None
                    self.response_factory = None

                @get_api(url='/data')
                def get_data(self):
                    return {"data": "ok"}

            instance = FrameworkController()

            # 不应该有警告
            stateful_warnings = [warning for warning in w if issubclass(warning.category, StatefulControllerWarning)]
            assert len(stateful_warnings) == 0

    def test_mixed_safe_and_unsafe(self):
        """测试：混合安全和不安全的属性"""

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @controller(url='/api/mixed')
            class MixedController:
                safe_injection = InjectByName('Service')

                def __init__(self):
                    self.dependencies = {}  # ✅ 框架管理
                    self.user_data = None   # ❌ 不安全

                @get_api(url='/data')
                def get_data(self):
                    return {"data": "ok"}

            instance = MixedController()

            # 应该有警告（针对 user_data）
            stateful_warnings = [warning for warning in w if issubclass(warning.category, StatefulControllerWarning)]
            assert len(stateful_warnings) > 0

            warning_message = str(stateful_warnings[0].message)
            assert 'user_data' in warning_message
            # 不应该包含 dependencies（因为它是允许的）
            # 不应该包含 safe_injection（因为它是注入描述符）


class TestStatelessValidatorIntegration:
    """集成测试：验证器与 @controller 装饰器集成"""

    def test_controller_decorator_applies_validation(self):
        """测试：@controller 装饰器自动应用验证"""

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 定义一个有状态的 Controller
            @controller(url='/api/test')
            class AutoValidatedController:
                def __init__(self):
                    self.problem = "This should trigger warning"

                @get_api(url='/test')
                def test_method(self):
                    return {"test": "ok"}

            # 实例化（验证器会在 __init__ 时检查）
            instance = AutoValidatedController()

            # 应该有警告
            stateful_warnings = [warning for warning in w if issubclass(warning.category, StatefulControllerWarning)]
            assert len(stateful_warnings) > 0


class TestValidatorDocumentation:
    """文档化测试：展示正确和错误的用法"""

    def test_correct_usage_example(self):
        """正确示例：无状态设计"""

        @controller(url='/api/users')
        class UserController:
            user_service = InjectByName('UserService')

            @get_api(url='/list')
            def list_users(self, query_params):
                # ✅ 请求数据通过参数传递
                page = query_params.get('page', 1)
                # ✅ 使用注入的 Service
                users = self.user_service.get_users(page)
                return {"users": users}

            @post_api(url='/create')
            def create_user(self, body_params):
                # ✅ 请求数据通过参数传递
                user_data = body_params
                user = self.user_service.create(user_data)
                return {"user": user}

        print("✅ Correct: Stateless controller with parameter passing")

    def test_incorrect_usage_example(self):
        """错误示例：有状态设计（会触发警告）"""

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            @controller(url='/api/bad')
            class BadController:
                def __init__(self):
                    self.current_user = None  # ❌ 错误：实例变量存储请求数据

                @post_api(url='/login')
                def login(self, body_params):
                    # ❌ 错误：将请求数据存入实例变量
                    self.current_user = body_params.get('user')
                    return {"status": "ok"}

                @get_api(url='/me')
                def get_me(self):
                    # ❌ 错误：从实例变量读取（并发问题）
                    return {"user": self.current_user}

            instance = BadController()

            # 确认触发了警告
            stateful_warnings = [warning for warning in w if issubclass(warning.category, StatefulControllerWarning)]
            assert len(stateful_warnings) > 0

            print("❌ Incorrect: Stateful controller (warning triggered)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

