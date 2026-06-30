# -*- coding: utf-8 -*-
"""Shared user-facing diagnostic messages for Cullinan."""

from __future__ import annotations


def _qualified_name(target: object) -> str:
    module_name = getattr(target, "__module__", None)
    qualname = getattr(target, "__qualname__", None) or getattr(target, "__name__", None)
    if module_name and qualname:
        return f"{module_name}.{qualname}"
    return repr(target)


def require_application_entry(api_name: str) -> str:
    return (
        f"{api_name}() requires an @application entry method. "
        "Decorate a zero-body entry method with @application and optionally "
        "@configure(...), then call that method directly."
    )


def require_root_module(api_name: str) -> str:
    return (
        f"{api_name}() requires a root module. "
        "Pass one explicitly, or configure it first with "
        "configure(root_module=YourRootModule)."
    )


def application_not_installed() -> str:
    return "The application has not been installed yet."


def invalid_application_entry(api_name: str, entry: object) -> str:
    return (
        f"{api_name}() expected a Cullinan @application entry method, but received "
        f"{_qualified_name(entry)}. Decorate the entry method with @application."
    )


def legacy_root_module_entry_removed() -> str:
    return (
        "configure(root_module=...) is no longer part of the default Cullinan startup model. "
        "Declare an entry method with @application and attach startup settings with "
        "@configure(...)."
    )


def legacy_public_entry_removed(api_name: str, entry: object) -> str:
    return (
        f"{api_name}() no longer accepts startup classes or root modules such as "
        f"{_qualified_name(entry)}. Declare an @application entry method and call it "
        "directly, or use Application.run(...) only when you intentionally need the "
        "advanced runtime model."
    )


def application_decorator_requires_function(target: object) -> str:
    return (
        "@application now decorates an entry method, not a startup class such as "
        f"{_qualified_name(target)}. Declare a zero-body function and decorate it with "
        "@application instead."
    )


def application_entry_method_takes_no_arguments(entry: object) -> str:
    return (
        f"{_qualified_name(entry)}() is a Cullinan entry method and should be called "
        "without arguments. Call the method directly for default startup, or use "
        "entry.run(...) / entry.get_asgi_app(...) for explicit runtime control."
    )


def duplicate_definition(name: str) -> str:
    return f"Definition '{name}' is already registered. Duplicate registration is not allowed."


def missing_inner_type(container_name: str) -> str:
    return f"{container_name} requires an inner type."


def optional_single_dependency_only() -> str:
    return "Optional[...] only supports wrapping a single dependency."


def union_single_candidates_only() -> str:
    return "Union[...] only supports multiple single-dependency candidates."


def provider_requires_single_type_argument() -> str:
    return "Provider[T] requires exactly one type argument."


def provider_single_dependency_only() -> str:
    return "Provider[T] only supports a single dependency."


def tuple_injection_form() -> str:
    return "Tuple injection only supports tuple[T, ...]."


def collection_requires_one_element_type() -> str:
    return "Collection injection requires exactly one element type."


def collection_single_dependency_only() -> str:
    return "Collection injection only supports single-dependency element types."


def unsupported_annotation_type(annotation_repr: str) -> str:
    return f"Unsupported annotation type: {annotation_repr}"


def invalid_annotation_expression(annotation_text: str) -> str:
    return f"Could not parse annotation expression '{annotation_text}'"


def unsupported_annotation_expression(annotation_repr: str) -> str:
    return f"Unsupported annotation expression: {annotation_repr}"


def unsupported_annotation_container(annotation_repr: str) -> str:
    return f"Unsupported annotation container: {annotation_repr}"


def container_requires_one_element_type(container_name: str) -> str:
    return f"{container_name}[T] requires exactly one element type."


def unknown_scope_type(scope_type: object) -> str:
    return f"Unknown scope type: {scope_type}"
