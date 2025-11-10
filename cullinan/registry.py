# -*- coding: utf-8 -*-
"""Handler and header registry for the Cullinan framework.

This module provides backward compatibility by re-exporting the new handler
registry implementation from cullinan.handler module.

DEPRECATED: This module is maintained for backward compatibility.
New code should import directly from cullinan.handler.

For new code:
    from cullinan.handler import HandlerRegistry, get_handler_registry

For backward compatibility (still works):
    from cullinan.registry import HandlerRegistry, get_handler_registry
"""

from typing import List, Any
import logging
import warnings

# Import the new implementation from handler module
from cullinan.handler import (
    HandlerRegistry as _HandlerRegistry,
    get_handler_registry as _get_handler_registry,
    reset_handler_registry as _reset_handler_registry
)

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
HandlerRegistry = _HandlerRegistry



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


# Global header registry instance
_default_header_registry = HeaderRegistry()


def get_handler_registry() -> HandlerRegistry:
    """Get the default global handler registry.
    
    Returns:
        The default HandlerRegistry instance
    """
    return _get_handler_registry()


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
    _reset_handler_registry()
    _default_header_registry.clear()
    logger.debug("Reset all registries")
