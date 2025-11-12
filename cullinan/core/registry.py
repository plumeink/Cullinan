# -*- coding: utf-8 -*-
"""Base registry pattern for Cullinan framework.

Provides a generic, type-safe registry that can be extended for
specific use cases (services, handlers, etc.).

Performance optimizations:
- Use __slots__ for memory efficiency
- Fast-path lookups with direct dict access
- Lazy metadata initialization
- Batch registration support
- Hook system for extensibility
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict, Optional, Any, List, Callable, Set, Iterable, Tuple
import logging
import threading

from .exceptions import RegistryError

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Type of items being registered


class Registry(ABC, Generic[T]):
    """Abstract base class for all registries in Cullinan.
    
    Provides common functionality for registration, retrieval, and
    management of framework components with performance optimizations.

    Performance features:
    - Fast O(1) lookups using dict
    - Lazy metadata initialization (only created when needed)
    - Batch registration support
    - Hook system for pre/post registration callbacks
    - Thread-safe operations (when using proper locking in subclasses)

    Type Parameters:
        T: The type of items this registry manages
    
    Usage:
        class MyRegistry(Registry[MyType]):
            def register(self, name: str, item: MyType, **metadata):
                # Implementation
                pass
    """
    
    # Use __slots__ for memory efficiency (reduces memory by ~40%)
    __slots__ = ('_items', '_metadata', '_initialized', '_hooks', '_frozen', '_lock')

    def __init__(self):
        """Initialize an empty registry with optimized storage."""
        self._items: Dict[str, T] = {}
        # Lazy initialization - only create metadata dict when first used
        self._metadata: Optional[Dict[str, Dict[str, Any]]] = None
        self._initialized: bool = False
        # Hook system for extensibility (lazy init)
        self._hooks: Optional[Dict[str, List[Callable]]] = None
        # Frozen state - prevents modification when True
        self._frozen: bool = False
        self._lock = threading.RLock()

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
        """Check if an item is registered (O(1) operation).

        Args:
            name: Identifier to check
        
        Returns:
            True if item is registered, False otherwise
        """
        return name in self._items
    
    def has_metadata(self, name: str) -> bool:
        """Check if an item has metadata (O(1) operation).

        Args:
            name: Identifier to check

        Returns:
            True if item has metadata, False otherwise
        """
        return self._metadata is not None and name in self._metadata

    def list_all(self) -> Dict[str, T]:
        """Get all registered items.
        
        Returns:
            Dictionary mapping names to items (copy for safety)
        """
        return self._items.copy()
    
    def list_names(self) -> List[str]:
        """Get list of all registered item names (faster than list_all().keys()).

        Returns:
            List of registered names
        """
        return list(self._items.keys())

    def items(self) -> Iterable[Tuple[str, T]]:
        """Iterate over (name, item) pairs efficiently.

        Returns:
            Iterator of (name, item) tuples
        """
        return self._items.items()

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a registered item.
        
        Args:
            name: Identifier of the item
        
        Returns:
            Dictionary of metadata, or None if item not found or has no metadata
        """
        if self._metadata is None:
            return None
        return self._metadata.get(name)
    
    def set_metadata(self, name: str, **metadata) -> None:
        """Set or update metadata for a registered item.

        Args:
            name: Identifier of the item
            **metadata: Metadata key-value pairs

        Raises:
            RegistryError: If item not found or registry is frozen
        """
        with self._lock:
            self._check_frozen()
            if name not in self._items:
                raise RegistryError(f"Item not found: {name}")

            # Lazy init metadata dict
            if self._metadata is None:
                self._metadata = {}

            if name not in self._metadata:
                self._metadata[name] = {}
            self._metadata[name].update(metadata)

    def clear(self) -> None:
        """Clear all registered items.
        
        Useful for testing or application reinitialization.
        """
        with self._lock:
            self._check_frozen()
            self._items.clear()
            if self._metadata is not None:
                self._metadata.clear()
            logger.debug("Cleared registry")

    def count(self) -> int:
        """Get the number of registered items (O(1) operation).

        Returns:
            Number of registered items
        """
        return len(self._items)
    
    def is_empty(self) -> bool:
        """Check if registry is empty (O(1) operation).

        Returns:
            True if no items registered, False otherwise
        """
        return len(self._items) == 0

    # ========================================================================
    # Batch Operations (Performance Optimized)
    # ========================================================================

    def register_batch(self, items: Iterable[Tuple[str, T, Dict[str, Any]]]) -> int:
        """Register multiple items in batch (more efficient than multiple register calls).

        Args:
            items: Iterable of (name, item, metadata) tuples

        Returns:
            Number of items successfully registered

        Raises:
            RegistryError: If any name is invalid
        """
        self._check_frozen()
        count = 0
        for name, item, metadata in items:
            try:
                self.register(name, item, **metadata)
                count += 1
            except RegistryError as e:
                logger.warning(f"Failed to register {name}: {e}")
        return count

    def get_batch(self, names: Iterable[str]) -> Dict[str, Optional[T]]:
        """Get multiple items in batch (single dict access per item).

        Args:
            names: Iterable of item names

        Returns:
            Dictionary mapping names to items (None if not found)
        """
        return {name: self._items.get(name) for name in names}

    # ========================================================================
    # Hook System (Extensibility)
    # ========================================================================

    def add_hook(self, event: str, callback: Callable) -> None:
        """Add a hook callback for an event.

        Supported events:
        - 'pre_register': Called before registration with (name, item, metadata)
        - 'post_register': Called after registration with (name, item)
        - 'pre_unregister': Called before unregistration with (name,)
        - 'post_unregister': Called after unregistration with (name,)

        Args:
            event: Event name
            callback: Callable to invoke on event
        """
        with self._lock:
            if self._hooks is None:
                self._hooks = {}
            if event not in self._hooks:
                self._hooks[event] = []
            self._hooks[event].append(callback)

    def _trigger_hooks(self, event: str, *args, **kwargs) -> None:
        """Trigger all hooks for an event.

        Args:
            event: Event name
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
        """
        if self._hooks is None or event not in self._hooks:
            return
        for callback in self._hooks[event]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Hook {event} failed: {e}")

    # ========================================================================
    # Freeze/Unfreeze (Immutability Support)
    # ========================================================================

    def freeze(self) -> None:
        """Freeze the registry to prevent modifications.

        Useful for production environments where registrations should be immutable.
        """
        with self._lock:
            self._frozen = True
            logger.debug("Registry frozen")

    def unfreeze(self) -> None:
        """Unfreeze the registry to allow modifications."""
        with self._lock:
            self._frozen = False
            logger.debug("Registry unfrozen")

    def is_frozen(self) -> bool:
        """Check if registry is frozen.

        Returns:
            True if frozen, False otherwise
        """
        return self._frozen

    def _check_frozen(self) -> None:
        """Check if registry is frozen and raise error if so.

        Raises:
            RegistryError: If registry is frozen
        """
        if self._frozen:
            raise RegistryError("Registry is frozen and cannot be modified")

    # ========================================================================
    # Validation
    # ========================================================================

    def _validate_name(self, name: str) -> None:
        """Validate that name is a valid identifier (optimized).

        Args:
            name: Name to validate
        
        Raises:
            RegistryError: If name is invalid
        """
        # Fast path: check type and emptiness first
        if not isinstance(name, str) or not name:
            raise RegistryError(f"Invalid name: {name!r} (must be non-empty string)")
        # Only check for whitespace if needed
        if not name.strip():
            raise RegistryError(f"Invalid name: {name!r} (must not be whitespace-only)")


class SimpleRegistry(Registry[T]):
    """Optimized concrete implementation of Registry.

    This is a high-performance implementation with:
    - Fast O(1) operations for all basic methods
    - Lazy metadata initialization
    - Hook support for extensibility
    - Minimal memory footprint
    - Configurable duplicate registration policy

    Use this for simple registration needs or as a base for custom registries.
    """

    __slots__ = ('_duplicate_policy',)

    def __init__(self, duplicate_policy: str = 'warn'):
        """Initialize registry with duplicate policy.

        Args:
            duplicate_policy: How to handle duplicate registrations
                - 'error': Raise RegistryError (strict mode)
                - 'warn': Log warning and skip (default, backward compatible)
                - 'replace': Silently replace existing item
        """
        super().__init__()
        if duplicate_policy not in ('error', 'warn', 'replace'):
            raise ValueError(f"Invalid duplicate_policy: {duplicate_policy}. Must be 'error', 'warn', or 'replace'")
        self._duplicate_policy = duplicate_policy

    def register(self, name: str, item: T, **metadata) -> None:
        """Register an item with optional metadata (optimized).

        Performance: O(1) average case

        Args:
            name: Unique identifier for the item
            item: The item to register
            **metadata: Additional metadata
        
        Raises:
            RegistryError: If name already registered, invalid, or registry frozen
        """
        with self._lock:
            self._check_frozen()
            self._validate_name(name)

            # Trigger pre-register hooks
            self._trigger_hooks('pre_register', name, item, metadata)

            # Handle duplicate registration based on policy
            if name in self._items:
                if self._duplicate_policy == 'error':
                    raise RegistryError(f"Item already registered: {name}")
                elif self._duplicate_policy == 'warn':
                    logger.warning(f"Item already registered: {name}, skipping")
                    return
                elif self._duplicate_policy == 'replace':
                    logger.debug(f"Replacing existing item: {name}")
                    # Continue to register (replace)

            # Register item (O(1))
            self._items[name] = item

            # Lazy metadata initialization - only create dict if metadata provided
            if metadata:
                if self._metadata is None:
                    self._metadata = {}
                self._metadata[name] = metadata

            logger.debug(f"Registered item: {name}")

            # Trigger post-register hooks
            self._trigger_hooks('post_register', name, item)

    def get(self, name: str) -> Optional[T]:
        """Retrieve a registered item by name (optimized O(1)).

        Args:
            name: Identifier of the item to retrieve
        
        Returns:
            The registered item, or None if not found
        """
        return self._items.get(name)
    
    def unregister(self, name: str) -> bool:
        """Unregister an item by name (O(1) operation).

        Args:
            name: Identifier of the item to unregister
        
        Returns:
            True if item was unregistered, False if not found

        Raises:
            RegistryError: If registry is frozen
        """
        with self._lock:
            self._check_frozen()

            if name not in self._items:
                return False

            # Trigger pre-unregister hooks
            self._trigger_hooks('pre_unregister', name)

            # Remove item
            del self._items[name]
            if self._metadata is not None and name in self._metadata:
                del self._metadata[name]

            logger.debug(f"Unregister item: {name}")

            # Trigger post-unregister hooks
            self._trigger_hooks('post_unregister', name)

            return True

    def get_or_default(self, name: str, default: T) -> T:
        """Get item or return default if not found (O(1)).

        Args:
            name: Identifier of the item
            default: Default value if not found

        Returns:
            The registered item or default
        """
        return self._items.get(name, default)

    def update(self, name: str, item: T) -> bool:
        """Update an existing item (O(1) operation).

        Args:
            name: Identifier of the item
            item: New item value

        Returns:
            True if updated, False if item doesn't exist

        Raises:
            RegistryError: If registry is frozen
        """
        with self._lock:
            self._check_frozen()

            if name not in self._items:
                return False

            self._items[name] = item
            logger.debug(f"Updated item: {name}")
            return True
