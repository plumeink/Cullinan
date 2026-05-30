# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - Factory 集成测试

作者：Plumeink

测试 PR-R4 的最小验收集合：
1. 基于现有注入能力进行真实注入
2. 注入失败输出结构化诊断
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.core.container import ApplicationContext
from cullinan.core.container import Definition, ScopeType
from cullinan.core.container import Factory


class UserRepository:
    """模拟 Repository"""

    def get_user(self, user_id: int) -> dict:
        return {'id': user_id, 'name': f'User{user_id}'}


class UserService:
    """模拟 Service，依赖 Repository"""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def find_user(self, user_id: int) -> dict:
        return self.repo.get_user(user_id)


class TestFactoryBasics(unittest.TestCase):
    """Factory 基础功能测试"""

    def test_factory_resolve_delegates_to_context(self):
        """Factory.resolve 委托给 Context"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='UserRepository',
            factory=lambda c: UserRepository(),
            scope=ScopeType.SINGLETON,
            source='test:UserRepository'
        ))

        ctx.refresh()

        factory = Factory(ctx)
        instance = factory.resolve(ctx.get_definition('UserRepository'))

        self.assertIsInstance(instance, UserRepository)

    def test_factory_create_raw_bypasses_cache(self):
        """Factory.create_raw 绑过缓存每次创建新实例"""
        ctx = ApplicationContext()

        call_count = [0]

        def counting_factory(c):
            call_count[0] += 1
            return UserRepository()

        definition = Definition(
            name='UserRepository',
            factory=counting_factory,
            scope=ScopeType.SINGLETON,
            source='test:UserRepository'
        )

        ctx.register(definition)
        ctx.refresh()

        factory = Factory(ctx)

        # create_raw 每次都调用 factory
        instance1 = factory.create_raw(definition)
        instance2 = factory.create_raw(definition)

        self.assertIsNot(instance1, instance2)
        self.assertEqual(call_count[0], 2)


class TestDependencyInjectionViaContext(unittest.TestCase):
    """通过 Context 实现依赖注入测试"""

    def test_manual_dependency_injection(self):
        """手动依赖注入（factory 中调用 ctx.get）"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='UserRepository',
            factory=lambda c: UserRepository(),
            scope=ScopeType.SINGLETON,
            source='test:UserRepository'
        ))

        ctx.register(Definition(
            name='UserService',
            factory=lambda c: UserService(c.get('UserRepository')),
            scope=ScopeType.SINGLETON,
            source='test:UserService'
        ))

        ctx.refresh()

        service = ctx.get('UserService')

        self.assertIsInstance(service, UserService)
        self.assertIsInstance(service.repo, UserRepository)

        # 验证功能正常
        user = service.find_user(1)
        self.assertEqual(user['id'], 1)

    def test_dependency_chain_resolution(self):
        """依赖链解析"""
        ctx = ApplicationContext()

        class Controller:
            def __init__(self, service: UserService):
                self.service = service

        ctx.register(Definition(
            name='UserRepository',
            factory=lambda c: UserRepository(),
            scope=ScopeType.SINGLETON,
            source='test:UserRepository'
        ))

        ctx.register(Definition(
            name='UserService',
            factory=lambda c: UserService(c.get('UserRepository')),
            scope=ScopeType.SINGLETON,
            source='test:UserService'
        ))

        ctx.register(Definition(
            name='UserController',
            factory=lambda c: Controller(c.get('UserService')),
            scope=ScopeType.SINGLETON,
            source='test:UserController'
        ))

        ctx.refresh()

        controller = ctx.get('UserController')

        self.assertIsInstance(controller.service, UserService)
        self.assertIsInstance(controller.service.repo, UserRepository)


class TestPostProcessors(unittest.TestCase):
    """后处理器测试"""

    def test_post_processor_is_called(self):
        """后处理器被调用"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name='Service',
            factory=lambda c: UserRepository(),
            scope=ScopeType.SINGLETON,
            source='test:Service'
        ))

        ctx.refresh()

        factory = Factory(ctx)

        processed = []

        def track_processor(instance, definition):
            processed.append(definition.name)
            return instance

        factory.add_post_processor(track_processor)

        definition = ctx.get_definition('Service')
        factory.resolve(definition)

        self.assertIn('Service', processed)


if __name__ == '__main__':
    unittest.main()

