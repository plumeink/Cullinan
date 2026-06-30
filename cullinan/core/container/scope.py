# -*- coding: utf-8 -*-
"""兼容转发到统一 ScopeManager。"""

from ..scope_manager import RequestScope, ScopeManager, SingletonScope, PrototypeScope

__all__ = ["RequestScope", "ScopeManager", "SingletonScope", "PrototypeScope"]
