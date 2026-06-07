"""Tests for the annotations_hook module and string annotation normalization."""
import os
import sys
import tempfile
import importlib
import pytest

from cullinan.runtime.annotations_hook import (
    install_annotations_hook,
    uninstall_annotations_hook,
    is_annotations_hook_installed,
    get_hook_root_path,
    _is_subpath,
    _resolve_app_root_path,
    _AnnotationsFinder,
)
from cullinan.core.application_context import _normalize_string_annotation


# ── _normalize_string_annotation ────────────────────────────────────────

def test_normalize_plain_string_unchanged():
    assert _normalize_string_annotation("UserService") == "UserService"
    assert _normalize_string_annotation("Optional[int]") == "Optional[int]"


def test_normalize_single_quoted_string_unwrapped():
    assert _normalize_string_annotation("'UserService'") == "UserService"


def test_normalize_double_quoted_string_unwrapped():
    assert _normalize_string_annotation('"UserService"') == "UserService"


def test_normalize_non_string_passthrough():
    assert _normalize_string_annotation(42) == 42
    assert _normalize_string_annotation(None) is None
    assert _normalize_string_annotation(int) is int


def test_normalize_empty_string_passthrough():
    assert _normalize_string_annotation("") == ""


def test_normalize_mixed_quotes_not_unwrapped():
    # 'UserService" — different start/end quotes → keep
    assert _normalize_string_annotation("'UserService\"") == "'UserService\""


def test_normalize_whitespace_stripped():
    assert _normalize_string_annotation("  'UserService'  ") == "UserService"


def test_normalize_pep563_wrapped_string():
    """CO_FUTURE_ANNOTATIONS wraps `x: "UserService"` → `'\"UserService\"'`."""
    # repr('"UserService"') gives '\'"UserService"\'' which is the string
    # 'UserService' (with quotes). The normalize function should recursively
    # strip quotes until a bare name remains.
    wrapped = "'\"UserService\"'"
    assert _normalize_string_annotation(wrapped) == "UserService"


# ── _is_subpath ─────────────────────────────────────────────────────────

def test_is_subpath_identical():
    assert _is_subpath("/a/b", "/a/b") is True


def test_is_subpath_child():
    assert _is_subpath("/a/b/c", "/a/b") is True


def test_is_subpath_not_child():
    assert _is_subpath("/a/other", "/a/b") is False


def test_is_subpath_parent():
    assert _is_subpath("/a", "/a/b") is False


def test_is_subpath_windows_separator():
    assert _is_subpath(r"C:\a\b\c", r"C:\a\b") is True


# ── Hook lifecycle ──────────────────────────────────────────────────────

def test_hook_not_installed_initially():
    assert not is_annotations_hook_installed()
    assert get_hook_root_path() is None


def test_hook_install_and_uninstall(tmp_path):
    root = str(tmp_path)
    install_annotations_hook(root)
    try:
        assert is_annotations_hook_installed()
        assert get_hook_root_path() == root
        # Double install is idempotent
        install_annotations_hook(root)
        assert is_annotations_hook_installed()
    finally:
        uninstall_annotations_hook()

    assert not is_annotations_hook_installed()
    # Double uninstall is safe
    uninstall_annotations_hook()
    assert not is_annotations_hook_installed()


def test_hook_only_intercepts_target_package(tmp_path):
    """The hook must only intercept modules under the target root."""
    root = str(tmp_path)
    app_dir = os.path.join(tmp_path, "myapp")
    os.makedirs(app_dir, exist_ok=True)
    with open(os.path.join(app_dir, "__init__.py"), "w") as f:
        f.write("")

    with open(os.path.join(app_dir, "mod_a.py"), "w") as f:
        f.write("""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from myapp.mod_b import SomeClass

class WithTypeCheck:
    svc: SomeClass
""")

    with open(os.path.join(app_dir, "mod_b.py"), "w") as f:
        f.write("class SomeClass:\n    pass\n")

    sys.path.insert(0, str(tmp_path))

    # Without hook: should fail with NameError (no from __future__)
    for k in list(sys.modules):
        if k.startswith("myapp"):
            del sys.modules[k]
    try:
        try:
            importlib.import_module("myapp.mod_a")
            assert False, "Expected NameError"
        except NameError:
            pass  # expected
    finally:
        # Clean up
        for k in list(sys.modules):
            if k.startswith("myapp"):
                del sys.modules[k]

    # With hook: should succeed with string annotations
    install_annotations_hook(app_dir)
    try:
        mod = importlib.import_module("myapp.mod_a")
        ann = mod.WithTypeCheck.__annotations__.get("svc")
        assert isinstance(ann, str), f"Expected str annotation, got {type(ann)}"
        # The annotation should be the class name, not a quoted string literal
        assert ann == "SomeClass", f"Expected 'SomeClass', got {ann!r}"
    finally:
        uninstall_annotations_hook()
        sys.path.remove(str(root))
        for k in list(sys.modules):
            if k.startswith("myapp"):
                del sys.modules[k]


def test_hook_does_not_intercept_framework(tmp_path):
    """Cullinan modules must never be affected by the hook."""
    root = str(tmp_path)
    install_annotations_hook(root)
    try:
        # Import a Cullinan module — this must succeed normally
        # and NOT be affected by the hook (which targets the tmp path).
        import cullinan.core.application_context as ctx
        assert ctx is not None
    finally:
        uninstall_annotations_hook()


def test_construct_injection_via_application_run(tmp_path):
    """End-to-end: Application.run() with hook auto-injected."""
    root = str(tmp_path)
    app_dir = os.path.join(tmp_path, "e2eapp")
    os.makedirs(app_dir, exist_ok=True)
    with open(os.path.join(app_dir, "__init__.py"), "w") as f:
        f.write("")

    with open(os.path.join(app_dir, "services.py"), "w") as f:
        f.write("""
from cullinan import service

@service
class GreetingService:
    def greet(self):
        return "hello from e2e"
""")

    with open(os.path.join(app_dir, "controllers.py"), "w") as f:
        f.write("""
from typing import TYPE_CHECKING
from cullinan import controller

if TYPE_CHECKING:
    from e2eapp.services import GreetingService

@controller(url="/e2e")
class E2EController:
    greeter: GreetingService
""")

    with open(os.path.join(app_dir, "root.py"), "w") as f:
        f.write("""
from cullinan import module

@module(packages=["e2eapp"])
class E2ERoot:
    pass
""")

    sys.path.insert(0, str(tmp_path))
    try:
        from cullinan.application import Application
        
        mod = importlib.import_module("e2eapp.root")
        app = Application.run(mod.E2ERoot)
        svc = app.context.get("GreetingService")
        assert svc.greet() == "hello from e2e"
    finally:
        sys.path.remove(str(root))
        for k in list(sys.modules):
            if k.startswith("e2eapp"):
                del sys.modules[k]
        # Reset registries
        from cullinan.core.pending import PendingRegistry
        from cullinan.core import set_application_context
        from cullinan.web.controller.registry import reset_controller_registry
        from cullinan.core.services.registry import reset_service_registry
        PendingRegistry.reset()
        reset_controller_registry()
        reset_service_registry()
        set_application_context(None)


def test_hook_intercepts_nested_subpackages(tmp_path):
    """Hook must intercept modules in nested sub-packages."""
    root = str(tmp_path)
    app_dir = os.path.join(tmp_path, "nestapp")
    sub_dir = os.path.join(app_dir, "sub", "deep")
    os.makedirs(sub_dir, exist_ok=True)

    # Create package __init__.py files
    with open(os.path.join(app_dir, "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(app_dir, "sub", "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(sub_dir, "__init__.py"), "w") as f:
        f.write("")

    # A service in the deep sub-package
    with open(os.path.join(sub_dir, "services.py"), "w") as f:
        f.write("\nclass DeepService:\n    def name(self):\n        return 'deep'\n")

    # A module that references it with TYPE_CHECKING + bare annotation
    with open(os.path.join(sub_dir, "consumers.py"), "w") as f:
        f.write("\nfrom typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from nestapp.sub.deep.services import DeepService\n\nclass DeepConsumer:\n    svc: DeepService\n")

    sys.path.insert(0, str(tmp_path))
    try:
        # Without hook: should fail with NameError
        for k in list(sys.modules):
            if k.startswith("nestapp"):
                del sys.modules[k]
        try:
            importlib.import_module("nestapp.sub.deep.consumers")
            assert False, "Expected NameError without hook"
        except NameError:
            pass

        # With hook: should succeed with string annotation
        install_annotations_hook(app_dir)
        for k in list(sys.modules):
            if k.startswith("nestapp"):
                del sys.modules[k]
        try:
            mod = importlib.import_module("nestapp.sub.deep.consumers")
            ann = mod.DeepConsumer.__annotations__.get("svc")
            assert isinstance(ann, str), f"Expected str, got {type(ann)}"
            assert ann == "DeepService", f"Expected 'DeepService', got {ann!r}"
        finally:
            uninstall_annotations_hook()
    finally:
        sys.path.remove(str(root))
        for k in list(sys.modules):
            if k.startswith("nestapp"):
                del sys.modules[k]


def test_resolve_app_root_path_from_file(tmp_path):
    """_resolve_app_root_path must resolve package dir from a module with __file__."""
    pkg_dir = os.path.join(tmp_path, "resolveapp")
    os.makedirs(pkg_dir, exist_ok=True)
    with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
        f.write("class RootModule:\n    pass\n")

    sys.path.insert(0, str(tmp_path))
    try:
        mod = importlib.import_module("resolveapp")
        result = _resolve_app_root_path(mod.RootModule)
        assert result is not None, "Should resolve path"
        assert os.path.isdir(result), f"Expected dir, got {result}"
        # Result should be the package directory
        assert os.path.basename(result) == "resolveapp"
    finally:
        sys.path.remove(str(tmp_path))
        for k in list(sys.modules):
            if k.startswith("resolveapp"):
                del sys.modules[k]


def test_resolve_app_root_path_returns_none_for_unresolvable():
    """_resolve_app_root_path returns None when path can't be determined."""
    # A class defined at REPL or without __module__ in sys.modules
    class FakeModule:
        __module__ = "nonexistent_module_xyz"
    
    result = _resolve_app_root_path(FakeModule)
    assert result is None, f"Expected None for unresolvable, got {result!r}"
