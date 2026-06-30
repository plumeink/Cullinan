# -*- coding: utf-8 -*-
"""TestContext immutability bypass tests.

Covers mock_permanently, mock() context manager, restore behaviour,
and integration with frozen instances.
"""

import pytest

from cullinan.core.application_context import (
    ApplicationContext,
    _ImmutableAttributeError,
)
from cullinan.core.definitions import Definition, ScopeType
from cullinan.testing import TestContext


# ── Helpers ───────────────────────────────────────────────────────────

class DepA:
    pass


class TargetService:
    a: DepA


def _make_frozen_svc():
    ctx = ApplicationContext()
    ctx.register(Definition(
        "a_dep", lambda c: DepA(),
        ScopeType.SINGLETON, "test", type_=DepA,
    ))
    ctx.register(Definition(
        name="Target",
        factory=lambda c: c._create_class_instance(TargetService),
        scope=ScopeType.SINGLETON,
        source="test",
        type_=TargetService,
    ))
    ctx.refresh()
    return ctx.get("Target")


# ── mock_permanently ──────────────────────────────────────────────────

def test_mock_permanently_basic():
    svc = _make_frozen_svc()
    original = svc.a

    new_a = DepA()
    TestContext.mock_permanently(svc, "a", new_a)
    assert svc.a is new_a
    assert svc.a is not original


def test_mock_permanently_on_non_frozen_attr():
    svc = _make_frozen_svc()
    TestContext.mock_permanently(svc, "custom_field", 42)
    assert svc.custom_field == 42


def test_mock_permanently_does_not_unfreeze():
    """After mock_permanently, the frozen __setattr__ still rejects reassignment."""
    svc = _make_frozen_svc()
    new_a = DepA()
    TestContext.mock_permanently(svc, "a", new_a)

    with pytest.raises(_ImmutableAttributeError):
        svc.a = DepA()


# ── mock() context manager ────────────────────────────────────────────

def test_mock_context_manager_basic():
    svc = _make_frozen_svc()
    original = svc.a

    temp = DepA()
    with TestContext.mock(svc, "a", temp):
        assert svc.a is temp

    assert svc.a is original


def test_mock_context_manager_restores_on_exception():
    svc = _make_frozen_svc()
    original = svc.a

    temp = DepA()
    try:
        with TestContext.mock(svc, "a", temp):
            assert svc.a is temp
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    assert svc.a is original


def test_mock_context_manager_nesting():
    svc = _make_frozen_svc()
    original = svc.a

    a1 = DepA()
    a2 = DepA()

    with TestContext.mock(svc, "a", a1):
        assert svc.a is a1
        with TestContext.mock(svc, "a", a2):
            assert svc.a is a2
        assert svc.a is a1

    assert svc.a is original


def test_mock_context_manager_non_frozen_attr():
    """mock() on a non-frozen attr restores original after exit."""
    svc = _make_frozen_svc()
    svc.custom = "original"

    with TestContext.mock(svc, "custom", "temp"):
        assert svc.custom == "temp"

    assert svc.custom == "original"


# ── mock() on non-frozen instance ─────────────────────────────────────

def test_mock_on_plain_instance():
    """TestContext.mock works on non-frozen instances too."""
    svc = TargetService()
    svc.a = DepA()
    original = svc.a

    temp = DepA()
    with TestContext.mock(svc, "a", temp):
        assert svc.a is temp

    assert svc.a is original
