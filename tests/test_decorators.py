# -*- coding: utf-8 -*-
"""Tests for core decorators.

Author: Plumeink
"""

import pytest
from cullinan.core.pending import PendingRegistry, ComponentType
from cullinan.core.decorators import (
    service,
    controller,
    component,
    provider,
    Inject,
    InjectByName,
    Lazy,
    get_injection_markers,
)


class TestServiceDecorator:
    """Tests for @service decorator."""

    def setup_method(self):
        PendingRegistry.reset()

    def teardown_method(self):
        PendingRegistry.reset()

    def test_basic_service(self):
        """Test basic service registration."""
        @service()
        class UserService:
            pass

        registry = PendingRegistry.get_instance()
        assert registry.count == 1

        reg = registry.get_by_name("UserService")
        assert reg is not None
        assert reg.cls is UserService
        assert reg.component_type == ComponentType.SERVICE
        assert reg.scope == "singleton"

    def test_service_with_custom_name(self):
        """Test service with custom name."""
        @service(name="customUserService")
        class UserService:
            pass

        registry = PendingRegistry.get_instance()
        reg = registry.get_by_name("customUserService")
        assert reg is not None
        assert reg.cls is UserService

    def test_service_with_dependencies(self):
        """Test service with explicit dependencies."""
        @service(dependencies=["EmailService", "CacheService"])
        class UserService:
            pass

        registry = PendingRegistry.get_instance()
        reg = registry.get_by_name("UserService")
        assert reg.dependencies == ["EmailService", "CacheService"]

    def test_service_with_prototype_scope(self):
        """Test service with prototype scope."""
        @service(scope="prototype")
        class RequestHandler:
            pass

        registry = PendingRegistry.get_instance()
        reg = registry.get_by_name("RequestHandler")
        assert reg.scope == "prototype"

    def test_service_source_location(self):
        """Test that source location is captured."""
        @service()
        class LocationTestService:
            pass

        registry = PendingRegistry.get_instance()
        reg = registry.get_by_name("LocationTestService")
        assert reg.source_file is not None
        assert reg.source_line is not None
        assert "test_decorators.py" in reg.source_file


class TestControllerDecorator:
    """Tests for @controller decorator."""

    def setup_method(self):
        PendingRegistry.reset()

    def teardown_method(self):
        PendingRegistry.reset()

    def test_basic_controller(self):
        """Test basic controller registration."""
        @controller(url="/api/users")
        class UserController:
            pass

        registry = PendingRegistry.get_instance()
        assert registry.count == 1

        reg = registry.get_by_name("UserController")
        assert reg is not None
        assert reg.cls is UserController
        assert reg.component_type == ComponentType.CONTROLLER
        assert reg.url_prefix == "/api/users"
        assert reg.scope == "singleton"

    def test_controller_empty_url(self):
        """Test controller with empty URL."""
        @controller()
        class RootController:
            pass

        registry = PendingRegistry.get_instance()
        reg = registry.get_by_name("RootController")
        assert reg.url_prefix == ""


class TestComponentDecorator:
    """Tests for @component decorator."""

    def setup_method(self):
        PendingRegistry.reset()

    def teardown_method(self):
        PendingRegistry.reset()

    def test_basic_component(self):
        """Test basic component registration."""
        @component()
        class CacheManager:
            pass

        registry = PendingRegistry.get_instance()
        reg = registry.get_by_name("CacheManager")
        assert reg is not None
        assert reg.component_type == ComponentType.COMPONENT
        assert reg.scope == "singleton"

    def test_component_with_custom_name_and_scope(self):
        """Test component with custom name and scope."""
        @component(name="myCache", scope="prototype")
        class CacheManager:
            pass

        registry = PendingRegistry.get_instance()
        reg = registry.get_by_name("myCache")
        assert reg is not None
        assert reg.scope == "prototype"


class TestProviderDecorator:
    """Tests for @provider decorator."""

    def setup_method(self):
        PendingRegistry.reset()

    def teardown_method(self):
        PendingRegistry.reset()

    def test_basic_provider(self):
        """Test basic provider registration."""
        @provider()
        class DatabaseProvider:
            pass

        registry = PendingRegistry.get_instance()
        reg = registry.get_by_name("DatabaseProvider")
        assert reg is not None
        assert reg.component_type == ComponentType.PROVIDER


class TestInjectionMarkers:
    """Tests for injection marker classes."""

    def test_inject_defaults(self):
        """Test Inject with default values."""
        marker = Inject()
        assert marker.required is True

    def test_inject_optional(self):
        """Test optional Inject."""
        marker = Inject(required=False)
        assert marker.required is False

    def test_inject_repr(self):
        """Test Inject string representation."""
        assert "required=True" in repr(Inject())
        assert "required=False" in repr(Inject(required=False))

    def test_inject_by_name_defaults(self):
        """Test InjectByName with defaults."""
        marker = InjectByName()
        assert marker.name is None
        assert marker.required is True

    def test_inject_by_name_explicit(self):
        """Test InjectByName with explicit name."""
        marker = InjectByName("UserService")
        assert marker.name == "UserService"
        assert marker.required is True

    def test_inject_by_name_repr(self):
        """Test InjectByName string representation."""
        assert "'UserService'" in repr(InjectByName("UserService"))
        assert "required=False" in repr(InjectByName(required=False))

    def test_lazy_defaults(self):
        """Test Lazy with defaults."""
        marker = Lazy()
        assert marker.name is None

    def test_lazy_explicit(self):
        """Test Lazy with explicit name."""
        marker = Lazy("ServiceB")
        assert marker.name == "ServiceB"

    def test_lazy_repr(self):
        """Test Lazy string representation."""
        assert "Lazy()" == repr(Lazy())
        assert "'ServiceB'" in repr(Lazy("ServiceB"))


class TestGetInjectionMarkers:
    """Tests for get_injection_markers utility."""

    def test_extract_markers(self):
        """Test extracting injection markers from class."""
        class TestService:
            email: "EmailService" = Inject()
            cache = InjectByName("CacheService")
            lazy_dep: "LazyService" = Lazy()
            normal_attr = "not a marker"

        markers = get_injection_markers(TestService)

        assert "email" in markers
        assert isinstance(markers["email"], Inject)

        assert "cache" in markers
        assert isinstance(markers["cache"], InjectByName)

        assert "lazy_dep" in markers
        assert isinstance(markers["lazy_dep"], Lazy)

        assert "normal_attr" not in markers

    def test_no_markers(self):
        """Test class with no injection markers."""
        class PlainClass:
            name = "test"
            value = 123

        markers = get_injection_markers(PlainClass)
        assert len(markers) == 0


class TestMultipleRegistrations:
    """Tests for multiple component registrations."""

    def setup_method(self):
        PendingRegistry.reset()

    def teardown_method(self):
        PendingRegistry.reset()

    def test_multiple_services(self):
        """Test registering multiple services."""
        @service()
        class UserService:
            pass

        @service()
        class EmailService:
            pass

        @service()
        class CacheService:
            pass

        registry = PendingRegistry.get_instance()
        assert registry.count == 3

        services = registry.get_by_type(ComponentType.SERVICE)
        assert len(services) == 3

    def test_mixed_components(self):
        """Test registering mixed component types."""
        @service()
        class UserService:
            pass

        @controller(url="/api")
        class ApiController:
            pass

        @component()
        class Helper:
            pass

        registry = PendingRegistry.get_instance()
        assert registry.count == 3

        assert len(registry.get_by_type(ComponentType.SERVICE)) == 1
        assert len(registry.get_by_type(ComponentType.CONTROLLER)) == 1
        assert len(registry.get_by_type(ComponentType.COMPONENT)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

