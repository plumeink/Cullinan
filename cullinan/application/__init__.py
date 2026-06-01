# -*- coding: utf-8 -*-
"""Application-level public facade for Cullinan."""

from cullinan.application.legacy import (
    ModuleReflectionResult,
    _build_transport_settings,
    _collect_global_headers,
    _finalize_runtime_setup,
    _validate_component_scan_results,
    reflect_module,
)
from cullinan.application.lifecycle import CullinanApplication, create_app
from cullinan.application.model import (
    Application,
    Module,
    ModuleGraph,
    ModuleMetadata,
    ModuleSpec,
    Runtime,
    _collect_module_specs,
    _resolve_component_owners,
    bind_runtime_request_context,
    current_app,
    get_module_metadata,
    module,
    release_runtime_request_context,
)
from cullinan.application.public import get_asgi_app, run
from cullinan.support.config import CullinanConfig, configure, get_config


def scan_controller(modules: list):
    return [reflect_module(mod, "controller") for mod in modules]


def scan_service(modules: list):
    return [reflect_module(mod, "nobody") for mod in modules]

__all__ = [
    "Application",
    "Module",
    "ModuleGraph",
    "ModuleMetadata",
    "ModuleReflectionResult",
    "ModuleSpec",
    "Runtime",
    "CullinanApplication",
    "CullinanConfig",
    "_collect_module_specs",
    "_resolve_component_owners",
    "bind_runtime_request_context",
    "configure",
    "create_app",
    "current_app",
    "get_asgi_app",
    "get_config",
    "get_module_metadata",
    "module",
    "reflect_module",
    "release_runtime_request_context",
    "run",
    "scan_controller",
    "scan_service",
    "_validate_component_scan_results",
]
