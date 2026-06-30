"""
Test TYPE_CHECKING + constructor injection scenarios.

Verifies that bare annotation constructor injection works correctly with:
1. from __future__ import annotations + TYPE_CHECKING (should work)
2. Without from __future__ + TYPE_CHECKING (should fail with NameError)
3. Direct import (should always work)
"""
import sys
import tempfile
import os
import importlib


def _cleanup(*prefixes):
    """Clean up sys.modules and reset container state."""
    for k in list(sys.modules):
        for p in prefixes:
            if k == p or k.startswith(p + "."):
                del sys.modules[k]
    # Reset container state to avoid cross-test pollution.
    from cullinan.core.pending import PendingRegistry
    from cullinan.core import set_application_context
    from cullinan.web.controller.registry import reset_controller_registry
    from cullinan.core.services.registry import reset_service_registry
    PendingRegistry.reset()
    reset_controller_registry()
    reset_service_registry()
    set_application_context(None)


def test_type_checking_with_future():
    """from __future__ import annotations + TYPE_CHECKING -> should work."""
    tmp_dir = tempfile.mkdtemp()
    sys.path.insert(0, tmp_dir)
    try:
        # Same package: svc and controller under same parent
        os.makedirs(os.path.join(tmp_dir, "pkg_a"), exist_ok=True)
        with open(os.path.join(tmp_dir, "pkg_a", "__init__.py"), "w") as f:
            f.write("")

        with open(os.path.join(tmp_dir, "pkg_a", "services.py"), "w", encoding="utf-8") as f:
            f.write(
                "from cullinan import service\n"
                "@service\n"
                "class UserService:\n"
                "    def __init__(self):\n"
                "        self.name = 'UserService_TC'\n"
            )

        with open(os.path.join(tmp_dir, "pkg_a", "root.py"), "w", encoding="utf-8") as f:
            f.write(
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n"
                "from cullinan import controller, module\n"
                "if TYPE_CHECKING:\n"
                "    from pkg_a.services import UserService\n"
                "@controller(url='/test')\n"
                "class UserController:\n"
                "    user_service: UserService\n"
                "@module\n"
                "class RootModule:\n"
                "    pass\n"
            )

        mod = importlib.import_module("pkg_a.root")
        from cullinan.application import Application

        app = Application.run(mod.RootModule)
        svc = app.context.get("UserService")
        assert svc.name == "UserService_TC", f"expected UserService_TC, got {svc.name}"
        print("  TEST A PASS: from __future__ + TYPE_CHECKING + bare annotation")
    finally:
        sys.path.remove(tmp_dir)
        _cleanup("pkg_a")


def test_type_checking_without_future():
    """Without from __future__ + TYPE_CHECKING -> should raise NameError."""
    tmp_dir = tempfile.mkdtemp()
    sys.path.insert(0, tmp_dir)
    try:
        os.makedirs(os.path.join(tmp_dir, "pkg_b"), exist_ok=True)
        with open(os.path.join(tmp_dir, "pkg_b", "__init__.py"), "w") as f:
            f.write("")

        with open(os.path.join(tmp_dir, "pkg_b", "services.py"), "w", encoding="utf-8") as f:
            f.write(
                "from cullinan import service\n"
                "@service\n"
                "class UserService:\n"
                "    def __init__(self):\n"
                "        self.name = 'UserService_TC2'\n"
            )

        with open(os.path.join(tmp_dir, "pkg_b", "root.py"), "w", encoding="utf-8") as f:
            f.write(
                "from typing import TYPE_CHECKING\n"
                "from cullinan import controller, module\n"
                "if TYPE_CHECKING:\n"
                "    from pkg_b.services import UserService\n"
                "@controller(url='/test')\n"
                "class UserController:\n"
                "    user_service: UserService\n"
                "@module\n"
                "class RootModule:\n"
                "    pass\n"
            )

        try:
            mod = importlib.import_module("pkg_b.root")
            print("  TEST B FAIL: no NameError - should have failed!")
            assert False, "Expected NameError but module imported successfully"
        except NameError as e:
            print(f"  TEST B PASS: NameError correctly raised (no from __future__): {e}")
        except Exception as e:
            print(f"  TEST B UNEXPECTED: {type(e).__name__}: {e}")
            raise
    finally:
        sys.path.remove(tmp_dir)
        _cleanup("pkg_b")


def test_direct_import():
    """Direct import (no TYPE_CHECKING) -> should always work."""
    tmp_dir = tempfile.mkdtemp()
    sys.path.insert(0, tmp_dir)
    try:
        os.makedirs(os.path.join(tmp_dir, "pkg_c"), exist_ok=True)
        with open(os.path.join(tmp_dir, "pkg_c", "__init__.py"), "w") as f:
            f.write("")

        with open(os.path.join(tmp_dir, "pkg_c", "services.py"), "w", encoding="utf-8") as f:
            f.write(
                "from cullinan import service\n"
                "@service\n"
                "class UserService:\n"
                "    def __init__(self):\n"
                "        self.name = 'UserService_Direct'\n"
            )

        with open(os.path.join(tmp_dir, "pkg_c", "root.py"), "w", encoding="utf-8") as f:
            f.write(
                "from pkg_c.services import UserService\n"
                "from cullinan import controller, module\n"
                "@controller(url='/test')\n"
                "class UserController:\n"
                "    user_service: UserService\n"
                "@module\n"
                "class RootModule:\n"
                "    pass\n"
            )

        mod = importlib.import_module("pkg_c.root")
        from cullinan.application import Application

        app = Application.run(mod.RootModule)
        svc = app.context.get("UserService")
        assert svc.name == "UserService_Direct"
        print("  TEST C PASS: direct import + bare annotation")
    finally:
        sys.path.remove(tmp_dir)
        _cleanup("pkg_c")


if __name__ == "__main__":
    print("\n=== TYPE_CHECKING + Constructor Injection Tests ===\n")
    test_type_checking_with_future()
    test_type_checking_without_future()
    test_direct_import()
    print("\n=== ALL TESTS DONE ===")
