# -*- coding: utf-8 -*-
"""Handler registry for Cullinan framework.

Provides handler registration and management using the core Registry pattern.
This module maintains backward compatibility with the existing registry API
while using the new core architecture.
"""

from typing import List, Tuple, Any, Optional
import logging

from cullinan.core import Registry
from cullinan.core.exceptions import RegistryError

logger = logging.getLogger(__name__)


class HandlerRegistry(Registry[Tuple[str, Any]]):
    """Registry for HTTP request handlers.
    
    Manages URL patterns and their associated handler (servlet) classes.
    Provides methods for registration, retrieval, and sorting of handlers.
    
    This implementation uses the core.Registry pattern while maintaining
    backward compatibility with the existing handler registration API.
    
    Usage:
        registry = HandlerRegistry()
        registry.register('/api/users', UserHandler)
        registry.register('/api/posts/([a-zA-Z0-9-]+)', PostHandler)
        
        handlers = registry.get_handlers()
        registry.sort()  # Sort by priority (static before dynamic)
    """
    
    def __init__(self):
        """Initialize an empty handler registry."""
        super().__init__()
        self._handlers: List[Tuple[str, Any]] = []
        self._initialized_handlers: set = set()  # Track initialized handlers
    
    def register(self, url: str, servlet: Any, **metadata) -> None:
        """Register a URL pattern with its handler servlet.
        
        Args:
            url: URL pattern (may contain regex patterns like ([a-zA-Z0-9-]+))
            servlet: Handler class for this URL pattern
            **metadata: Additional metadata (currently unused)
        
        Raises:
            RegistryError: If URL is invalid
        """
        # Validate URL
        if not url or not isinstance(url, str):
            raise RegistryError(f"Invalid URL pattern: {url!r}")
        
        # Check if URL already registered (backward compatible behavior)
        for item in self._handlers:
            if item[0] == url:
                logger.debug(f"URL pattern already registered: {url}")
                return
        
        # Store as tuple in both internal list and base registry
        handler_tuple = (url, servlet)
        self._handlers.append(handler_tuple)
        self._items[url] = handler_tuple
        
        if metadata:
            self._metadata[url] = metadata
        
        # Call on_init lifecycle hook if handler has it
        if hasattr(servlet, 'on_init') and callable(servlet.on_init):
            try:
                # Check if it's a class method or instance method
                # For classes, we need to instantiate or call as unbound
                if isinstance(servlet, type):
                    # It's a class, create temporary instance to call on_init
                    # Note: This may not be ideal for all cases
                    # Better to call on_init after handler instantiation by the framework
                    logger.debug(f"Handler {url} has on_init but is a class - will be called on instantiation")
                else:
                    # It's an instance
                    servlet.on_init()
                    self._initialized_handlers.add(url)
                    logger.debug(f"Called on_init for handler: {url}")
            except Exception as e:
                logger.error(f"Error in on_init for handler {url}: {e}", exc_info=True)
        
        logger.debug(f"Registered handler for URL: {url}")
    
    def get(self, url: str) -> Optional[Tuple[str, Any]]:
        """Get a handler by URL pattern.
        
        Args:
            url: URL pattern to look up
        
        Returns:
            Tuple of (url, servlet) if found, None otherwise
        """
        return self._items.get(url)
    
    def get_handlers(self) -> List[Tuple[str, Any]]:
        """Get all registered handlers.
        
        Returns:
            List of (url_pattern, servlet) tuples
        """
        return self._handlers.copy()
    
    def clear(self) -> None:
        """Clear all registered handlers.
        
        Useful for testing or application reinitialization.
        """
        super().clear()
        self._handlers.clear()
        self._initialized_handlers.clear()
        logger.debug("Cleared all registered handlers")
    
    def destroy_all(self) -> None:
        """Destroy all handlers by calling their on_destroy() lifecycle hooks.
        
        This should be called during application shutdown.
        """
        for url, servlet in reversed(self._handlers):
            if hasattr(servlet, 'on_destroy') and callable(servlet.on_destroy):
                try:
                    if isinstance(servlet, type):
                        # It's a class, skip (on_destroy should be called on instances)
                        logger.debug(f"Handler {url} is a class - on_destroy should be called on instances")
                    else:
                        # It's an instance
                        servlet.on_destroy()
                        logger.debug(f"Called on_destroy for handler: {url}")
                except Exception as e:
                    logger.error(f"Error in on_destroy for handler {url}: {e}", exc_info=True)
        
        logger.info(f"Destroyed {len(self._handlers)} handlers")
    
    def count(self) -> int:
        """Get the number of registered handlers.
        
        Returns:
            Number of registered URL patterns
        """
        return len(self._handlers)
    
    def sort(self) -> None:
        """Sort handlers with O(n log n) complexity.
        
        Handlers with dynamic segments (e.g., ([a-zA-Z0-9-]+)) are prioritized
        lower than static segments to ensure more specific routes match first.
        """
        if len(self._handlers) == 0:
            return
        
        def get_sort_key(handler: Tuple[str, Any]) -> Tuple[int, List[Tuple[int, str]]]:
            """Generate a sort key for a handler based on its URL pattern.
            
            Returns a tuple that ensures:
            - Static segments come before dynamic segments
            - Longer paths come before shorter paths
            - Lexicographic order within same priority level
            """
            url = handler[0]
            parts = url.split('/')
            
            # Build priority tuple: (priority_value, part_content)
            # priority_value: 0 for static, 1 for dynamic
            priority = []
            for part in parts:
                if part == '([a-zA-Z0-9-]+)':
                    # Dynamic segment - lower priority (sorts later)
                    priority.append((1, part))
                else:
                    # Static segment - higher priority (sorts earlier)
                    priority.append((0, part))
            
            # Return tuple for sorting: negative length ensures longer paths first,
            # then priority tuple for segment-by-segment comparison
            return (-len(parts), priority)
        
        self._handlers.sort(key=get_sort_key)
        logger.debug(f"Sorted {len(self._handlers)} handlers")


# Global handler registry instance
_global_handler_registry = HandlerRegistry()


def get_handler_registry() -> HandlerRegistry:
    """Get the global handler registry instance.
    
    Returns:
        The global HandlerRegistry instance
    """
    return _global_handler_registry


def reset_handler_registry() -> None:
    """Reset the global handler registry.
    
    Useful for testing to ensure clean state between tests.
    """
    _global_handler_registry.clear()
    logger.debug("Reset global handler registry")
