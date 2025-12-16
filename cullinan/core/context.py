# -*- coding: utf-8 -*-
"""Request context management for Cullinan framework.

Provides thread-safe context management for request-scoped data,
similar to Flask's request context or FastAPI's dependencies.
"""

import threading
from typing import Any, Dict, Optional, Callable
from contextvars import ContextVar
import logging

logger = logging.getLogger(__name__)

# Context variables for request-scoped data
_request_context: ContextVar[Optional['RequestContext']] = ContextVar('request_context', default=None)


class RequestContext:
    """Container for request-scoped data.
    
    This class holds data that is specific to a single request,
    such as user information, request metadata, and temporary state.
    
    Features can be controlled via configuration (v0.81+):
    - auto_request_id: Automatic request ID generation
    - timing: Request timing tracking
    - metadata: Metadata storage support
    - cleanup_callbacks: Cleanup callback support
    - debug_logging: Debug-level logging

    Example:
        # In a handler
        ctx = RequestContext()
        ctx.set('user_id', 123)
        ctx.set('request_id', 'abc-123')
        
        # Later in the same request
        user_id = ctx.get('user_id')
    """
    
    # Class-level feature flags (loaded from config)
    _features: Optional[Dict[str, Any]] = None

    @classmethod
    def _get_features(cls) -> Dict[str, Any]:
        """Get feature flags from configuration (cached)."""
        if cls._features is None:
            try:
                from cullinan.config import get_config
                config = get_config()
                cls._features = config.context_features.copy()
            except Exception:
                # Fallback to defaults if config not available
                cls._features = {
                    'auto_request_id': True,
                    'timing': True,
                    'metadata': True,
                    'cleanup_callbacks': True,
                    'debug_logging': False,
                    'request_id_format': 'uuid',
                    'custom_request_id_generator': None,
                }
        return cls._features

    @classmethod
    def reset_features(cls):
        """Reset feature flags cache (for testing)."""
        cls._features = None

    def __init__(self):
        """Initialize a new request context."""
        self._data: Dict[str, Any] = {}
        self._metadata: Optional[Dict[str, Any]] = None  # Lazy initialization
        self._cleanup_callbacks: Optional[list[Callable]] = None  # Lazy initialization

        # Get feature flags
        features = self._get_features()

        # Initialize optional features based on flags
        self._features_enabled = features

        # Auto-generate request ID if enabled
        if features.get('auto_request_id', True):
            self._init_request_id()

        # Initialize timing if enabled
        if features.get('timing', True):
            import time
            self._start_time = time.perf_counter()
        else:
            self._start_time = None

    def _init_request_id(self):
        """Initialize request ID based on configuration."""
        features = self._features_enabled
        request_id_format = features.get('request_id_format', 'uuid')

        if request_id_format == 'uuid':
            import uuid
            request_id = uuid.uuid4().hex[:16]
        elif request_id_format == 'sequential':
            # Sequential ID (thread-safe)
            import threading
            if not hasattr(RequestContext, '_id_counter'):
                RequestContext._id_counter = 0
                RequestContext._id_lock = threading.Lock()

            with RequestContext._id_lock:
                RequestContext._id_counter += 1
                request_id = f"req_{RequestContext._id_counter:08d}"
        elif request_id_format == 'custom':
            # Use custom generator if provided
            custom_gen = features.get('custom_request_id_generator')
            if custom_gen and callable(custom_gen):
                request_id = custom_gen()
            else:
                # Fallback to UUID
                import uuid
                request_id = uuid.uuid4().hex[:16]
        else:
            # Default to UUID
            import uuid
            request_id = uuid.uuid4().hex[:16]

        self.set('request_id', request_id)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context.
        
        Args:
            key: The key to store the value under
            value: The value to store
        """
        self._data[key] = value
        # Use lazy logging to avoid f-string evaluation when DEBUG is disabled
        # Also check feature flag
        if self._features_enabled.get('debug_logging', False) and logger.isEnabledFor(logging.DEBUG):
            logger.debug("Context set: %s", key)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context.
        
        Args:
            key: The key to retrieve
            default: Default value if key not found
        
        Returns:
            The stored value or default
        """
        return self._data.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if a key exists in the context.
        
        Args:
            key: The key to check
        
        Returns:
            True if key exists, False otherwise
        """
        return key in self._data
    
    def delete(self, key: str) -> None:
        """Remove a key from the context.
        
        Args:
            key: The key to remove
        """
        if key in self._data:
            del self._data[key]
            if self._features_enabled.get('debug_logging', False) and logger.isEnabledFor(logging.DEBUG):
                logger.debug("Context deleted: %s", key)

    def clear(self) -> None:
        """Clear all data from the context."""
        self._data.clear()
        if self._features_enabled.get('debug_logging', False) and logger.isEnabledFor(logging.DEBUG):
            logger.debug("Context cleared")

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for the context.
        
        Metadata is used for framework-level information that shouldn't
        be mixed with user data.
        
        Args:
            key: The metadata key
            value: The metadata value
        """
        # Check if metadata feature is enabled
        if not self._features_enabled.get('metadata', True):
            return

        # Lazy initialization: create dict only when first used
        if self._metadata is None:
            self._metadata = {}
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the context.
        
        Args:
            key: The metadata key
            default: Default value if key not found
        
        Returns:
            The metadata value or default
        """
        # Return default if metadata feature is disabled
        if not self._features_enabled.get('metadata', True):
            return default

        # Return default if metadata dict not yet initialized
        if self._metadata is None:
            return default
        return self._metadata.get(key, default)
    
    def register_cleanup(self, callback: Callable) -> None:
        """Register a cleanup callback to run when context is destroyed.
        
        Args:
            callback: Function to call during cleanup (no arguments)
        """
        # Check if cleanup_callbacks feature is enabled
        if not self._features_enabled.get('cleanup_callbacks', True):
            return

        # Lazy initialization: create list only when first callback is registered
        if self._cleanup_callbacks is None:
            self._cleanup_callbacks = []
        self._cleanup_callbacks.append(callback)
    
    def cleanup(self) -> None:
        """Run all registered cleanup callbacks."""
        # Skip if cleanup_callbacks feature is disabled
        if not self._features_enabled.get('cleanup_callbacks', True):
            return

        # Skip if no callbacks registered
        if self._cleanup_callbacks is None:
            return

        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error("Error in cleanup callback: %s", e)
        self._cleanup_callbacks.clear()
    
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time since context creation in seconds.

        Returns:
            Elapsed time in seconds, or None if timing feature is disabled
        """
        if not self._features_enabled.get('timing', True) or self._start_time is None:
            return None

        import time
        return time.perf_counter() - self._start_time

    def to_dict(self) -> Dict[str, Any]:
        """Get a copy of all context data.
        
        **Performance Warning**: This method creates a shallow copy of all data,
        which can be expensive if the context contains many items. For better
        performance, prefer accessing specific keys with get() instead of
        copying the entire context.

        Returns:
            Dictionary of all stored data
        """
        return self._data.copy()
    
    def __repr__(self) -> str:
        """String representation of the context."""
        metadata_count = len(self._metadata) if self._metadata is not None else 0
        return f"RequestContext(data={len(self._data)} items, metadata={metadata_count} items)"


def get_current_context() -> Optional[RequestContext]:
    """Get the current request context.
    
    Returns:
        The current RequestContext, or None if no context is active
    """
    return _request_context.get()


def set_current_context(context: Optional[RequestContext]) -> None:
    """Set the current request context.
    
    Args:
        context: The RequestContext to set as current
    """
    _request_context.set(context)


def create_context() -> RequestContext:
    """Create and activate a new request context.
    
    Returns:
        The newly created and activated RequestContext
    """
    context = RequestContext()
    set_current_context(context)
    logger.debug("Created new request context")
    return context


def destroy_context() -> None:
    """Destroy the current request context and run cleanup callbacks."""
    context = get_current_context()
    if context:
        context.cleanup()
        context.clear()
        set_current_context(None)
        logger.debug("Destroyed request context")


class ContextManager:
    """Context manager for request contexts.
    
    Usage:
        with ContextManager():
            ctx = get_current_context()
            ctx.set('key', 'value')
            # Context is automatically cleaned up on exit
    """
    
    def __enter__(self) -> RequestContext:
        """Enter the context manager."""
        return create_context()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and cleanup."""
        destroy_context()
        return False


# Convenience function for getting values with auto-context creation
def get_context_value(key: str, default: Any = None) -> Any:
    """Get a value from the current context.
    
    Convenience function that handles missing context gracefully.
    
    Args:
        key: The key to retrieve
        default: Default value if key not found or no context
    
    Returns:
        The stored value or default
    """
    context = get_current_context()
    if context is None:
        return default
    return context.get(key, default)


def set_context_value(key: str, value: Any) -> None:
    """Set a value in the current context.
    
    Convenience function that creates context if needed.
    
    Args:
        key: The key to store the value under
        value: The value to store
    """
    context = get_current_context()
    if context is None:
        context = create_context()
    context.set(key, value)
