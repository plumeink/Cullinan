# -*- coding: utf-8 -*-
"""Cullinan IoC Container Module (2.0)

This module provides the core IoC/DI container components:
- ApplicationContext: Single entry point for container operations
- Definition: Immutable dependency definition
- ScopeType: Scope enumeration (SINGLETON/PROTOTYPE/REQUEST)
- ScopeManager: Unified scope management
- Factory: Unified instance creation

Author: Plumeink
"""

from .context import ApplicationContext
from .definitions import Definition, ScopeType
from .scope import ScopeManager, SingletonScope, PrototypeScope, RequestScope
from .factory import Factory

__all__ = [
    'ApplicationContext',
    'Definition',
    'ScopeType',
    'ScopeManager',
    'SingletonScope',
    'PrototypeScope',
    'RequestScope',
    'Factory',
]

