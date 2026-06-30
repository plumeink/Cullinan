# -*- coding: utf-8 -*-
"""测试传递 scope 约束校验（Issue 3 修复验证）

验证 singleton/prototype → request-scoped 的传递依赖链在 refresh 时被拦截。
"""

import unittest
from cullinan.core.container import ApplicationContext
from cullinan.core.container import Definition, ScopeType
from cullinan.core.exceptions import LifecycleError
from cullinan.core.decorators import Inject, InjectByName


# ---- 测试组件 ----

class RequestScopedService:
    """模拟 request-scoped 组件"""
    def __init__(self):
        self.value = "request"


class SingletonB:
    """singleton B，通过 field injection 依赖 RequestScopedService"""
    req = InjectByName("RequestScopedService")

    def __init__(self):
        pass


class SingletonA:
    """singleton A，显式依赖 SingletonB"""

    def __init__(self):
        pass


class PrototypeB:
    """prototype B，通过 field injection 依赖 RequestScopedService"""
    req = InjectByName("RequestScopedService")

    def __init__(self):
        pass


class PrototypeA:
    """prototype A，显式依赖 PrototypeB"""

    def __init__(self):
        pass


class SingletonWithPrivateDI:
    """singleton，使用 _ 前缀的 Inject 依赖 request scoped（验证 Issue 5 联动）"""
    _req = InjectByName("RequestScopedService")

    def __init__(self):
        pass


# ---- 直接依赖测试（确保原有检查不退化） ----

class TestDirectScopeViolation(unittest.TestCase):
    """测试：singleton 直接依赖 request scoped 仍被检测"""

    def test_singleton_directly_depends_on_request(self):
        ctx = ApplicationContext()

        ctx.register(Definition(
            name="RequestService",
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source="test:RequestService",
        ))
        ctx.register(Definition(
            name="SingletonService",
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.SINGLETON,
            dependencies=["RequestService"],
            source="test:SingletonService",
        ))

        with self.assertRaises(LifecycleError) as cm:
            ctx.refresh()
        self.assertIn("request-scoped", str(cm.exception))


# ---- 传递依赖测试 ----

class TestTransitiveScopeViolation(unittest.TestCase):
    """测试：singleton 传递依赖 request scoped 被检测"""

    def test_singleton_transitive_via_explicit_deps(self):
        """SingletonA → SingletonB → RequestC (显式依赖链)"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name="RequestScopedService",
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source="test:RequestScopedService",
        ))
        ctx.register(Definition(
            name="SingletonB",
            factory=lambda c: SingletonB(),
            scope=ScopeType.SINGLETON,
            type_=SingletonB,
            dependencies=["RequestScopedService"],
            source="test:SingletonB",
        ))
        ctx.register(Definition(
            name="SingletonA",
            factory=lambda c: SingletonA(),
            scope=ScopeType.SINGLETON,
            type_=SingletonA,
            dependencies=["SingletonB"],
            source="test:SingletonA",
        ))

        with self.assertRaises(LifecycleError) as cm:
            ctx.refresh()
        self.assertIn("request-scoped", str(cm.exception))
        self.assertIn("SingletonB", str(cm.exception))

    def test_singleton_transitive_via_field_injection(self):
        """SingletonA → SingletonB(Inject→RequestC) (隐式 field injection 链)"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name="RequestScopedService",
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source="test:RequestScopedService",
        ))
        ctx.register(Definition(
            name="SingletonB",
            factory=lambda c: SingletonB(),
            scope=ScopeType.SINGLETON,
            type_=SingletonB,
            source="test:SingletonB",
        ))
        ctx.register(Definition(
            name="SingletonA",
            factory=lambda c: SingletonA(),
            scope=ScopeType.SINGLETON,
            dependencies=["SingletonB"],
            source="test:SingletonA",
        ))

        with self.assertRaises(LifecycleError) as cm:
            ctx.refresh()
        self.assertIn("RequestScopedService", str(cm.exception))
        self.assertIn("field", str(cm.exception).lower())

    def test_prototype_transitive_via_field_injection(self):
        """PrototypeA → PrototypeB(Inject→RequestC) (prototype 传递依赖)"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name="RequestScopedService",
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source="test:RequestScopedService",
        ))
        ctx.register(Definition(
            name="PrototypeB",
            factory=lambda c: PrototypeB(),
            scope=ScopeType.PROTOTYPE,
            type_=PrototypeB,
            source="test:PrototypeB",
        ))
        ctx.register(Definition(
            name="PrototypeA",
            factory=lambda c: PrototypeA(),
            scope=ScopeType.PROTOTYPE,
            dependencies=["PrototypeB"],
            source="test:PrototypeA",
        ))

        with self.assertRaises(LifecycleError) as cm:
            ctx.refresh()
        self.assertIn("RequestScopedService", str(cm.exception))

    def test_underscore_prefixed_injection_also_checked(self):
        """_ 前缀 field injection 也受 scope 校验（Issue 5 联动）"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name="RequestScopedService",
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            source="test:RequestScopedService",
        ))
        ctx.register(Definition(
            name="SingletonWithPrivateDI",
            factory=lambda c: SingletonWithPrivateDI(),
            scope=ScopeType.SINGLETON,
            type_=SingletonWithPrivateDI,
            source="test:SingletonWithPrivateDI",
        ))

        with self.assertRaises(LifecycleError) as cm:
            ctx.refresh()
        self.assertIn("RequestScopedService", str(cm.exception))

    def test_request_to_singleton_is_allowed(self):
        """request → singleton 依赖是合法的（反向不报错）"""
        ctx = ApplicationContext()

        ctx.register(Definition(
            name="SingletonService",
            factory=lambda c: SingletonA(),
            scope=ScopeType.SINGLETON,
            source="test:SingletonService",
        ))
        ctx.register(Definition(
            name="RequestService",
            factory=lambda c: RequestScopedService(),
            scope=ScopeType.REQUEST,
            dependencies=["SingletonService"],
            source="test:RequestService",
        ))

        # 不应抛出 LifecycleError
        try:
            ctx.refresh()
        except LifecycleError:
            self.fail("request → singleton 依赖不应触发 LifecycleError")
