# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - Request Scope 测试

作者：Plumeink

测试 PR-R6 的最小验收集合：
1. 无 RequestContext 解析 request scope：抛 ScopeNotActiveError
2. 不同 RequestContext 下实例隔离
"""

import unittest
import sys
import os
import threading
import concurrent.futures

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.core.container import ApplicationContext
from cullinan.core.container import Definition, ScopeType
from cullinan.core.diagnostics import ScopeNotActiveError


class RequestScopedService:
    """用于测试的 request scope 服务"""

    instance_count = 0

    def __init__(self):
        RequestScopedService.instance_count += 1
        self.id = RequestScopedService.instance_count


class TestRequestScopeBasics(unittest.TestCase):
    """Request Scope 基础功能测试"""

    def setUp(self):
        RequestScopedService.instance_count = 0

    def test_request_scope_without_context_raises_error(self):
        """无 RequestContext 解析 request scope 抛 ScopeNotActiveError"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='RequestService',
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source='test:RequestService'
        ))

        ctx.refresh()

        # 没有进入 request context 时应该抛出 ScopeNotActiveError
        with self.assertRaises(ScopeNotActiveError) as cm:
            ctx.get('RequestService')

        exc = cm.exception
        self.assertEqual(exc.scope_type, 'REQUEST')
        self.assertEqual(exc.dependency_name, 'RequestService')

    def test_request_scope_with_context_succeeds(self):
        """有 RequestContext 时 request scope 解析成功"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='RequestService',
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source='test:RequestService'
        ))

        ctx.refresh()

        # 进入 request context
        ctx.enter_request_context()
        try:
            instance = ctx.get('RequestService')
            self.assertIsNotNone(instance)
            self.assertIsInstance(instance, RequestScopedService)
        finally:
            ctx.exit_request_context()

    def test_same_request_context_returns_same_instance(self):
        """同一 request context 内返回同一实例"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='RequestService',
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source='test:RequestService'
        ))

        ctx.refresh()

        ctx.enter_request_context()
        try:
            instance1 = ctx.get('RequestService')
            instance2 = ctx.get('RequestService')

            self.assertIs(instance1, instance2)
            self.assertEqual(RequestScopedService.instance_count, 1)
        finally:
            ctx.exit_request_context()

    def test_different_request_contexts_return_different_instances(self):
        """不同 request context 返回不同实例"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='RequestService',
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source='test:RequestService'
        ))

        ctx.refresh()

        # 第一个请求
        ctx.enter_request_context()
        try:
            instance1 = ctx.get('RequestService')
        finally:
            ctx.exit_request_context()

        # 第二个请求
        ctx.enter_request_context()
        try:
            instance2 = ctx.get('RequestService')
        finally:
            ctx.exit_request_context()

        self.assertIsNot(instance1, instance2)
        self.assertNotEqual(instance1.id, instance2.id)
        self.assertEqual(RequestScopedService.instance_count, 2)

    def test_is_request_active_returns_correct_value(self):
        """is_request_active 正确反映状态"""
        ctx = ApplicationContext()
        ctx.refresh()

        self.assertFalse(ctx.is_request_active())

        ctx.enter_request_context()
        self.assertTrue(ctx.is_request_active())

        ctx.exit_request_context()
        self.assertFalse(ctx.is_request_active())


class TestRequestScopeConcurrency(unittest.TestCase):
    """Request Scope 并发测试"""

    def setUp(self):
        RequestScopedService.instance_count = 0

    def test_concurrent_requests_are_isolated(self):
        """并发请求下 request scope 实例隔离"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='RequestService',
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source='test:RequestService'
        ))

        ctx.refresh()

        results = {}

        def make_request(request_id: int):
            ctx.enter_request_context()
            try:
                instance = ctx.get('RequestService')
                results[request_id] = instance.id
            finally:
                ctx.exit_request_context()

        # 使用线程池模拟并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            concurrent.futures.wait(futures)

        # 应该有 5 个不同的实例
        self.assertEqual(len(results), 5)
        self.assertEqual(len(set(results.values())), 5)


class TestTryGetWithRequestScope(unittest.TestCase):
    """try_get 与 request scope 的交互测试"""

    def test_try_get_request_scope_without_context_raises_error(self):
        """try_get 在无 context 时对 request scope 仍应抛出 ScopeNotActiveError"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='RequestService',
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source='test:RequestService'
        ))

        ctx.refresh()

        # 按照 2.6.3 Contract，系统错误仍应抛出
        with self.assertRaises(ScopeNotActiveError):
            ctx.try_get('RequestService')


if __name__ == '__main__':
    unittest.main()