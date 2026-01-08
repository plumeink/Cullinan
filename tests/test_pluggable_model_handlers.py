# -*- coding: utf-8 -*-
"""可插拔模型处理器测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataclasses import dataclass
from typing import Optional


def test_registry_basic():
    """测试注册表基本功能"""
    print("1. 测试注册表基本功能...")

    from cullinan.params.model_handlers import (
        get_model_handler_registry,
        reset_model_handler_registry,
        DataclassHandler,
    )

    # 重置注册表
    reset_model_handler_registry()

    # 获取注册表
    registry = get_model_handler_registry()

    # 检查自动发现
    handlers = registry.get_handler_names()
    assert 'dataclass' in handlers, f"Expected 'dataclass' in {handlers}"

    print(f"   已注册的处理器: {handlers}")
    print("   基本功能测试通过")
    return True


def test_dataclass_handler():
    """测试 dataclass 处理器"""
    print("2. 测试 dataclass 处理器...")

    from cullinan.params.model_handlers import (
        get_model_handler_registry,
        reset_model_handler_registry,
    )

    reset_model_handler_registry()
    registry = get_model_handler_registry()

    @dataclass
    class User:
        name: str
        age: int = 0
        email: Optional[str] = None

    # 检查可处理
    handler = registry.get_handler(User)
    assert handler is not None
    assert handler.name == 'dataclass'

    # 测试解析
    data = {'name': 'John', 'age': '25', 'email': 'john@example.com'}
    user = handler.resolve(User, data)

    assert user.name == 'John'
    assert user.age == 25
    assert user.email == 'john@example.com'

    # 测试 to_dict
    result = handler.to_dict(user)
    assert result['name'] == 'John'
    assert result['age'] == 25

    print("   dataclass 处理器测试通过")
    return True


def test_param_resolver_with_dataclass():
    """测试 ParamResolver 使用注册表"""
    print("3. 测试 ParamResolver 使用模型处理器...")

    from cullinan.params import ParamResolver
    from cullinan.params.model_handlers import reset_model_handler_registry

    reset_model_handler_registry()

    @dataclass
    class CreateUserRequest:
        name: str
        age: int = 0

    def handler(self, user: CreateUserRequest):
        pass

    # 分析参数
    config = ParamResolver.analyze_params(handler)

    assert 'user' in config
    assert config['user']['source'] == 'body'
    assert config['user'].get('model_handler') is not None
    assert config['user']['model_handler'].name == 'dataclass'

    print("   ParamResolver 模型处理器集成测试通过")
    return True


def test_custom_handler():
    """测试自定义处理器注册"""
    print("4. 测试自定义处理器注册...")

    from cullinan.params.model_handlers import (
        ModelHandler,
        ModelHandlerError,
        get_model_handler_registry,
        reset_model_handler_registry,
    )

    reset_model_handler_registry()

    # 创建自定义处理器
    class CustomModel:
        """自定义模型类"""
        def __init__(self, data):
            self.data = data

    class CustomHandler(ModelHandler):
        priority = 100  # 高优先级
        name = "custom"

        def can_handle(self, type_):
            return type_ is CustomModel

        def resolve(self, model_class, data):
            return CustomModel(data)

        def to_dict(self, instance):
            return instance.data

    # 注册自定义处理器
    registry = get_model_handler_registry()
    registry.register(CustomHandler())

    # 检查注册
    assert 'custom' in registry.get_handler_names()

    # 检查优先级（custom 应该在最前面）
    handlers = registry.handlers
    assert handlers[0].name == 'custom'

    # 测试解析
    handler = registry.get_handler(CustomModel)
    assert handler.name == 'custom'

    instance = handler.resolve(CustomModel, {'key': 'value'})
    assert instance.data == {'key': 'value'}

    print("   自定义处理器测试通过")
    return True


def test_pydantic_handler_optional():
    """测试 Pydantic 处理器（可选）"""
    print("5. 测试 Pydantic 处理器...")

    from cullinan.params.model_handlers import (
        get_model_handler_registry,
        reset_model_handler_registry,
    )

    reset_model_handler_registry()
    registry = get_model_handler_registry()

    handlers = registry.get_handler_names()

    if 'pydantic' in handlers:
        print("   Pydantic 已安装，测试 Pydantic 处理器...")

        from pydantic import BaseModel

        class PydanticUser(BaseModel):
            name: str
            age: int = 0

        handler = registry.get_handler(PydanticUser)
        assert handler is not None
        assert handler.name == 'pydantic'

        # 测试解析
        data = {'name': 'Jane', 'age': 30}
        user = handler.resolve(PydanticUser, data)

        assert user.name == 'Jane'
        assert user.age == 30

        print("   Pydantic 处理器测试通过")
    else:
        print("   Pydantic 未安装，跳过 Pydantic 测试")

    return True


def test_handler_priority():
    """测试处理器优先级"""
    print("6. 测试处理器优先级...")

    from cullinan.params.model_handlers import (
        get_model_handler_registry,
        reset_model_handler_registry,
    )

    reset_model_handler_registry()
    registry = get_model_handler_registry()

    handlers = registry.handlers

    # 检查优先级排序（降序）
    for i in range(len(handlers) - 1):
        assert handlers[i].priority >= handlers[i+1].priority, \
            f"Handler priority not sorted: {handlers[i].name}({handlers[i].priority}) < {handlers[i+1].name}({handlers[i+1].priority})"

    print(f"   处理器优先级顺序: {[(h.name, h.priority) for h in handlers]}")
    print("   处理器优先级测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("可插拔模型处理器架构测试")
    print("=" * 60)
    print()

    tests = [
        test_registry_basic,
        test_dataclass_handler,
        test_param_resolver_with_dataclass,
        test_custom_handler,
        test_pydantic_handler_optional,
        test_handler_priority,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

