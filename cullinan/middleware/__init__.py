# -*- coding: utf-8 -*-
"""Middleware module for Cullinan framework.

Provides base classes and utilities for implementing middleware components
that can process requests and responses.
"""

from .base import Middleware, MiddlewareChain
from .registry import (
    MiddlewareRegistry,
    get_middleware_registry,
    reset_middleware_registry,
    middleware,
)

# ============================================================================
# BACKWARD_COMPAT: v0.8 - Legacy middleware registration API
# 替代方案：使用 @middleware 装饰器
# 计划移除版本：v1.0
# ============================================================================
from .legacy import (
    register_middleware_manual,
    get_registered_middlewares,
)
# ============================================================================
# END BACKWARD_COMPAT
# ============================================================================

__all__ = [
    'Middleware',
    'MiddlewareChain',
    'MiddlewareRegistry',
    'get_middleware_registry',
    'reset_middleware_registry',
    'middleware',
    # Deprecated (BACKWARD_COMPAT: v0.8)
    'register_middleware_manual',
    'get_registered_middlewares',
]
