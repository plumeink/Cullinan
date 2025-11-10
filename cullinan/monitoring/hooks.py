# -*- coding: utf-8 -*-
"""Monitoring hooks for Cullinan framework.

Provides interfaces for monitoring application events and collecting metrics.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
import time

logger = logging.getLogger(__name__)


class MonitoringHook(ABC):
    """Abstract base class for monitoring hooks.
    
    Monitoring hooks can observe application events such as:
    - Service initialization and destruction
    - Request handling
    - Errors and exceptions
    - Custom application events
    
    Example:
        class MetricsHook(MonitoringHook):
            def on_request_start(self, context):
                context['start_time'] = time.time()
            
            def on_request_end(self, context):
                duration = time.time() - context['start_time']
                self.metrics.record('request_duration', duration)
    """
    
    def __init__(self):
        """Initialize the monitoring hook."""
        pass
    
    def on_service_init(self, service_name: str, service: Any) -> None:
        """Called when a service is initialized.
        
        Args:
            service_name: Name of the service
            service: The service instance
        """
        pass
    
    def on_service_destroy(self, service_name: str, service: Any) -> None:
        """Called when a service is destroyed.
        
        Args:
            service_name: Name of the service
            service: The service instance
        """
        pass
    
    def on_request_start(self, context: Dict[str, Any]) -> None:
        """Called when a request starts processing.
        
        Args:
            context: Request context dictionary (can be modified)
        """
        pass
    
    def on_request_end(self, context: Dict[str, Any]) -> None:
        """Called when a request finishes processing.
        
        Args:
            context: Request context dictionary
        """
        pass
    
    def on_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Called when an error occurs.
        
        Args:
            error: The exception that occurred
            context: Optional context information
        """
        pass
    
    def on_custom_event(self, event_name: str, data: Any) -> None:
        """Called for custom application events.
        
        Args:
            event_name: Name of the event
            data: Event data
        """
        pass


class MonitoringManager:
    """Manages monitoring hooks and dispatches events.
    
    The monitoring manager maintains a collection of monitoring hooks
    and dispatches events to all registered hooks.
    
    Example:
        manager = MonitoringManager()
        manager.register(MetricsHook())
        manager.register(LoggingHook())
        
        # Events are dispatched to all hooks
        manager.on_request_start({'path': '/api/users'})
    """
    
    def __init__(self):
        """Initialize the monitoring manager."""
        self._hooks: List[MonitoringHook] = []
    
    def register(self, hook: MonitoringHook) -> None:
        """Register a monitoring hook.
        
        Args:
            hook: The monitoring hook instance
        """
        if not isinstance(hook, MonitoringHook):
            raise TypeError(f"Expected MonitoringHook instance, got {type(hook)}")
        
        self._hooks.append(hook)
        logger.debug(f"Registered monitoring hook: {hook.__class__.__name__}")
    
    def unregister(self, hook: MonitoringHook) -> bool:
        """Unregister a monitoring hook.
        
        Args:
            hook: The monitoring hook instance to remove
        
        Returns:
            True if hook was removed, False if not found
        """
        try:
            self._hooks.remove(hook)
            logger.debug(f"Unregistered monitoring hook: {hook.__class__.__name__}")
            return True
        except ValueError:
            return False
    
    def on_service_init(self, service_name: str, service: Any) -> None:
        """Dispatch service initialization event to all hooks.
        
        Args:
            service_name: Name of the service
            service: The service instance
        """
        for hook in self._hooks:
            try:
                hook.on_service_init(service_name, service)
            except Exception as e:
                logger.error(f"Error in {hook.__class__.__name__}.on_service_init: {e}", exc_info=True)
    
    def on_service_destroy(self, service_name: str, service: Any) -> None:
        """Dispatch service destruction event to all hooks.
        
        Args:
            service_name: Name of the service
            service: The service instance
        """
        for hook in self._hooks:
            try:
                hook.on_service_destroy(service_name, service)
            except Exception as e:
                logger.error(f"Error in {hook.__class__.__name__}.on_service_destroy: {e}", exc_info=True)
    
    def on_request_start(self, context: Dict[str, Any]) -> None:
        """Dispatch request start event to all hooks.
        
        Args:
            context: Request context dictionary
        """
        for hook in self._hooks:
            try:
                hook.on_request_start(context)
            except Exception as e:
                logger.error(f"Error in {hook.__class__.__name__}.on_request_start: {e}", exc_info=True)
    
    def on_request_end(self, context: Dict[str, Any]) -> None:
        """Dispatch request end event to all hooks.
        
        Args:
            context: Request context dictionary
        """
        for hook in self._hooks:
            try:
                hook.on_request_end(context)
            except Exception as e:
                logger.error(f"Error in {hook.__class__.__name__}.on_request_end: {e}", exc_info=True)
    
    def on_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Dispatch error event to all hooks.
        
        Args:
            error: The exception that occurred
            context: Optional context information
        """
        for hook in self._hooks:
            try:
                hook.on_error(error, context)
            except Exception as e:
                logger.error(f"Error in {hook.__class__.__name__}.on_error: {e}", exc_info=True)
    
    def on_custom_event(self, event_name: str, data: Any) -> None:
        """Dispatch custom event to all hooks.
        
        Args:
            event_name: Name of the event
            data: Event data
        """
        for hook in self._hooks:
            try:
                hook.on_custom_event(event_name, data)
            except Exception as e:
                logger.error(f"Error in {hook.__class__.__name__}.on_custom_event: {e}", exc_info=True)
    
    def clear(self) -> None:
        """Clear all registered hooks.
        
        Useful for testing or reinitialization.
        """
        self._hooks.clear()
        logger.debug("Cleared all monitoring hooks")
    
    def count(self) -> int:
        """Get the number of registered hooks.
        
        Returns:
            Number of monitoring hooks
        """
        return len(self._hooks)


# Global monitoring manager instance
_global_monitoring_manager = MonitoringManager()


def get_monitoring_manager() -> MonitoringManager:
    """Get the global monitoring manager instance.
    
    Returns:
        The global MonitoringManager instance
    """
    return _global_monitoring_manager


def reset_monitoring_manager() -> None:
    """Reset the global monitoring manager.
    
    Useful for testing to ensure clean state between tests.
    """
    _global_monitoring_manager.clear()
    logger.debug("Reset global monitoring manager")
