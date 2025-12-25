# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - Context 基础功能测试

作者：Plumeink

测试 PR-R1 的最小验收集合：
1. singleton：同名两次 get() 返回同一对象
2. prototype：同名两次 get() 返回不同对象
"""

import unittest
import sys
import os

# 确保能导入 cullinan
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.core.container import ApplicationContext
from cullinan.core.container import Definition, ScopeType


class SimpleService:
    """用于测试的简单服务类"""

    instance_count = 0

    def __init__(self):
        SimpleService.instance_count += 1
        self.id = SimpleService.instance_count


class TestApplicationContextBasics(unittest.TestCase):
    """ApplicationContext 基础功能测试"""

    def setUp(self):
        """每个测试前重置计数器"""
        SimpleService.instance_count = 0

    def test_singleton_scope_returns_same_instance(self):
        """singleton：同名两次 get() 返回同一对象"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='SimpleService',
            factory=lambda c: SimpleService(),
            scope=ScopeType.SINGLETON,
            source='test:SimpleService'
        ))

        ctx.refresh()

        # 两次 get 应该返回同一个实例
        instance1 = ctx.get('SimpleService')
        instance2 = ctx.get('SimpleService')

        self.assertIs(instance1, instance2)
        self.assertEqual(instance1.id, instance2.id)
        # 应该只创建了一次
        self.assertEqual(SimpleService.instance_count, 1)

    def test_prototype_scope_returns_different_instances(self):
        """prototype：同名两次 get() 返回不同对象"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='SimpleService',
            factory=lambda c: SimpleService(),
            scope=ScopeType.PROTOTYPE,
            source='test:SimpleService'
        ))

        ctx.refresh()

        # 两次 get 应该返回不同的实例
        instance1 = ctx.get('SimpleService')
        instance2 = ctx.get('SimpleService')

        self.assertIsNot(instance1, instance2)
        self.assertNotEqual(instance1.id, instance2.id)
        # 应该创建了两次
        self.assertEqual(SimpleService.instance_count, 2)

    def test_register_before_refresh_succeeds(self):
        """refresh 前允许注册"""
        ctx = ApplicationContext()

        # 应该不抛异常
        ctx.register(Definition(
            name='Service1',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:Service1'
        ))

        ctx.register(Definition(
            name='Service2',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:Service2'
        ))

        self.assertEqual(ctx.definition_count, 2)
        self.assertFalse(ctx.is_frozen)

    def test_refresh_freezes_registry(self):
        """refresh 后 registry 被冻结"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='Service',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:Service'
        ))

        self.assertFalse(ctx.is_frozen)

        ctx.refresh()

        self.assertTrue(ctx.is_frozen)
        self.assertTrue(ctx.is_refreshed)

    def test_has_returns_correct_value(self):
        """has() 正确返回 Definition 是否存在"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='ExistingService',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ExistingService'
        ))

        self.assertTrue(ctx.has('ExistingService'))
        self.assertFalse(ctx.has('NonExistingService'))

    def test_list_definitions(self):
        """list_definitions() 返回所有已注册的名称"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='ServiceA',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ServiceA'
        ))

        ctx.register(Definition(
            name='ServiceB',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ServiceB'
        ))

        names = ctx.list_definitions()

        self.assertIn('ServiceA', names)
        self.assertIn('ServiceB', names)
        self.assertEqual(len(names), 2)

    def test_try_get_returns_none_for_missing(self):
        """try_get() 对不存在的依赖返回 None"""
        ctx = ApplicationContext()
        ctx.refresh()

        result = ctx.try_get('NonExisting')

        self.assertIsNone(result)

    def test_try_get_returns_instance_for_existing(self):
        """try_get() 对存在的依赖返回实例"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='Service',
            factory=lambda c: SimpleService(),
            scope=ScopeType.SINGLETON,
            source='test:Service'
        ))

        ctx.refresh()

        result = ctx.try_get('Service')

        self.assertIsNotNone(result)
        self.assertIsInstance(result, SimpleService)

    def test_eager_initialization(self):
        """eager=True 的 Definition 在 refresh 时预创建"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='EagerService',
            factory=lambda c: SimpleService(),
            scope=ScopeType.SINGLETON,
            source='test:EagerService',
            eager=True
        ))

        self.assertEqual(SimpleService.instance_count, 0)

        ctx.refresh()

        # refresh 后应该已经创建
        self.assertEqual(SimpleService.instance_count, 1)

    def test_non_eager_not_initialized_on_refresh(self):
        """eager=False 的 Definition 在 refresh 时不创建"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='LazyService',
            factory=lambda c: SimpleService(),
            scope=ScopeType.SINGLETON,
            source='test:LazyService',
            eager=False
        ))

        ctx.refresh()

        # refresh 后应该还没创建
        self.assertEqual(SimpleService.instance_count, 0)

        # 首次 get 时才创建
        ctx.get('LazyService')
        self.assertEqual(SimpleService.instance_count, 1)


class TestConditions(unittest.TestCase):
    """条件功能测试"""

    def test_condition_satisfied_allows_resolution(self):
        """条件满足时允许解析"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='ConditionalService',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ConditionalService',
            conditions=[lambda c: True]
        ))

        ctx.refresh()

        result = ctx.get('ConditionalService')
        self.assertIsNotNone(result)

    def test_try_get_returns_none_when_condition_not_met(self):
        """try_get 在条件不满足时返回 None"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='ConditionalService',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ConditionalService',
            conditions=[lambda c: False]
        ))

        ctx.refresh()

        result = ctx.try_get('ConditionalService')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

