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
    
    Example:
        # In a handler
        ctx = RequestContext()
        ctx.set('user_id', 123)
        ctx.set('request_id', 'abc-123')
        
        # Later in the same request
        user_id = ctx.get('user_id')
    """
    
    def __init__(self):
        """Initialize a new request context."""
        self._data: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._cleanup_callbacks: list[Callable] = []
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the context.
        
        Args:
            key: The key to store the value under
            value: The value to store
        """
        self._data[key] = value
        logger.debug(f"Context set: {key}")
    
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
            logger.debug(f"Context deleted: {key}")
    
    def clear(self) -> None:
        """Clear all data from the context."""
        self._data.clear()
        logger.debug("Context cleared")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for the context.
        
        Metadata is used for framework-level information that shouldn't
        be mixed with user data.
        
        Args:
            key: The metadata key
            value: The metadata value
        """
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the context.
        
        Args:
            key: The metadata key
            default: Default value if key not found
        
        Returns:
            The metadata value or default
        """
        return self._metadata.get(key, default)
    
    def register_cleanup(self, callback: Callable) -> None:
        """Register a cleanup callback to run when context is destroyed.
        
        Args:
            callback: Function to call during cleanup (no arguments)
        """
        self._cleanup_callbacks.append(callback)
    
    def cleanup(self) -> None:
        """Run all registered cleanup callbacks."""
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback: {e}")
        self._cleanup_callbacks.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Get a copy of all context data.
        
        Returns:
            Dictionary of all stored data
        """
        return self._data.copy()
    
    def __repr__(self) -> str:
        """String representation of the context."""
        return f"RequestContext(data={len(self._data)} items, metadata={len(self._metadata)} items)"


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
