import importlib
import textwrap
import warnings

import pytest

from cullinan import Provider
from cullinan.application import _validate_component_scan_results, scan_service
from cullinan.core import (
    ApplicationContext,
    PendingRegistry,
    CompatibilitySemanticWarning,
    ComponentDiscoveryWarning,
    InjectionSemanticWarning,
    get_injection_registry,
    injectable,
)
from cullinan.core.exceptions import DependencyNotFoundError, DependencyTypeResolutionError
from cullinan.core.semantic_rules import reset_semantic_warnings
from cullinan.support.exceptions import PackageDiscoveryError


@pytest.fixture(autouse=True)
def reset_pending_registry():
    PendingRegistry.reset()
    reset_semantic_warnings()
    yield
    PendingRegistry.reset()
    reset_semantic_warnings()


def _write_module(path, source: str) -> None:
    path.write_text(textwrap.dedent(source), encoding="utf-8")


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
    assert "Semantic rule" in error_message
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
    assert "module-top-level" in error_message


def test_refresh_resolves_type_checking_forward_reference(tmp_path, monkeypatch):
    package_dir = tmp_path / "typehintpkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    _write_module(
        package_dir / "providers.py",
        """
        from cullinan import service


        @service()
        class DatabaseSessionProvider:
            pass
        """,
    )
    _write_module(
        package_dir / "repository.py",
        """
        from typing import TYPE_CHECKING

        from cullinan import Inject, service

        if TYPE_CHECKING:
            from .providers import DatabaseSessionProvider


        @service()
        class ChannelBindingRepository:
            session_provider: "DatabaseSessionProvider" = Inject()
        """,
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.import_module("typehintpkg.providers")
    importlib.import_module("typehintpkg.repository")

    ctx = ApplicationContext()
    ctx.refresh()

    repository = ctx.get("ChannelBindingRepository")
    session_provider = ctx.get("DatabaseSessionProvider")

    assert repository.session_provider is session_provider


def test_refresh_surfaces_missing_type_checking_dependency_with_diagnostics(tmp_path, monkeypatch):
    package_dir = tmp_path / "typehintmissingpkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    _write_module(
        package_dir / "repository.py",
        """
        from typing import TYPE_CHECKING

        from cullinan import Inject, service

        if TYPE_CHECKING:
            from .providers import DatabaseSessionProvider


        @service()
        class ChannelBindingRepository:
            session_provider: "DatabaseSessionProvider" = Inject()
        """,
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.import_module("typehintmissingpkg.repository")

    ctx = ApplicationContext()

    with pytest.raises(DependencyNotFoundError) as exc_info:
        ctx.refresh()

    error_message = str(exc_info.value)
    assert "ChannelBindingRepository" in error_message
    assert "session_provider" in error_message
    assert "DatabaseSessionProvider" in error_message


def test_refresh_supports_provider_optional_and_collection_wrappers(tmp_path, monkeypatch):
    package_dir = tmp_path / "advancedtypepkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    _write_module(
        package_dir / "contracts.py",
        """
        class Hook:
            pass
        """,
    )
    _write_module(
        package_dir / "providers.py",
        """
        from .contracts import Hook
        from cullinan import service


        @service()
        class DatabaseSessionProvider:
            pass


        @service()
        class AuditHook(Hook):
            pass


        @service()
        class MetricsHook(Hook):
            pass
        """,
    )
    _write_module(
        package_dir / "repository.py",
        """
        from typing import TYPE_CHECKING, Optional

        from cullinan import Inject, Provider, service

        if TYPE_CHECKING:
            from .contracts import Hook
            from .providers import DatabaseSessionProvider


        @service()
        class ChannelBindingRepository:
            session_provider: Provider["DatabaseSessionProvider"] = Inject()
            hooks: list["Hook"] = Inject()
            optional_cache: Optional["CacheService"] = Inject()
        """,
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.import_module("advancedtypepkg.providers")
    importlib.import_module("advancedtypepkg.repository")

    ctx = ApplicationContext()
    ctx.refresh()

    repository = ctx.get("ChannelBindingRepository")

    assert isinstance(repository.session_provider, Provider)
    assert repository.session_provider.get() is ctx.get("DatabaseSessionProvider")
    assert {type(item).__name__ for item in repository.hooks} == {"AuditHook", "MetricsHook"}
    assert repository.optional_cache is None


def test_refresh_supports_union_when_only_one_candidate_is_available(tmp_path, monkeypatch):
    package_dir = tmp_path / "unionpkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    _write_module(
        package_dir / "providers.py",
        """
        from cullinan import service


        @service()
        class PrimarySessionProvider:
            pass
        """,
    )
    _write_module(
        package_dir / "repository.py",
        """
        from typing import TYPE_CHECKING

        from cullinan import Inject, service

        if TYPE_CHECKING:
            from .providers import PrimarySessionProvider, SecondarySessionProvider


        @service()
        class ChannelBindingRepository:
            session_provider: "PrimarySessionProvider | SecondarySessionProvider" = Inject()
        """,
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.import_module("unionpkg.providers")
    importlib.import_module("unionpkg.repository")

    ctx = ApplicationContext()
    ctx.refresh()

    repository = ctx.get("ChannelBindingRepository")
    assert type(repository.session_provider).__name__ == "PrimarySessionProvider"


def test_refresh_rejects_union_when_multiple_candidates_are_available(tmp_path, monkeypatch):
    package_dir = tmp_path / "unionambiguouspkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    _write_module(
        package_dir / "providers.py",
        """
        from cullinan import service


        @service()
        class PrimarySessionProvider:
            pass


        @service()
        class SecondarySessionProvider:
            pass
        """,
    )
    _write_module(
        package_dir / "repository.py",
        """
        from typing import TYPE_CHECKING

        from cullinan import Inject, service

        if TYPE_CHECKING:
            from .providers import PrimarySessionProvider, SecondarySessionProvider


        @service()
        class ChannelBindingRepository:
            session_provider: "PrimarySessionProvider | SecondarySessionProvider" = Inject()
        """,
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.import_module("unionambiguouspkg.providers")
    importlib.import_module("unionambiguouspkg.repository")

    ctx = ApplicationContext()

    with pytest.raises(DependencyTypeResolutionError) as exc_info:
        ctx.refresh()

    error_message = str(exc_info.value)
    assert "PrimarySessionProvider" in error_message
    assert "SecondarySessionProvider" in error_message
    assert "Semantic rule" in error_message


def test_local_component_definition_emits_semantic_warning():
    from cullinan import component
    from cullinan.core.decorators import get_component_registration_metadata

    def build_component():
        @component
        class LocalComponent:
            pass

        return LocalComponent

    local_cls = build_component()
    metadata = get_component_registration_metadata(local_cls)
    assert metadata is not None
    assert metadata["is_top_level"] is False
    assert "<locals>" in metadata["source_qualname"]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ctx = ApplicationContext()
        ctx.refresh()

    assert any(item.category is ComponentDiscoveryWarning for item in caught)
    assert any("module top level" in str(item.message) for item in caught)


def test_local_component_definition_after_refresh_fails_with_semantic_message():
    from cullinan import component

    ctx = ApplicationContext()
    ctx.refresh()

    with pytest.raises(RuntimeError) as exc_info:
        def build_component():
            @component
            class LateComponent:
                pass

            return LateComponent

        build_component()

    message = str(exc_info.value)
    assert "Semantic rule" in message
    assert "refresh()" in message
    assert "module top level" in message


def test_refresh_warns_for_name_based_injection_without_explicit_name_or_type(tmp_path, monkeypatch):
    package_dir = tmp_path / "namebasedpkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    _write_module(
        package_dir / "services.py",
        """
        from typing import Any

        from cullinan import InjectByName, service


        @service()
        class EmailService:
            pass


        @service()
        class ConsumerService:
            EmailService: Any = InjectByName()
        """,
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.import_module("namebasedpkg.services")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ctx = ApplicationContext()
        ctx.refresh()

    consumer = ctx.get("ConsumerService")
    assert consumer.EmailService is ctx.get("EmailService")
    assert any(item.category is InjectionSemanticWarning for item in caught)
    assert any("InjectByName()" in str(item.message) for item in caught)


def test_compatibility_api_emits_semantic_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")

        @injectable
        class LegacyService:
            pass

        registry = get_injection_registry()

    assert LegacyService.__name__ == "LegacyService"
    assert registry is None
    assert any(item.category is CompatibilitySemanticWarning for item in caught)
    assert any("Compatibility APIs" in str(item.message) for item in caught)
