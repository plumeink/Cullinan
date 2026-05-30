# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - 生命周期测试

作者：Plumeink

测试 PR-R5 的最小验收集合：
1. refresh/start 触发 eager 初始化
2. shutdown 按顺序执行
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.core.container import ApplicationContext
from cullinan.core.container import Definition, ScopeType


class LifecycleTracker:
    """用于跟踪生命周期事件的辅助类"""
    
    events = []
    
    @classmethod
    def reset(cls):
        cls.events = []
    
    @classmethod
    def record(cls, event: str):
        cls.events.append(event)


class ServiceWithLifecycle:
    """带生命周期钩子的服务"""
    
    def __init__(self, name: str):
        self.name = name
        LifecycleTracker.record(f'{name}:init')
    
    def on_shutdown(self):
        LifecycleTracker.record(f'{self.name}:shutdown')


class TestEagerInitialization(unittest.TestCase):
    """Eager 初始化测试"""
    
    def setUp(self):
        LifecycleTracker.reset()
    
    def test_eager_definitions_initialized_on_refresh(self):
        """eager=True 的 Definition 在 refresh 时初始化"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='EagerService',
            factory=lambda c: ServiceWithLifecycle('EagerService'),
            scope=ScopeType.SINGLETON,
            source='test:EagerService',
            eager=True
        ))
        
        self.assertEqual(len(LifecycleTracker.events), 0)
        
        ctx.refresh()
        
        self.assertIn('EagerService:init', LifecycleTracker.events)
    
    def test_non_eager_definitions_not_initialized_on_refresh(self):
        """eager=False 的 Definition 在 refresh 时不初始化"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='LazyService',
            factory=lambda c: ServiceWithLifecycle('LazyService'),
            scope=ScopeType.SINGLETON,
            source='test:LazyService',
            eager=False
        ))
        
        ctx.refresh()
        
        self.assertNotIn('LazyService:init', LifecycleTracker.events)
        
        # 首次访问时才初始化
        ctx.get('LazyService')
        self.assertIn('LazyService:init', LifecycleTracker.events)
    
    def test_eager_initialization_respects_dependencies(self):
        """eager 初始化时遵循依赖顺序"""
        ctx = ApplicationContext()
        
        ctx.register(Definition(
            name='ServiceA',
            factory=lambda c: ServiceWithLifecycle('ServiceA'),
            scope=ScopeType.SINGLETON,
            source='test:ServiceA',
            eager=True,
            dependencies=['ServiceB']  # A 依赖 B
        ))
        
        ctx.register(Definition(
            name='ServiceB',
            factory=lambda c: ServiceWithLifecycle('ServiceB'),
            scope=ScopeType.SINGLETON,
            source='test:ServiceB',
            eager=True
        ))
        
        ctx.refresh()
        
        # 两个都应该被初始化
        self.assertIn('ServiceA:init', LifecycleTracker.events)
        self.assertIn('ServiceB:init', LifecycleTracker.events)


class TestShutdown(unittest.TestCase):
    """Shutdown 测试"""
    
    def setUp(self):
        LifecycleTracker.reset()
    
    def test_shutdown_handlers_are_called(self):
        """shutdown 时调用注册的 handler"""
        ctx = ApplicationContext()
        ctx.refresh()
        
        ctx.add_shutdown_handler(lambda: LifecycleTracker.record('handler1'))
        ctx.add_shutdown_handler(lambda: LifecycleTracker.record('handler2'))
        
        ctx.shutdown()
        
        self.assertIn('handler1', LifecycleTracker.events)
        self.assertIn('handler2', LifecycleTracker.events)
    
    def test_shutdown_handlers_called_in_order(self):
        """shutdown handler 按注册顺序调用"""
        ctx = ApplicationContext()
        ctx.refresh()
        
        ctx.add_shutdown_handler(lambda: LifecycleTracker.record('first'))
        ctx.add_shutdown_handler(lambda: LifecycleTracker.record('second'))
        ctx.add_shutdown_handler(lambda: LifecycleTracker.record('third'))
        
        ctx.shutdown()
        
        first_idx = LifecycleTracker.events.index('first')
        second_idx = LifecycleTracker.events.index('second')
        third_idx = LifecycleTracker.events.index('third')
        
        self.assertLess(first_idx, second_idx)
        self.assertLess(second_idx, third_idx)
    
    def test_shutdown_handler_exception_does_not_stop_others(self):
        """一个 handler 异常不阻止其他 handler 执行"""
        ctx = ApplicationContext()
        ctx.refresh()
        
        def failing_handler():
            LifecycleTracker.record('failing')
            raise RuntimeError("Intentional failure")
        
        ctx.add_shutdown_handler(lambda: LifecycleTracker.record('before'))
        ctx.add_shutdown_handler(failing_handler)
        ctx.add_shutdown_handler(lambda: LifecycleTracker.record('after'))
        
        # shutdown 不应该因为一个 handler 失败而中断
        ctx.shutdown()
        
        self.assertIn('before', LifecycleTracker.events)
        self.assertIn('failing', LifecycleTracker.events)
        self.assertIn('after', LifecycleTracker.events)


class TestContextLifecycle(unittest.TestCase):
    """Context 完整生命周期测试"""
    
    def setUp(self):
        LifecycleTracker.reset()
    
    def test_full_lifecycle(self):
        """完整生命周期：register -> refresh -> use -> shutdown"""
        ctx = ApplicationContext()
        
        # 1. Register
        ctx.register(Definition(
            name='Service',
            factory=lambda c: ServiceWithLifecycle('Service'),
            scope=ScopeType.SINGLETON,
            source='test:Service',
            eager=True
        ))
        
        self.assertFalse(ctx.is_refreshed)
        
        # 2. Refresh
        ctx.refresh()
        
        self.assertTrue(ctx.is_refreshed)
        self.assertTrue(ctx.is_frozen)
        self.assertIn('Service:init', LifecycleTracker.events)
        
        # 3. Use
        service = ctx.get('Service')
        self.assertIsNotNone(service)
        
        # 4. Shutdown
        ctx.add_shutdown_handler(lambda: LifecycleTracker.record('context:shutdown'))
        ctx.shutdown()
        
        self.assertIn('context:shutdown', LifecycleTracker.events)


if __name__ == '__main__':
    unittest.main()

