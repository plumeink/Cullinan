# -*- coding: utf-8 -*-
"""测试 SimpleRegistry 的重复注册策略

验证 error/warn/replace 三种策略的行为
"""

import pytest
from cullinan.core.registry import SimpleRegistry
from cullinan.core.exceptions import RegistryError


def test_duplicate_policy_error():
    """测试：error 策略在重复注册时抛出异常"""

    registry = SimpleRegistry(duplicate_policy='error')

    registry.register('item1', 'value1')

    with pytest.raises(RegistryError) as exc_info:
        registry.register('item1', 'value2')

    assert 'already registered' in str(exc_info.value).lower()

    # 验证原值未被修改
    assert registry.get('item1') == 'value1'


def test_duplicate_policy_warn():
    """测试：warn 策略在重复注册时记录警告并跳过"""

    registry = SimpleRegistry(duplicate_policy='warn')

    registry.register('item1', 'value1')

    # 不应抛出异常
    registry.register('item1', 'value2')

    # 验证原值未被修改（保持第一次注册的值）
    assert registry.get('item1') == 'value1'


def test_duplicate_policy_replace():
    """测试：replace 策略会替换已存在的项"""

    registry = SimpleRegistry(duplicate_policy='replace')

    registry.register('item1', 'value1')
    registry.register('item1', 'value2')

    # 验证值已被替换
    assert registry.get('item1') == 'value2'


def test_default_policy_is_warn():
    """测试：默认策略是 warn（向后兼容）"""

    registry = SimpleRegistry()

    registry.register('item1', 'value1')
    registry.register('item1', 'value2')

    # 默认应该保持第一次注册的值
    assert registry.get('item1') == 'value1'


def test_invalid_policy_raises_error():
    """测试：无效的策略参数会抛出 ValueError"""

    with pytest.raises(ValueError) as exc_info:
        SimpleRegistry(duplicate_policy='invalid')

    assert 'Invalid duplicate_policy' in str(exc_info.value)
    assert 'error' in str(exc_info.value)
    assert 'warn' in str(exc_info.value)
    assert 'replace' in str(exc_info.value)


def test_duplicate_policy_with_metadata():
    """测试：重复注册策略与元数据的交互"""

    # error 策略
    registry_error = SimpleRegistry(duplicate_policy='error')
    registry_error.register('item1', 'value1', meta='old')

    with pytest.raises(RegistryError):
        registry_error.register('item1', 'value2', meta='new')

    assert registry_error.get_metadata('item1') == {'meta': 'old'}

    # replace 策略
    registry_replace = SimpleRegistry(duplicate_policy='replace')
    registry_replace.register('item1', 'value1', meta='old')
    registry_replace.register('item1', 'value2', meta='new')

    assert registry_replace.get('item1') == 'value2'
    assert registry_replace.get_metadata('item1') == {'meta': 'new'}


def test_duplicate_policy_with_hooks():
    """测试：重复注册策略与 hooks 的交互"""

    pre_calls = []
    post_calls = []

    def pre_hook(name, item, metadata):
        pre_calls.append(name)

    def post_hook(name, item):
        post_calls.append(name)

    # warn 策略：pre_hook 会被调用，但 post_hook 不会（因为跳过了注册）
    registry = SimpleRegistry(duplicate_policy='warn')
    registry.add_hook('pre_register', pre_hook)
    registry.add_hook('post_register', post_hook)

    registry.register('item1', 'value1')
    registry.register('item1', 'value2')

    assert len(pre_calls) == 2  # pre_hook 两次都调用
    assert len(post_calls) == 1  # post_hook 只在第一次调用


def test_policy_error_mode_strict():
    """测试：error 模式提供严格的注册控制"""

    registry = SimpleRegistry(duplicate_policy='error')

    # 成功注册多个不同的项
    registry.register('item1', 'value1')
    registry.register('item2', 'value2')
    registry.register('item3', 'value3')

    assert registry.count() == 3

    # 尝试重复注册任何一个都会失败
    with pytest.raises(RegistryError):
        registry.register('item1', 'new_value')

    with pytest.raises(RegistryError):
        registry.register('item2', 'new_value')

    # 验证所有原值未变
    assert registry.get('item1') == 'value1'
    assert registry.get('item2') == 'value2'
    assert registry.get('item3') == 'value3'


def test_policy_replace_mode_override():
    """测试：replace 模式允许覆盖注册"""

    registry = SimpleRegistry(duplicate_policy='replace')

    # 多次注册同一个键
    registry.register('config', 'v1')
    registry.register('config', 'v2')
    registry.register('config', 'v3')

    # 最后一次注册生效
    assert registry.get('config') == 'v3'
    assert registry.count() == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

