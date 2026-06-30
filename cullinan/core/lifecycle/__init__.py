# -*- coding: utf-8 -*-
"""Cullinan lifecycle public facade.

This package is the single public lifecycle namespace:
- unified lifecycle orchestration comes from ``cullinan.core.lifecycle_enhanced``
- lifecycle event hooks live in ``cullinan.core.lifecycle.events``

The package exists to provide one stable import surface instead of parallel
module-level wrappers.
"""

# Re-export unified lifecycle from parent lifecycle_enhanced
from ..lifecycle_enhanced import (
    LifecyclePhase,
    LifecycleAware,
    SmartLifecycle,
    LifecycleManager,
    get_lifecycle_manager,
    reset_lifecycle_manager,
)

# Keep events for backward compatibility
from .events import (
    LifecycleEvent,
    LifecycleEventManager,
    LifecycleEventContext,
    LifecycleEventHook,
    get_lifecycle_event_manager,
    reset_lifecycle_event_manager,
)

__all__ = [
    # Unified lifecycle
    'LifecyclePhase',
    'LifecycleAware',
    'SmartLifecycle',
    'LifecycleManager',
    'get_lifecycle_manager',
    'reset_lifecycle_manager',
    # Events
    'LifecycleEvent',
    'LifecycleEventManager',
    'LifecycleEventContext',
    'LifecycleEventHook',
    'get_lifecycle_event_manager',
    'reset_lifecycle_event_manager',
]
