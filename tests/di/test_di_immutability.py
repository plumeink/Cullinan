# -*- coding: utf-8 -*-
"""DI immutability enforcement tests.

Validates that all injection paths result in read-only attributes
after :meth:`ApplicationContext.refresh` materializes instances.
"""

import pytest

from cullinan.core.application_context import (
    ApplicationContext,
    _ImmutableAttributeError,
    _LazyProxy,
)
from cullinan.core.definitions import Definition, ScopeType
from cullinan.core.decorators import Inject, InjectByName, Lazy
from cullinan.testing import TestContext


# ── Custom types to avoid ambiguous type-based resolution ─────────────

class Database:
    pass


class CacheService:
    pass


class RepoService:
    pass


class EmailService:
    pass


class NotifierService:
    pass


class MixinDep:
    pass


class LazyDep:
    pass


class NamedDep:
    pass


# ── Test helpers ──────────────────────────────────────────────────────

def _make_frozen_instance(ctx, cls, name):
    """Register *cls* in *ctx*, refresh, and return the frozen instance."""
    ctx.register(Definition(
        name=name,
        factory=lambda c: c._create_class_instance(cls),
        scope=ScopeType.SINGLETON,
        source="test",
        type_=cls,
    ))
    ctx.refresh()
    return ctx.get(name)


# ── 1. Core freeze behavior ───────────────────────────────────────────

class SimpleService:
    database: Database


def test_frozen_reassign_raises():
    """Reassigning any injected attribute raises _ImmutableAttributeError."""
    ctx = ApplicationContext()
    ctx.register(Definition(
        "db_dep", lambda c: Database(),
        ScopeType.SINGLETON, "test", type_=Database,
    ))
    svc = _make_frozen_instance(ctx, SimpleService, "Svc")
    assert isinstance(svc.database, Database)

    with pytest.raises(_ImmutableAttributeError) as exc:
        svc.database = "hacked"
    assert "Cannot reassign 'database'" in str(exc.value)
    assert "TestContext.mock" in str(exc.value)


def test_frozen_non_di_attr_writable():
    """Non-DI attributes remain freely writable."""
    ctx = ApplicationContext()
    ctx.register(Definition(
        "db_dep", lambda c: Database(),
        ScopeType.SINGLETON, "test", type_=Database,
    ))
    svc = _make_frozen_instance(ctx, SimpleService, "Svc")

    svc.custom_field = 42
    assert svc.custom_field == 42
    svc.custom_field = 99
    assert svc.custom_field == 99


# ── 2. Constructor optional ───────────────────────────────────────────

class OptionalService:
    database: Database
    notifier: NotifierService = None    # optional — not registered → stays writable
    static_config: int = 5              # literal — framework ignores


def test_frozen_optional_none_not_registered():
    """= None without registration stays writable (user's field)."""
    ctx = ApplicationContext()
    ctx.register(Definition(
        "db_dep", lambda c: Database(),
        ScopeType.SINGLETON, "test", type_=Database,
    ))
    # notifier NOT registered
    svc = _make_frozen_instance(ctx, OptionalService, "OptSvc")
    assert isinstance(svc.database, Database)
    assert svc.notifier is None

    # database is frozen
    with pytest.raises(_ImmutableAttributeError):
        svc.database = "other"

    # notifier (= None, not registered) is NOT frozen
    svc.notifier = NotifierService()
    assert isinstance(svc.notifier, NotifierService)

    # literal is NOT frozen (framework ignores it)
    svc.static_config = 10
    assert svc.static_config == 10


# ── 3. Inject() mutations ─────────────────────────────────────────────

class InjectFieldService:
    repo: RepoService = Inject()
    cache: CacheService = Inject(required=False)


def test_frozen_inject_required_reassign_raises():
    """Inject() required → reassignment blocked."""
    ctx = ApplicationContext()
    ctx.register(Definition("repo_dep", lambda c: RepoService(),
                            ScopeType.SINGLETON, "test", type_=RepoService))
    ctx.register(Definition("cache_dep", lambda c: CacheService(),
                            ScopeType.SINGLETON, "test", type_=CacheService))
    svc = _make_frozen_instance(ctx, InjectFieldService, "IFSvc")
    assert isinstance(svc.repo, RepoService)
    assert isinstance(svc.cache, CacheService)

    with pytest.raises(_ImmutableAttributeError):
        svc.repo = "other"


def test_frozen_inject_required_false_not_found():
    """Inject(required=False) not found → stays None, frozen."""
    ctx = ApplicationContext()
    ctx.register(Definition("repo_dep", lambda c: RepoService(),
                            ScopeType.SINGLETON, "test", type_=RepoService))
    # cache NOT registered
    svc = _make_frozen_instance(ctx, InjectFieldService, "IFSvc2")
    assert isinstance(svc.repo, RepoService)
    assert svc.cache is None

    # repo is frozen
    with pytest.raises(_ImmutableAttributeError):
        svc.repo = "other"

    # cache is also frozen (Inject marker = DI intent)
    with pytest.raises(_ImmutableAttributeError):
        svc.cache = "fallback"


# ── 4. InjectByName ───────────────────────────────────────────────────

class InjectByNameService:
    email = InjectByName("EmailDep")
    notification = InjectByName()


def test_frozen_injectbyname():
    """InjectByName() attributes are frozen after injection."""
    ctx = ApplicationContext()
    ctx.register(Definition("EmailDep", lambda c: EmailService(),
                            ScopeType.SINGLETON, "test", type_=EmailService))
    ctx.register(Definition("notification", lambda c: NotifierService(),
                            ScopeType.SINGLETON, "test", type_=NotifierService))
    svc = _make_frozen_instance(ctx, InjectByNameService, "IBNSvc")
    assert isinstance(svc.email, EmailService)
    assert isinstance(svc.notification, NotifierService)

    with pytest.raises(_ImmutableAttributeError):
        svc.email = "other"
    with pytest.raises(_ImmutableAttributeError):
        svc.notification = "other"


# ── 5. Lazy ───────────────────────────────────────────────────────────

class LazyService:
    dep: LazyDep = Lazy()


def test_frozen_lazy():
    """Lazy()-injected attributes are frozen (proxy stored, not raw value)."""
    ctx = ApplicationContext()
    ctx.register(Definition("lazy_dep", lambda c: LazyDep(),
                            ScopeType.SINGLETON, "test", type_=LazyDep))
    svc = _make_frozen_instance(ctx, LazyService, "LazySvc")
    # Lazy stores a _LazyProxy; it resolves on method access, not ==
    assert isinstance(svc.dep, _LazyProxy)

    with pytest.raises(_ImmutableAttributeError):
        svc.dep = "other"


# ── 6. Mixed constructor + field injection ────────────────────────────

class MixedService:
    database: Database                # constructor injection
    cache: CacheService = Inject()    # field injection


def test_frozen_mixed_injection():
    """Both constructor and field injection are frozen."""
    ctx = ApplicationContext()
    ctx.register(Definition("db_dep", lambda c: Database(),
                            ScopeType.SINGLETON, "test", type_=Database))
    ctx.register(Definition("cache_dep", lambda c: CacheService(),
                            ScopeType.SINGLETON, "test", type_=CacheService))
    svc = _make_frozen_instance(ctx, MixedService, "MixedSvc")
    assert isinstance(svc.database, Database)
    assert isinstance(svc.cache, CacheService)

    with pytest.raises(_ImmutableAttributeError):
        svc.database = "other"
    with pytest.raises(_ImmutableAttributeError):
        svc.cache = "other"


# ── 7. TestContext bypass ─────────────────────────────────────────────

def test_frozen_mock_permanently():
    """TestContext.mock_permanently bypasses freeze using object.__setattr__."""
    ctx = ApplicationContext()
    ctx.register(Definition(
        "db_dep", lambda c: Database(),
        ScopeType.SINGLETON, "test", type_=Database,
    ))
    svc = _make_frozen_instance(ctx, SimpleService, "MockSvc")
    assert isinstance(svc.database, Database)

    db2 = Database()
    TestContext.mock_permanently(svc, "database", db2)
    assert svc.database is db2

    # mock_permanently uses object.__setattr__ once —
    # subsequent normal setattr still goes through frozen __setattr__
    with pytest.raises(_ImmutableAttributeError):
        svc.database = "another_mock"


def test_frozen_mock_context_manager():
    """TestContext.mock context manager restores on exit."""
    ctx = ApplicationContext()
    ctx.register(Definition(
        "db_dep", lambda c: Database(),
        ScopeType.SINGLETON, "test", type_=Database,
    ))
    svc = _make_frozen_instance(ctx, SimpleService, "CtxSvc")
    original = svc.database
    assert isinstance(original, Database)

    temp = Database()
    with TestContext.mock(svc, "database", temp):
        assert svc.database is temp

    assert svc.database is original


# ── 8. Prototype scope isolation ──────────────────────────────────────

def test_frozen_prototype_isolation():
    """Each prototype instance is independently frozen."""
    ctx = ApplicationContext()
    ctx.register(Definition(
        "prototype_svc",
        lambda c: c._create_class_instance(SimpleService),
        ScopeType.PROTOTYPE, "test", type_=SimpleService,
    ))
    ctx.register(Definition(
        "db_dep", lambda c: Database(),
        ScopeType.SINGLETON, "test", type_=Database,
    ))
    ctx.refresh()

    inst1 = ctx.get("prototype_svc")
    inst2 = ctx.get("prototype_svc")
    assert inst1 is not inst2
    assert isinstance(inst1.database, Database)
    assert isinstance(inst2.database, Database)

    # Both are independently frozen
    with pytest.raises(_ImmutableAttributeError):
        inst1.database = "hacked"

    # Use TestContext on one — does not affect the other
    db1 = Database()
    TestContext.mock_permanently(inst1, "database", db1)
    assert inst1.database is db1
    assert isinstance(inst2.database, Database)
    assert inst2.database is not db1


# ── 9. Identity preservation ──────────────────────────────────────────

def test_frozen_isinstance_unchanged():
    """isinstance() still works after freezing."""
    ctx = ApplicationContext()
    ctx.register(Definition(
        "db_dep", lambda c: Database(),
        ScopeType.SINGLETON, "test", type_=Database,
    ))
    svc = _make_frozen_instance(ctx, SimpleService, "IdentSvc")
    assert isinstance(svc, SimpleService)
    assert type(svc).__name__ == "SimpleService"


def test_frozen_repr_unchanged():
    """type name unchanged after freezing."""
    ctx = ApplicationContext()
    ctx.register(Definition(
        "db_dep", lambda c: Database(),
        ScopeType.SINGLETON, "test", type_=Database,
    ))
    svc = _make_frozen_instance(ctx, SimpleService, "ReprSvc")
    assert "SimpleService" in repr(svc) or "SimpleService" in str(type(svc))


# ── 10. Full freeze rules table validation ────────────────────────────

class FullFreezeService:
    # 1. Constructor required
    required_dep: Database
    # 2. Constructor optional (resolved)
    optional_resolved: CacheService = None
    # 3. Constructor optional (not registered) — see optional test above
    # 4. Constructor literal — see optional test above
    # 5. Inject() required
    inject_required: RepoService = Inject()
    # 6. Inject(required=False) resolved
    inject_optional: MixinDep = Inject(required=False)
    # 7. InjectByName
    named = InjectByName("NamedDep")
    # 8. Lazy
    lazy_dep: LazyDep = Lazy()


def test_frozen_all_styles():
    """All 8 injection styles from the freeze rules table are enforced."""
    ctx = ApplicationContext()
    ctx.register(Definition("required_dep", lambda c: Database(),
                            ScopeType.SINGLETON, "test", type_=Database))
    ctx.register(Definition("optional_resolved", lambda c: CacheService(),
                            ScopeType.SINGLETON, "test", type_=CacheService))
    ctx.register(Definition("inject_required", lambda c: RepoService(),
                            ScopeType.SINGLETON, "test", type_=RepoService))
    ctx.register(Definition("inject_optional", lambda c: MixinDep(),
                            ScopeType.SINGLETON, "test", type_=MixinDep))
    ctx.register(Definition("NamedDep", lambda c: NamedDep(),
                            ScopeType.SINGLETON, "test", type_=NamedDep))
    ctx.register(Definition("lazy_dep", lambda c: LazyDep(),
                            ScopeType.SINGLETON, "test", type_=LazyDep))

    svc = _make_frozen_instance(ctx, FullFreezeService, "FullSvc")

    # Verify injection
    assert isinstance(svc.required_dep, Database)
    assert isinstance(svc.optional_resolved, CacheService)
    assert isinstance(svc.inject_required, RepoService)
    assert isinstance(svc.inject_optional, MixinDep)
    assert isinstance(svc.named, NamedDep)
    assert isinstance(svc.lazy_dep, _LazyProxy)

    # Every injected attribute is frozen (Lazy proxy is frozen too)
    for attr in ("required_dep", "optional_resolved", "inject_required",
                  "inject_optional", "named", "lazy_dep"):
        with pytest.raises(_ImmutableAttributeError, match=attr):
            setattr(svc, attr, "hacked")
