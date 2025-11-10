# -*- coding: utf-8 -*-
"""Middleware module for Cullinan framework.

Provides base classes and utilities for implementing middleware components
that can process requests and responses.
"""

from .base import Middleware, MiddlewareChain

__all__ = [
    'Middleware',
    'MiddlewareChain',
]
