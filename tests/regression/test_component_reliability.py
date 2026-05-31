import importlib
import textwrap

import pytest

from cullinan.application import _validate_component_scan_results, scan_service
from cullinan.core import ApplicationContext, PendingRegistry
from cullinan.core.exceptions import DependencyTypeResolutionError
from cullinan.exceptions import PackageDiscoveryError


@pytest.fixture(autouse=True)
def reset_pending_registry():
    PendingRegistry.reset()
    yield
    PendingRegistry.reset()


def test_scan_validation_surfaces_module_import_failures(tmp_path, monkeypatch):
    package_dir = tmp_path / "scanpkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "healthy.py").write_text(
        "from cullinan import service\n@service()\nclass HealthyService:\n    pass\n",
        encoding="utf-8",
    )
    (package_dir / "broken.py").write_text(
        "raise RuntimeError('boom during import')\n",
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    modules = ["scanpkg.healthy", "scanpkg.broken"]
    scan_results = scan_service(modules)

    with pytest.raises(PackageDiscoveryError) as exc_info:
        _validate_component_scan_results(modules, scan_results)

    error_message = str(exc_info.value)
    assert "scanpkg.broken" in error_message
    assert "boom during import" in error_message


def test_scan_validation_detects_missing_pending_registration(tmp_path, monkeypatch):
    package_dir = tmp_path / "regpkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "services.py").write_text(
        "from cullinan import service\n@service()\nclass HealthyService:\n    pass\n",
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    modules = ["regpkg.services"]
    scan_results = scan_service(modules)

    pending = PendingRegistry.get_instance()
    pending.clear()

    with pytest.raises(PackageDiscoveryError) as exc_info:
        _validate_component_scan_results(modules, scan_results)

    error_message = str(exc_info.value)
    assert "HealthyService" in error_message
    assert "PendingRegistry" in error_message


def test_refresh_fails_when_type_checking_dependency_cannot_resolve(tmp_path, monkeypatch):
    package_dir = tmp_path / "typehintpkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "repository.py").write_text(
        textwrap.dedent(
            """
            from typing import TYPE_CHECKING

            from cullinan import Inject, service

            if TYPE_CHECKING:
                from .providers import DatabaseSessionProvider


            @service()
            class ChannelBindingRepository:
                session_provider: "DatabaseSessionProvider" = Inject()
            """
        ),
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.import_module("typehintpkg.repository")

    ctx = ApplicationContext()

    with pytest.raises(DependencyTypeResolutionError) as exc_info:
        ctx.refresh()

    error_message = str(exc_info.value)
    assert "ChannelBindingRepository" in error_message
    assert "session_provider" in error_message
    assert "DatabaseSessionProvider" in error_message
    assert "SessionProvider" in error_message
