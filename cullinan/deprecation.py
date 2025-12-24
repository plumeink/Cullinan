# -*- coding: utf-8 -*-
"""Deprecation utilities for Cullinan framework.

Provides tools for marking deprecated APIs and managing backward compatibility.

Author: Plumeink
"""

import warnings
import functools
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def deprecated(version: str,
               alternative: str,
               removal_version: str = "1.0",
               category: type = DeprecationWarning):
    """Decorator to mark a function or class as deprecated.

    Args:
        version: Version in which the API was deprecated
        alternative: Description of the alternative API to use
        removal_version: Version in which the API will be removed (default: "1.0")
        category: Warning category (default: DeprecationWarning)

    Example:
        >>> @deprecated(
        ...     version="0.8",
        ...     alternative="resolve_dependency()",
        ...     removal_version="1.0"
        ... )
        ... def get_service_by_name(name: str):
        ...     return registry.get_instance(name)
    """
    def decorator(obj):
        # Handle both functions and classes
        if isinstance(obj, type):
            # For classes
            original_init = obj.__init__

            @functools.wraps(original_init)
            def new_init(self, *args, **kwargs):
                warnings.warn(
                    f"{obj.__name__} is deprecated since v{version} and will be removed in v{removal_version}. "
                    f"Use {alternative} instead.",
                    category=category,
                    stacklevel=2
                )
                original_init(self, *args, **kwargs)

            obj.__init__ = new_init

            # Add deprecation marker
            obj.__deprecated__ = True
            obj.__deprecated_info__ = {
                'version': version,
                'alternative': alternative,
                'removal_version': removal_version,
            }

            return obj
        else:
            # For functions
            @functools.wraps(obj)
            def wrapper(*args, **kwargs):
                warnings.warn(
                    f"{obj.__name__}() is deprecated since v{version} and will be removed in v{removal_version}. "
                    f"Use {alternative} instead.",
                    category=category,
                    stacklevel=2
                )
                return obj(*args, **kwargs)

            # Add deprecation marker
            wrapper.__deprecated__ = True
            wrapper.__deprecated_info__ = {
                'version': version,
                'alternative': alternative,
                'removal_version': removal_version,
            }

            return wrapper

    return decorator


def is_deprecated(obj) -> bool:
    """Check if an object is marked as deprecated.

    Args:
        obj: The object to check

    Returns:
        True if the object is deprecated
    """
    return getattr(obj, '__deprecated__', False)


def get_deprecation_info(obj) -> Optional[dict]:
    """Get deprecation information for an object.

    Args:
        obj: The object to check

    Returns:
        Dictionary with deprecation info, or None if not deprecated
    """
    if is_deprecated(obj):
        return getattr(obj, '__deprecated_info__', None)
    return None


class DeprecationManager:
    """Manages deprecation warnings and backward compatibility.

    Can be configured to control deprecation warning behavior.
    """

    def __init__(self):
        """Initialize the deprecation manager."""
        self._enabled = True
        self._strict_mode = False  # If True, raise errors instead of warnings
        self._logged_warnings = set()  # Track which warnings have been shown

    def enable(self):
        """Enable deprecation warnings."""
        self._enabled = True
        logger.info("Deprecation warnings enabled")

    def disable(self):
        """Disable deprecation warnings."""
        self._enabled = False
        logger.info("Deprecation warnings disabled")

    def is_enabled(self) -> bool:
        """Check if deprecation warnings are enabled."""
        return self._enabled

    def set_strict_mode(self, strict: bool = True):
        """Set strict mode.

        In strict mode, deprecated API usage raises errors instead of warnings.

        Args:
            strict: Whether to enable strict mode
        """
        self._strict_mode = strict
        logger.info(f"Strict mode {'enabled' if strict else 'disabled'}")

    def is_strict(self) -> bool:
        """Check if strict mode is enabled."""
        return self._strict_mode

    def warn_once(self, key: str, message: str, category: type = DeprecationWarning):
        """Issue a deprecation warning only once per key.

        Useful for avoiding spam when a deprecated API is called in a loop.

        Args:
            key: Unique key for this warning
            message: Warning message
            category: Warning category
        """
        if not self._enabled:
            return

        if key in self._logged_warnings:
            return

        if self._strict_mode:
            raise DeprecationError(message)

        warnings.warn(message, category=category, stacklevel=3)
        self._logged_warnings.add(key)
        logger.warning(f"Deprecation warning: {message}")

    def clear_logged_warnings(self):
        """Clear the set of logged warnings."""
        self._logged_warnings.clear()


class DeprecationError(Exception):
    """Raised when deprecated API is used in strict mode."""
    pass


# Global deprecation manager
_deprecation_manager: Optional[DeprecationManager] = None


def get_deprecation_manager() -> DeprecationManager:
    """Get the global deprecation manager.

    Returns:
        The global DeprecationManager instance
    """
    global _deprecation_manager
    if _deprecation_manager is None:
        _deprecation_manager = DeprecationManager()
    return _deprecation_manager


def reset_deprecation_manager():
    """Reset the global deprecation manager (for testing)."""
    global _deprecation_manager
    _deprecation_manager = None


# Convenience functions

def warn_deprecated(message: str, category: type = DeprecationWarning):
    """Issue a deprecation warning.

    Args:
        message: Warning message
        category: Warning category
    """
    manager = get_deprecation_manager()
    if manager.is_enabled():
        if manager.is_strict():
            raise DeprecationError(message)
        warnings.warn(message, category=category, stacklevel=2)


def check_backward_compat_enabled() -> bool:
    """Check if backward compatibility mode is enabled.

    Returns:
        True if backward compatibility is enabled
    """
    try:
        from cullinan.config import get_config
        config = get_config()
        return getattr(config, 'enable_backward_compat', True)
    except Exception:
        return True  # Default to enabled

