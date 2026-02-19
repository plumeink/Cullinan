# -*- coding: utf-8 -*-
"""Type definitions for the Cullinan core module.

This module provides type hints and protocols used throughout
the core module for better type safety and IDE support.
"""

from typing import Protocol, Any, Dict, List, Optional
from enum import Enum


class LifecycleState(Enum):
    """Lifecycle states for managed components."""
    CREATED = "created"
    POST_CONSTRUCT = "post_construct"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    PRE_DESTROY = "pre_destroy"
    DESTROYED = "destroyed"


class LifecycleAware(Protocol):
    """Protocol for components that have unified lifecycle methods.

    Components use Duck Typing - no base class inheritance required.
    Just implement the methods you need.
    """

    def on_post_construct(self) -> None:
        """Called after dependency injection."""
        ...
    
    def on_startup(self) -> None:
        """Called during application startup."""
        ...

    def on_shutdown(self) -> None:
        """Called during application shutdown."""
        ...

    def on_pre_destroy(self) -> None:
        """Called before destruction."""
        ...
