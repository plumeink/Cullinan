# -*- coding: utf-8 -*-
"""Constructor injection tests (Issue 6)."""

import pytest

from cullinan.core.application_context import ApplicationContext
from cullinan.core.definitions import Definition, ScopeType
from cullinan.core.exceptions import (
    AmbiguousDependencyError,
    DependencyNotFoundError,
    LifecycleError,
)
from cullinan.core.pending import PendingRegistry


# ── Test utility ────────────────────────────────────────────────────────

def _make_factory(ctx, cls, name):
    """Register *cls* in *ctx* and return a `get` shortcut."""
    ctx.register(Definition(
        name=name,
        factory=lambda c: c._create_class_instance(cls),
        scope=ScopeType.SINGLETON,
        source="test",
        type_=cls,
    ))
    ctx.refresh()
    return ctx.get(name)


# ── 1. Single & multi param ─────────────────────────────────────────────

class DatabaseService:
    def connect(self) -> str:
        return "connected"


class CacheService:
    def get(self, key: str) -> str:
        return f"cache:{key}"


class UserService:
    database: DatabaseService


class MultiService:
    database: DatabaseService
    cache: CacheService


def test_single_param():
    """Scenario 1: single constructor param."""
    ctx = ApplicationContext()
    ctx.register(Definition("db", lambda c: c._create_class_instance(DatabaseService),
                            ScopeType.SINGLETON, "test", type_=DatabaseService))
    svc = _make_factory(ctx, UserService, "USvc")
    assert isinstance(svc.database, DatabaseService)
    assert svc.database.connect() == "connected"


def test_multi_param():
    """Scenario 2: multiple constructor params."""
    ctx = ApplicationContext()
    ctx.register(Definition("db", lambda c: c._create_class_instance(DatabaseService),
                            ScopeType.SINGLETON, "test", type_=DatabaseService))
    ctx.register(Definition("cache", lambda c: c._create_class_instance(CacheService),
                            ScopeType.SINGLETON, "test", type_=CacheService))
    svc = _make_factory(ctx, MultiService, "MSvc")
    assert isinstance(svc.database, DatabaseService)
    assert isinstance(svc.cache, CacheService)


# ── 2. Optional DI ──────────────────────────────────────────────────────

class NotifierService:
    pass


class OptionalService:
    database: DatabaseService
    notifier: NotifierService = None


def test_optional_di_present():
    """Scenario 3: Optional DI — present dep injected, absent stays None."""
    ctx = ApplicationContext()
    ctx.register(Definition("db", lambda c: c._create_class_instance(DatabaseService),
                            ScopeType.SINGLETON, "test", type_=DatabaseService))
    svc = _make_factory(ctx, OptionalService, "OSvc")
    assert isinstance(svc.database, DatabaseService)
    assert svc.notifier is None


def test_optional_di_no_error():
    """Scenario 6: Optional missing dep — refresh succeeds."""
    ctx = ApplicationContext()
    ctx.register(Definition("db", lambda c: c._create_class_instance(DatabaseService),
                            ScopeType.SINGLETON, "test", type_=DatabaseService))
    ctx.register(Definition("optsvc", lambda c: c._create_class_instance(OptionalService),
                            ScopeType.SINGLETON, "test", type_=OptionalService))
    ctx.refresh()  # No exception


# ── 3. Mixed constructor + field injection ──────────────────────────────

from cullinan.core.decorators import Inject


class MixedService:
    database: DatabaseService  # constructor
    cache: CacheService = Inject()  # field


def test_mixed_constructor_and_field():
    """Scenario 4: constructor + field coexist."""
    ctx = ApplicationContext()
    ctx.register(Definition("db", lambda c: c._create_class_instance(DatabaseService),
                            ScopeType.SINGLETON, "test", type_=DatabaseService))
    ctx.register(Definition("cache", lambda c: c._create_class_instance(CacheService),
                            ScopeType.SINGLETON, "test", type_=CacheService))
    svc = _make_factory(ctx, MixedService, "MixedSvc")
    assert isinstance(svc.database, DatabaseService)
    assert isinstance(svc.cache, CacheService)


def test_immutability_field_no_overwrite():
    """Scenario 5: field injection skips constructor-set attrs."""
    ctx = ApplicationContext()
    ctx.register(Definition("db", lambda c: c._create_class_instance(DatabaseService),
                            ScopeType.SINGLETON, "test", type_=DatabaseService))
    svc = _make_factory(ctx, UserService, "USvc2")
    db = svc.database
    assert isinstance(db, DatabaseService)
    assert db is svc.database  # identity not replaced


# ── 4. Error cases ──────────────────────────────────────────────────────

class UnknownService:
    pass


class MissingDepService:
    nonexistent: UnknownService   # NOT registered!


def test_missing_required_dependency():
    """Scenario 7: required dep missing → DependencyNotFoundError."""
    ctx = ApplicationContext()
    ctx.register(Definition("missing", lambda c: c._create_class_instance(MissingDepService),
                            ScopeType.SINGLETON, "test", type_=MissingDepService))
    with pytest.raises(DependencyNotFoundError):
        ctx.refresh()


# ── 5. Ambiguous multi-candidate ────────────────────────────────────────

class BaseRepo:
    pass


class MemoryRepo(BaseRepo):
    pass


class DiskRepo(BaseRepo):
    pass


class AmbiguousConsumer:
    repo: BaseRepo


def test_ambiguous_dependency():
    """Scenario 8: multiple candidates → AmbiguousDependencyError."""
    ctx = ApplicationContext()
    ctx.register(Definition("mem", lambda c: c._create_class_instance(MemoryRepo),
                            ScopeType.SINGLETON, "test", type_=MemoryRepo))
    ctx.register(Definition("disk", lambda c: c._create_class_instance(DiskRepo),
                            ScopeType.SINGLETON, "test", type_=DiskRepo))
    ctx.register(Definition("amb", lambda c: c._create_class_instance(AmbiguousConsumer),
                            ScopeType.SINGLETON, "test", type_=AmbiguousConsumer))
    with pytest.raises(AmbiguousDependencyError):
        ctx.refresh()


# ── 6. Manual instantiation ─────────────────────────────────────────────

def test_manual_instantiation_no_di():
    """Scenario 9: manual instantiation + setattr bypasses DI entirely."""
    class MockDB:
        def connect(self) -> str:
            return "mock"

    svc = UserService()
    svc.database = MockDB()
    assert svc.database.connect() == "mock"


# ── 7. Scope validation ─────────────────────────────────────────────────

class RequestScopedSvc:
    pass


class SingletonConsumer:
    req_svc: RequestScopedSvc


def test_scope_violation():
    """Scenario 10: singleton → request scope blocked."""
    ctx = ApplicationContext()
    ctx.register(Definition("req", lambda c: c._create_class_instance(RequestScopedSvc),
                            ScopeType.REQUEST, "test", type_=RequestScopedSvc))
    ctx.register(Definition("singleton", lambda c: c._create_class_instance(SingletonConsumer),
                            ScopeType.SINGLETON, "test", type_=SingletonConsumer))
    with pytest.raises(LifecycleError):
        ctx.refresh()


# ── 8. Backward compatibility ───────────────────────────────────────────

from cullinan.core.decorators import Lazy


class FieldOnlyService:
    database: DatabaseService = Inject()


class LazyFieldService:
    cache: CacheService = Lazy()


def test_field_injection_backward_compat():
    """Scenario 11: existing field injection unchanged."""
    ctx = ApplicationContext()
    ctx.register(Definition("db", lambda c: c._create_class_instance(DatabaseService),
                            ScopeType.SINGLETON, "test", type_=DatabaseService))
    ctx.register(Definition("cache", lambda c: c._create_class_instance(CacheService),
                            ScopeType.SINGLETON, "test", type_=CacheService))

    svc = _make_factory(ctx, FieldOnlyService, "FieldSvc")
    assert isinstance(svc.database, DatabaseService)

    ctx2 = ApplicationContext()
    ctx2.register(Definition("db2", lambda c: c._create_class_instance(DatabaseService),
                             ScopeType.SINGLETON, "test", type_=DatabaseService))
    ctx2.register(Definition("cache2", lambda c: c._create_class_instance(CacheService),
                             ScopeType.SINGLETON, "test", type_=CacheService))
    lazy_svc = _make_factory(ctx2, LazyFieldService, "LazySvc")
    # Lazy() returns _LazyProxy — the proxy resolves on first access
    # when the framework resolves it (not during the instance.__dict__ check).
    from cullinan.core.application_context import _LazyProxy
    assert isinstance(lazy_svc.cache, _LazyProxy)


# ── 9. Literal defaults ─────────────────────────────────────────────────

class SimpleService:
    name: str = "hello"

    def greet(self) -> str:
        return self.name


def test_literal_default_not_injected():
    """Literal defaults are not treated as DI."""
    ctx = ApplicationContext()
    svc = _make_factory(ctx, SimpleService, "Simple")
    assert svc.name == "hello"


# ── 10. Edge cases ──────────────────────────────────────────────────────

class NoAnnotationService:
    pass


def test_no_annotations_no_error():
    """Class with no annotations works fine."""
    ctx = ApplicationContext()
    svc = _make_factory(ctx, NoAnnotationService, "NoAnn")
    assert svc is not None


# ── 11. find_by_type unit tests ─────────────────────────────────────────

from cullinan.core.definition_registry import DefinitionRegistry, _unwrap_optional
from typing import Optional


def test_unwrap_optional():
    assert _unwrap_optional(Optional[DatabaseService]) is DatabaseService
    assert _unwrap_optional(DatabaseService) is DatabaseService
    assert _unwrap_optional(None) is None


def test_find_by_type():
    reg = DefinitionRegistry()
    reg.register(Definition("db", lambda c: None, ScopeType.SINGLETON, "test", type_=DatabaseService))
    reg.register(Definition("cache", lambda c: None, ScopeType.SINGLETON, "test", type_=CacheService))

    assert len(reg.find_by_type(DatabaseService)) == 1
    assert reg.find_by_type(DatabaseService)[0].name == "db"
    assert len(reg.find_by_type(object)) == 2
    assert len(reg.find_by_type(UnknownService)) == 0
