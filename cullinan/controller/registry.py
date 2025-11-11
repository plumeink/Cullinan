# -*- coding: utf-8 -*-
"""Controller registry for Cullinan framework.

Provides controller registration and management using the core Registry pattern.
Controllers are classes that contain HTTP handler methods decorated with @get, @post, etc.

Performance optimizations:
- Fast O(1) controller and method lookup
- Lazy metadata and method storage initialization
- Memory-efficient with __slots__
- Batch method registration support
"""

from typing import Type, Any, Optional, Dict, List, Tuple
import logging

from cullinan.core import Registry
from cullinan.core.exceptions import RegistryError

logger = logging.getLogger(__name__)


class ControllerRegistry(Registry[Type[Any]]):
    """Optimized registry for controller classes.

    Manages controller classes and their metadata (URL prefixes, methods) with:
    - Fast O(1) controller registration and lookup
    - Efficient method registration and retrieval
    - URL prefix management
    - Memory-efficient storage with __slots__

    Performance features:
    - Direct dict access for O(1) operations
    - Lazy initialization of method storage
    - Minimal memory footprint
    - Batch method registration

    Usage:
        registry = ControllerRegistry()
        registry.register('UserController', UserController, url_prefix='/api/users')
        registry.register_method('UserController', '', 'get', handler_func)

        # Batch registration
        registry.register_methods_batch('UserController', [
            ('', 'get', list_func),
            ('', 'post', create_func),
        ])

        controllers = registry.list_all()
        methods = registry.get_methods('UserController')
    """

    __slots__ = ('_controller_methods',)

    def __init__(self):
        """Initialize an empty controller registry with optimized storage."""
        super().__init__()
        # Lazy init - only create when first method is registered
        # Maps controller_name -> [(url, method, func), ...]
        self._controller_methods: Optional[Dict[str, List[Tuple[str, str, Any]]]] = None

    def register(self, name: str, controller_class: Type[Any],
                 url_prefix: str = '', **metadata) -> None:
        """Register a controller class with optional URL prefix (O(1) operation).

        Performance: O(1) registration

        Args:
            name: Unique identifier for the controller (typically class name)
            controller_class: The controller class
            url_prefix: URL prefix for all routes in this controller
            **metadata: Additional metadata (e.g., middleware, auth requirements)

        Raises:
            RegistryError: If name already registered, invalid, or registry frozen
        """
        self._check_frozen()
        self._validate_name(name)

        # Fast path: check if already registered
        if name in self._items:
            logger.warning(f"Controller already registered: {name}")
            return

        # Register controller class (O(1))
        self._items[name] = controller_class

        # Lazy metadata initialization
        if url_prefix or metadata:
            if self._metadata is None:
                self._metadata = {}
            meta = metadata.copy()
            meta['url_prefix'] = url_prefix
            self._metadata[name] = meta
        elif self._metadata is not None or url_prefix == '':
            # Store empty prefix for consistency if metadata dict exists
            if self._metadata is None:
                self._metadata = {}
            self._metadata[name] = {'url_prefix': url_prefix}

        logger.debug(f"Registered controller: {name} with prefix: {url_prefix}")

    def register_method(self, controller_name: str, url: str,
                       http_method: str, handler_func: Any) -> None:
        """Register a method handler for a controller (O(1) operation).

        Args:
            controller_name: Name of the controller
            url: URL pattern for this method (relative to controller prefix)
            http_method: HTTP method (get, post, put, delete, etc.)
            handler_func: The handler function

        Raises:
            RegistryError: If controller not found or registry frozen
        """
        self._check_frozen()

        if controller_name not in self._items:
            raise RegistryError(f"Controller not found: {controller_name}")

        # Lazy init method storage
        if self._controller_methods is None:
            self._controller_methods = {}

        # Ensure list exists for this controller
        if controller_name not in self._controller_methods:
            self._controller_methods[controller_name] = []

        # Register method (O(1) append)
        method_info = (url, http_method, handler_func)
        self._controller_methods[controller_name].append(method_info)

        logger.debug(f"Registered method: {controller_name}.{http_method} {url}")

    def register_methods_batch(self, controller_name: str,
                               methods: List[Tuple[str, str, Any]]) -> int:
        """Register multiple methods for a controller in batch (optimized).

        More efficient than calling register_method multiple times.

        Args:
            controller_name: Name of the controller
            methods: List of (url, http_method, handler_func) tuples

        Returns:
            Number of methods successfully registered

        Raises:
            RegistryError: If controller not found or registry frozen
        """
        self._check_frozen()

        if controller_name not in self._items:
            raise RegistryError(f"Controller not found: {controller_name}")

        # Lazy init method storage
        if self._controller_methods is None:
            self._controller_methods = {}

        # Ensure list exists
        if controller_name not in self._controller_methods:
            self._controller_methods[controller_name] = []

        # Batch append (more efficient than multiple appends)
        self._controller_methods[controller_name].extend(methods)

        logger.debug(f"Registered {len(methods)} methods for controller: {controller_name}")
        return len(methods)

    def get(self, name: str) -> Optional[Type[Any]]:
        """Get a controller class by name (O(1) operation).

        Args:
            name: Controller identifier

        Returns:
            Controller class, or None if not found
        """
        return self._items.get(name)

    def get_methods(self, controller_name: str) -> List[Tuple[str, str, Any]]:
        """Get all registered methods for a controller (O(1) lookup + copy).

        Args:
            controller_name: Name of the controller

        Returns:
            List of (url, http_method, handler_func) tuples (copy for safety)
        """
        if self._controller_methods is None:
            return []
        return self._controller_methods.get(controller_name, []).copy()

    def has_methods(self, controller_name: str) -> bool:
        """Check if controller has any methods registered (O(1) operation).

        Args:
            controller_name: Name of the controller

        Returns:
            True if controller has methods, False otherwise
        """
        if self._controller_methods is None:
            return False
        return controller_name in self._controller_methods and \
               len(self._controller_methods[controller_name]) > 0

    def get_method_count(self, controller_name: str) -> int:
        """Get number of methods for a controller (O(1) operation).

        Args:
            controller_name: Name of the controller

        Returns:
            Number of registered methods
        """
        if self._controller_methods is None:
            return 0
        return len(self._controller_methods.get(controller_name, []))

    def get_url_prefix(self, controller_name: str) -> Optional[str]:
        """Get the URL prefix for a controller (O(1) operation).

        Args:
            controller_name: Name of the controller

        Returns:
            URL prefix string, or None if controller not found
        """
        if self._metadata is None:
            return None
        metadata = self._metadata.get(controller_name)
        if metadata:
            return metadata.get('url_prefix', '')
        return None

    def clear(self) -> None:
        """Clear all registered controllers and methods.

        Useful for testing or application reinitialization.
        """
        super().clear()
        if self._controller_methods is not None:
            self._controller_methods.clear()
        logger.debug("Cleared all registered controllers")

    def count(self) -> int:
        """Get the number of registered controllers (O(1) operation).

        Returns:
            Number of registered controllers
        """
        return len(self._items)

    def list_all_methods(self) -> Dict[str, List[Tuple[str, str, Any]]]:
        """Get all registered methods for all controllers.

        Returns:
            Dictionary mapping controller names to their method lists (copy)
        """
        if self._controller_methods is None:
            return {}
        return {name: methods.copy() for name, methods in self._controller_methods.items()}


# Global controller registry instance (singleton pattern)
_global_controller_registry = ControllerRegistry()


def get_controller_registry() -> ControllerRegistry:
    """Get the global controller registry instance.

    Returns:
        The global ControllerRegistry instance
    """
    return _global_controller_registry


def reset_controller_registry() -> None:
    """Reset the global controller registry.

    Useful for testing to ensure clean state between tests.
    """
    _global_controller_registry.clear()
    logger.debug("Reset global controller registry")
