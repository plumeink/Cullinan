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
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"


class LifecycleAware(Protocol):
    """Protocol for components that have lifecycle methods."""
    
    def on_init(self) -> None:
        """Called when component is initialized."""
        ...
    
    def on_destroy(self) -> None:
        """Called when component is being destroyed."""
        ...
