# -*- coding: utf-8 -*-
"""Factory extension layer for Cullinan IoC/DI 2.0."""

from typing import Any, Optional, Callable, List, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .application_context import ApplicationContext
    from .definitions import Definition

logger = logging.getLogger(__name__)


class Factory:
    """Unified instance creation factory.

    Responsibilities:
    - condition filtering
    - circular dependency detection
    - scope-aware caching
    - calling ``definition.factory(ctx)``
    - optional post-processing for injection-related extensions
    """
    
    __slots__ = ('_context', '_injection_enabled', '_post_processors')
    
    def __init__(self, context: 'ApplicationContext'):
        """Initialize the factory.

        Args:
            context: ApplicationContext instance.
        """
        self._context = context
        self._injection_enabled = False
        self._post_processors: List[Callable[[Any, 'Definition'], Any]] = []
    
    def enable_injection(self) -> None:
        """Enable injection-related post-processing."""
        self._injection_enabled = True
    
    def add_post_processor(self, processor: Callable[[Any, 'Definition'], Any]) -> None:
        """Register a post-processor for created instances.

        Args:
            processor: Callable that receives ``(instance, definition)`` and returns the processed instance.
        """
        self._post_processors.append(processor)
    
    def resolve(self, definition: 'Definition', injection_point: Optional[str] = None) -> Any:
        """Resolve and create an instance.

        Delegates to ``ApplicationContext._resolve()`` and allows optional post-processing.
        """
        # Use the context's internal resolution path.
        instance = self._context._resolve(definition)
        
        # Apply post-processors.
        for processor in self._post_processors:
            try:
                instance = processor(instance, definition)
            except Exception as e:
                logger.warning("Post-processor execution failed: %s", e)
        
        return instance
    
    def create_raw(self, definition: 'Definition') -> Any:
        """Create a raw instance directly through the factory without scope caching."""
        return definition.factory(self._context)


__all__ = ['Factory']
