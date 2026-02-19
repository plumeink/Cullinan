# -*- coding: utf-8 -*-
"""Cullinan Lifecycle Module

This module provides unified lifecycle management:
- LifecycleAware: Base interface for lifecycle-aware components
- SmartLifecycle: Extended interface with phase control
- LifecycleManager: Component lifecycle orchestration
- LifecyclePhase: Lifecycle phase enumeration

All lifecycle management is now centralized in ApplicationContext.

Author: Plumeink
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

