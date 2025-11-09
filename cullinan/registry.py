# -*- coding: utf-8 -*-
"""Handler and header registry for the Cullinan framework.

This module provides a centralized registry for managing HTTP handlers and headers,
replacing the previous global list-based approach with a more testable and maintainable
dependency injection pattern.

Extracted from controller.py for better separation of concerns and testability.
"""

from typing import List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HandlerRegistry:
    """Registry for HTTP request handlers.
    
    Manages URL patterns and their associated handler (servlet) classes.
    Provides methods for registration, retrieval, and sorting of handlers.
    """
    
    def __init__(self):
        """Initialize an empty handler registry."""
        self._handlers: List[Tuple[str, Any]] = []
    
    def register(self, url: str, servlet: Any) -> None:
        """Register a URL pattern with its handler servlet.
        
        Args:
            url: URL pattern (may contain regex patterns like ([a-zA-Z0-9-]+))
            servlet: Handler class for this URL pattern
        """
        # Check if URL already registered
        for item in self._handlers:
            if item[0] == url:
                logger.debug(f"URL pattern already registered: {url}")
                return
        
        self._handlers.append((url, servlet))
        logger.debug(f"Registered handler for URL: {url}")
    
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
        self._handlers.clear()
        logger.debug("Cleared all registered handlers")
    
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


class HeaderRegistry:
    """Registry for global HTTP headers.
    
    Manages headers that should be applied to all HTTP responses.
    Provides methods for registration and retrieval of headers.
    """
    
    def __init__(self):
        """Initialize an empty header registry."""
        self._headers: List[Any] = []
    
    def register(self, header: Any) -> None:
        """Register a global header to be applied to all responses.
        
        Args:
            header: Header object or tuple to be added to responses
        """
        self._headers.append(header)
        logger.debug(f"Registered global header: {header}")
    
    def get_headers(self) -> List[Any]:
        """Get all registered headers.
        
        Returns:
            List of header objects/tuples
        """
        return self._headers.copy()
    
    def clear(self) -> None:
        """Clear all registered headers.
        
        Useful for testing or application reinitialization.
        """
        self._headers.clear()
        logger.debug("Cleared all registered headers")
    
    def count(self) -> int:
        """Get the number of registered headers.
        
        Returns:
            Number of registered global headers
        """
        return len(self._headers)
    
    def has_headers(self) -> bool:
        """Check if any headers are registered.
        
        Returns:
            True if headers exist, False otherwise
        """
        return len(self._headers) > 0


# Global registry instances (for backward compatibility)
# These can be replaced with dependency injection in new code
_default_handler_registry = HandlerRegistry()
_default_header_registry = HeaderRegistry()


def get_handler_registry() -> HandlerRegistry:
    """Get the default global handler registry.
    
    Returns:
        The default HandlerRegistry instance
    """
    return _default_handler_registry


def get_header_registry() -> HeaderRegistry:
    """Get the default global header registry.
    
    Returns:
        The default HeaderRegistry instance
    """
    return _default_header_registry


def reset_registries() -> None:
    """Reset all registries to empty state.
    
    Useful for testing to ensure clean state between tests.
    """
    _default_handler_registry.clear()
    _default_header_registry.clear()
    logger.debug("Reset all registries")
