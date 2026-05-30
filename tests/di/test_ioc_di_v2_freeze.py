# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - 冻结机制测试

作者：Plumeink

测试 PR-R2 的最小验收集合：
1. refresh 前 register 成功
2. refresh 后 register/clear 抛 RegistryFrozenError
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.core.container import ApplicationContext
from cullinan.core.container import Definition, ScopeType
from cullinan.core.diagnostics import RegistryFrozenError


class TestFreezeAfterRefresh(unittest.TestCase):
    """冻结机制测试"""
    
    def test_register_before_refresh_succeeds(self):
        """refresh 前 register 成功"""
        ctx = ApplicationContext()
        
        # 应该不抛异常
        ctx.register(Definition(
            name='Service1',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:Service1'
        ))
        
        self.assertEqual(ctx.definition_count, 1)
        self.assertFalse(ctx.is_frozen)
    
    def test_register_after_refresh_raises_frozen_error(self):
        """refresh 后 register 抛 RegistryFrozenError"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='ExistingService',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ExistingService'
        ))
        
        ctx.refresh()
        
        # refresh 后注册应该抛出 RegistryFrozenError
        with self.assertRaises(RegistryFrozenError) as cm:
            ctx.register(Definition(
                name='NewService',
                factory=lambda c: object(),
                scope=ScopeType.SINGLETON,
                source='test:NewService'
            ))
        
        self.assertIn('冻结', str(cm.exception))
        self.assertIn('NewService', str(cm.exception))
    
    def test_duplicate_registration_raises_error(self):
        """重复注册同名 Definition 抛出 ValueError"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='Service',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:Service'
        ))
        
        with self.assertRaises(ValueError) as cm:
            ctx.register(Definition(
                name='Service',
                factory=lambda c: object(),
                scope=ScopeType.SINGLETON,
                source='test:Service'
            ))
        
        self.assertIn('已存在', str(cm.exception))
    
    def test_is_frozen_property(self):
        """is_frozen 属性正确反映状态"""
        ctx = ApplicationContext()
        
        self.assertFalse(ctx.is_frozen)
        
        ctx.refresh()
        
        self.assertTrue(ctx.is_frozen)
    
    def test_multiple_refresh_calls_are_idempotent(self):
        """多次调用 refresh 是幂等的"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='Service',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:Service'
        ))
        
        ctx.refresh()
        ctx.refresh()  # 第二次应该不会抛异常
        ctx.refresh()  # 第三次也不会
        
        self.assertTrue(ctx.is_frozen)
        self.assertTrue(ctx.is_refreshed)


class TestRegistryFrozenErrorDetails(unittest.TestCase):
    """RegistryFrozenError 异常详情测试"""
    
    def test_error_message_contains_definition_name(self):
        """错误信息包含尝试注册的 Definition 名称"""
        ctx = ApplicationContext()
        ctx.refresh()
        
        try:
            ctx.register(Definition(
                name='FailingService',
                factory=lambda c: object(),
                scope=ScopeType.SINGLETON,
                source='test:FailingService'
            ))
            self.fail("应该抛出 RegistryFrozenError")
        except RegistryFrozenError as e:
            self.assertIn('FailingService', str(e))
    
    def test_error_is_registry_error_subclass(self):
        """RegistryFrozenError 是 RegistryError 的子类"""
        from cullinan.core.diagnostics import RegistryError

        self.assertTrue(issubclass(RegistryFrozenError, RegistryError))


if __name__ == '__main__':
    unittest.main()

