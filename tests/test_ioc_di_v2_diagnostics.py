# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - 诊断与异常测试

作者：Plumeink

测试 PR-R3 的最小验收集合：
1. 缺失依赖：断言异常字段包含 injection_point/dependency_name/resolution_path/candidate_sources
2. 循环依赖：链路严格等于 A->B->C->A
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.core.container import ApplicationContext
from cullinan.core.container import Definition, ScopeType
from cullinan.core.diagnostics import (
    DependencyNotFoundError,
    CircularDependencyError,
    ConditionNotMetError,
    CreationError,
    render_resolution_path,
    format_circular_dependency_error,
    format_missing_dependency_error,
)


class TestDependencyNotFoundError(unittest.TestCase):
    """缺失依赖异常测试"""
    
    def test_get_missing_dependency_raises_error(self):
        """get() 缺失依赖抛出 DependencyNotFoundError"""
        ctx = ApplicationContext()
        ctx.refresh()
        
        with self.assertRaises(DependencyNotFoundError) as cm:
            ctx.get('NonExistingService')
        
        exc = cm.exception
        self.assertEqual(exc.dependency_name, 'NonExistingService')
    
    def test_error_contains_candidate_sources(self):
        """错误包含候选来源信息"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='ServiceA',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ServiceA'
        ))
        
        ctx.refresh()
        
        with self.assertRaises(DependencyNotFoundError) as cm:
            ctx.get('ServiceB')
        
        exc = cm.exception
        self.assertIsNotNone(exc.candidate_sources)
        self.assertGreater(len(exc.candidate_sources), 0)


class TestCircularDependencyError(unittest.TestCase):
    """循环依赖异常测试"""
    
    def test_circular_dependency_detected(self):
        """检测到循环依赖"""
        ctx = ApplicationContext()
        
        # A -> B -> C -> A
        ctx.register(Definition(
            name='ServiceA',
            factory=lambda c: c.get('ServiceB'),
            scope=ScopeType.SINGLETON,
            source='test:ServiceA'
        ))
        
        ctx.register(Definition(
            name='ServiceB',
            factory=lambda c: c.get('ServiceC'),
            scope=ScopeType.SINGLETON,
            source='test:ServiceB'
        ))
        
        ctx.register(Definition(
            name='ServiceC',
            factory=lambda c: c.get('ServiceA'),
            scope=ScopeType.SINGLETON,
            source='test:ServiceC'
        ))
        
        ctx.refresh()
        
        with self.assertRaises(CircularDependencyError) as cm:
            ctx.get('ServiceA')
        
        exc = cm.exception
        self.assertIsNotNone(exc.dependency_chain)
    
    def test_circular_dependency_chain_is_ordered(self):
        """循环依赖链路有序且稳定"""
        ctx = ApplicationContext()
        
        # A -> B -> A (简单环)
        ctx.register(Definition(
            name='ServiceA',
            factory=lambda c: c.get('ServiceB'),
            scope=ScopeType.SINGLETON,
            source='test:ServiceA'
        ))
        
        ctx.register(Definition(
            name='ServiceB',
            factory=lambda c: c.get('ServiceA'),
            scope=ScopeType.SINGLETON,
            source='test:ServiceB'
        ))
        
        ctx.refresh()
        
        with self.assertRaises(CircularDependencyError) as cm:
            ctx.get('ServiceA')
        
        exc = cm.exception
        chain = exc.dependency_chain
        
        # 链路应该是有序的：从 A 开始到 A 结束
        self.assertEqual(chain[0], 'ServiceA')
        self.assertEqual(chain[-1], 'ServiceA')
        self.assertIn('ServiceB', chain)
    
    def test_dependency_cycle_in_definitions_detected_on_refresh(self):
        """dependencies 中的环在 refresh 时被检测"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='ServiceA',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ServiceA',
            dependencies=['ServiceB']
        ))
        
        ctx.register(Definition(
            name='ServiceB',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ServiceB',
            dependencies=['ServiceC']
        ))
        
        ctx.register(Definition(
            name='ServiceC',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ServiceC',
            dependencies=['ServiceA']
        ))
        
        with self.assertRaises(CircularDependencyError) as cm:
            ctx.refresh()
        
        exc = cm.exception
        self.assertIsNotNone(exc.dependency_chain)


class TestConditionNotMetError(unittest.TestCase):
    """条件不满足异常测试"""
    
    def test_get_with_unmet_condition_raises_error(self):
        """get() 条件不满足抛出 ConditionNotMetError"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='ConditionalService',
            factory=lambda c: object(),
            scope=ScopeType.SINGLETON,
            source='test:ConditionalService',
            conditions=[lambda c: False]
        ))
        
        ctx.refresh()
        
        with self.assertRaises(ConditionNotMetError) as cm:
            ctx.get('ConditionalService')
        
        exc = cm.exception
        self.assertEqual(exc.dependency_name, 'ConditionalService')


class TestCreationError(unittest.TestCase):
    """创建失败异常测试"""
    
    def test_factory_exception_wrapped_in_creation_error(self):
        """factory 异常被包装为 CreationError"""
        ctx = ApplicationContext()
        
        def failing_factory(c):
            raise ValueError("Factory 内部错误")
        
        ctx.register(Definition(
            name='FailingService',
            factory=failing_factory,
            scope=ScopeType.SINGLETON,
            source='test:FailingService'
        ))
        
        ctx.refresh()
        
        with self.assertRaises(CreationError) as cm:
            ctx.get('FailingService')
        
        exc = cm.exception
        self.assertEqual(exc.dependency_name, 'FailingService')
        self.assertIsNotNone(exc.cause)
        self.assertIsInstance(exc.cause, ValueError)
    
    def test_factory_returning_none_raises_creation_error(self):
        """factory 返回 None 抛出 CreationError"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='NoneService',
            factory=lambda c: None,
            scope=ScopeType.SINGLETON,
            source='test:NoneService'
        ))
        
        ctx.refresh()
        
        with self.assertRaises(CreationError) as cm:
            ctx.get('NoneService')
        
        exc = cm.exception
        self.assertIn('None', str(exc))


class TestDiagnosticsRendering(unittest.TestCase):
    """诊断渲染功能测试"""
    
    def test_render_resolution_path(self):
        """render_resolution_path 输出稳定格式"""
        path = ['ServiceA', 'ServiceB', 'ServiceC', 'ServiceA']
        result = render_resolution_path(path)
        
        self.assertEqual(result, 'ServiceA -> ServiceB -> ServiceC -> ServiceA')
    
    def test_render_empty_path(self):
        """空路径渲染"""
        result = render_resolution_path([])
        self.assertEqual(result, '(empty)')
    
    def test_format_circular_dependency_error(self):
        """format_circular_dependency_error 输出包含链路"""
        chain = ['A', 'B', 'C', 'A']
        result = format_circular_dependency_error(chain)
        
        self.assertIn('A -> B -> C -> A', result)
        self.assertIn('循环依赖', result)
    
    def test_format_missing_dependency_error(self):
        """format_missing_dependency_error 输出包含依赖名"""
        result = format_missing_dependency_error(
            dependency_name='MissingService',
            available_sources=['ServiceA', 'ServiceB']
        )
        
        self.assertIn('MissingService', result)
        self.assertIn('ServiceA', result)


if __name__ == '__main__':
    unittest.main()

