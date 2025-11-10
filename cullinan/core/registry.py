# -*- coding: utf-8 -*-
"""Base registry pattern for Cullinan framework.

Provides a generic, type-safe registry that can be extended for
specific use cases (services, handlers, etc.).
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, Optional, Any, List
import logging

from .exceptions import RegistryError

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Type of items being registered


class Registry(ABC, Generic[T]):
    """Abstract base class for all registries in Cullinan.
    
    Provides common functionality for registration, retrieval, and
    management of framework components.
    
    Type Parameters:
        T: The type of items this registry manages
    
    Usage:
        class MyRegistry(Registry[MyType]):
            def register(self, name: str, item: MyType, **metadata):
                # Implementation
                pass
    """
    
    def __init__(self):
        """Initialize an empty registry."""
        self._items: Dict[str, T] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._initialized: bool = False
    
    @abstractmethod
    def register(self, name: str, item: T, **metadata) -> None:
        """Register an item with optional metadata.
        
        Args:
            name: Unique identifier for the item
            item: The item to register
            **metadata: Additional metadata (implementation-specific)
        
        Raises:
            RegistryError: If name already registered
        """
        pass
    
    @abstractmethod
    def get(self, name: str) -> Optional[T]:
        """Retrieve a registered item by name.
        
        Args:
            name: Identifier of the item to retrieve
        
        Returns:
            The registered item, or None if not found
        """
        pass
    
    def has(self, name: str) -> bool:
        """Check if an item is registered.
        
        Args:
            name: Identifier to check
        
        Returns:
            True if item is registered, False otherwise
        """
        return name in self._items
    
    def list_all(self) -> Dict[str, T]:
        """Get all registered items.
        
        Returns:
            Dictionary mapping names to items (copy)
        """
        return self._items.copy()
    
    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a registered item.
        
        Args:
            name: Identifier of the item
        
        Returns:
            Dictionary of metadata, or None if item not found
        """
        return self._metadata.get(name)
    
    def clear(self) -> None:
        """Clear all registered items.
        
        Useful for testing or application reinitialization.
        """
        self._items.clear()
        self._metadata.clear()
        logger.debug("Cleared registry")
    
    def count(self) -> int:
        """Get the number of registered items.
        
        Returns:
            Number of registered items
        """
        return len(self._items)
    
    def _validate_name(self, name: str) -> None:
        """Validate that name is a valid identifier.
        
        Args:
            name: Name to validate
        
        Raises:
            RegistryError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise RegistryError(f"Invalid name: {name!r} (must be non-empty string)")
        if not name.strip():
            raise RegistryError(f"Invalid name: {name!r} (must not be whitespace-only)")


class SimpleRegistry(Registry[T]):
    """Simple concrete implementation of Registry.
    
    This is a basic implementation that stores items without any
    special behavior. Subclass this for simple registration needs.
    """
    
    def register(self, name: str, item: T, **metadata) -> None:
        """Register an item with optional metadata.
        
        Args:
            name: Unique identifier for the item
            item: The item to register
            **metadata: Additional metadata
        
        Raises:
            RegistryError: If name already registered or invalid
        """
        self._validate_name(name)
        
        if name in self._items:
            logger.warning(f"Item already registered: {name}")
            return
        
        self._items[name] = item
        if metadata:
            self._metadata[name] = metadata
        
        logger.debug(f"Registered item: {name}")
    
    def get(self, name: str) -> Optional[T]:
        """Retrieve a registered item by name.
        
        Args:
            name: Identifier of the item to retrieve
        
        Returns:
            The registered item, or None if not found
        """
        return self._items.get(name)
    
    def unregister(self, name: str) -> bool:
        """Unregister an item by name.
        
        Args:
            name: Identifier of the item to unregister
        
        Returns:
            True if item was unregistered, False if not found
        """
        if name in self._items:
            del self._items[name]
            if name in self._metadata:
                del self._metadata[name]
            logger.debug(f"Unregistered item: {name}")
            return True
        return False
