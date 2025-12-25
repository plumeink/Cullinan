# -*- coding: utf-8 -*-
"""Cullinan Legacy Module (Deprecated)

.. deprecated:: 0.90
    This module contains legacy code that will be removed in 1.0.0.
    Please migrate to the new IoC/DI system in cullinan.core.container.

This module provides backward compatibility for:
- Old injection system (Inject, InjectByName, injectable)
- Provider system
- Old registry patterns

Author: Plumeink
"""

import warnings

warnings.warn(
    "cullinan.core.legacy 模块已在 0.90 中弃用，将在 1.0.0 中移除。"
    "请迁移到 cullinan.core.container.ApplicationContext。",
    DeprecationWarning,
    stacklevel=2
)

# Re-export legacy components for compatibility
from .injection import (
    Inject,
    InjectByName,
    injectable,
    inject_constructor,
    InjectionRegistry,
    get_injection_registry,
    reset_injection_registry,
)

from .registry import Registry, SimpleRegistry

from .provider import (
    Provider,
    InstanceProvider,
    ClassProvider,
    FactoryProvider,
    ScopedProvider,
    ProviderRegistry,
)

from .provider_source import ProviderSource, SimpleProviderSource

from .scope import (
    Scope,
    SingletonScope as LegacySingletonScope,
    TransientScope,
    RequestScope as LegacyRequestScope,
    get_singleton_scope,
    get_transient_scope,
    get_request_scope,
)

from .facade import (
    IoCFacade,
    get_ioc_facade,
    reset_ioc_facade,
    resolve_dependency,
    resolve_dependency_by_name,
    has_dependency,
)

__all__ = [
    # Injection
    'Inject',
    'InjectByName',
    'injectable',
    'inject_constructor',
    'InjectionRegistry',
    'get_injection_registry',
    'reset_injection_registry',

    # Registry
    'Registry',
    'SimpleRegistry',

    # Provider
    'Provider',
    'InstanceProvider',
    'ClassProvider',
    'FactoryProvider',
    'ScopedProvider',
    'ProviderRegistry',
    'ProviderSource',
    'SimpleProviderSource',

    # Scope (Legacy)
    'Scope',
    'LegacySingletonScope',
    'TransientScope',
    'LegacyRequestScope',
    'get_singleton_scope',
    'get_transient_scope',
    'get_request_scope',

    # Facade
    'IoCFacade',
    'get_ioc_facade',
    'reset_ioc_facade',
    'resolve_dependency',
    'resolve_dependency_by_name',
    'has_dependency',
]

