# -*- coding: utf-8 -*-
"""Lifecycle management for Cullinan framework components.

This module re-exports the unified lifecycle interfaces from lifecycle_enhanced.py.
All lifecycle management is now handled by ApplicationContext using the
LifecycleAware and SmartLifecycle interfaces.

For backward compatibility, this module provides the same exports as before,
but the implementation is now in lifecycle_enhanced.py.
"""

# Re-export unified lifecycle from lifecycle_enhanced
from .lifecycle_enhanced import (
    LifecyclePhase,
    LifecycleAware,
    SmartLifecycle,
    LifecycleManager,
    get_lifecycle_manager,
    reset_lifecycle_manager,
)

# Re-export LifecycleState for backward compatibility
from .types import LifecycleState

__all__ = [
    'LifecyclePhase',
    'LifecycleAware',
    'SmartLifecycle',
    'LifecycleManager',
    'LifecycleState',
    'get_lifecycle_manager',
    'reset_lifecycle_manager',
]
