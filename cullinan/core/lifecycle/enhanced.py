# -*- coding: utf-8 -*-
"""Complete Lifecycle Management System for Cullinan Framework

This module re-exports the unified lifecycle interfaces from lifecycle_enhanced.py
in the parent directory. All lifecycle management is now centralized there.
"""

# Re-export from parent lifecycle_enhanced
from ..lifecycle_enhanced import (
    LifecyclePhase,
    LifecycleAware,
    SmartLifecycle,
    LifecycleManager,
    get_lifecycle_manager,
    reset_lifecycle_manager,
)

__all__ = [
    'LifecyclePhase',
    'LifecycleAware',
    'SmartLifecycle',
    'LifecycleManager',
    'get_lifecycle_manager',
    'reset_lifecycle_manager',
]

