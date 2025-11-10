# -*- coding: utf-8 -*-
"""Mock service base class for testing.

Provides utilities for creating mock services for testing purposes.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MockService:
    """Base class for mock services in tests.
    
    Provides call tracking and easy assertion methods for testing
    service interactions.
    
    Usage:
        class MockEmailService(MockService):
            def send_email(self, to, subject, body):
                self.record_call('send_email', to=to, subject=subject, body=body)
                return True
        
        # In test
        mock = MockEmailService()
        mock.send_email('test@example.com', 'Hello', 'World')
        
        assert mock.was_called('send_email')
        assert mock.call_count('send_email') == 1
        assert mock.get_call_args('send_email')['to'] == 'test@example.com'
    """
    
    def __init__(self):
        """Initialize the mock service."""
        self._calls: Dict[str, List[Dict[str, Any]]] = {}
        self.dependencies = {}
    
    def record_call(self, method_name: str, **kwargs) -> None:
        """Record a method call with its arguments.
        
        Args:
            method_name: Name of the method being called
            **kwargs: Arguments passed to the method
        """
        if method_name not in self._calls:
            self._calls[method_name] = []
        
        self._calls[method_name].append(kwargs)
        logger.debug(f"MockService recorded call: {method_name}({kwargs})")
    
    def was_called(self, method_name: str) -> bool:
        """Check if a method was called.
        
        Args:
            method_name: Name of the method to check
        
        Returns:
            True if method was called at least once
        """
        return method_name in self._calls and len(self._calls[method_name]) > 0
    
    def call_count(self, method_name: str) -> int:
        """Get the number of times a method was called.
        
        Args:
            method_name: Name of the method
        
        Returns:
            Number of times the method was called
        """
        return len(self._calls.get(method_name, []))
    
    def get_call_args(self, method_name: str, call_index: int = 0) -> Optional[Dict[str, Any]]:
        """Get the arguments from a specific method call.
        
        Args:
            method_name: Name of the method
            call_index: Index of the call (0 = first call, -1 = last call)
        
        Returns:
            Dictionary of arguments, or None if no such call
        """
        calls = self._calls.get(method_name, [])
        if not calls:
            return None
        
        try:
            return calls[call_index]
        except IndexError:
            return None
    
    def get_all_calls(self, method_name: str) -> List[Dict[str, Any]]:
        """Get all calls to a specific method.
        
        Args:
            method_name: Name of the method
        
        Returns:
            List of call argument dictionaries
        """
        return self._calls.get(method_name, []).copy()
    
    def reset_calls(self) -> None:
        """Clear all recorded calls."""
        self._calls.clear()
        logger.debug("MockService calls reset")
    
    def on_init(self):
        """Lifecycle hook for compatibility with Service."""
        pass
    
    def on_destroy(self):
        """Lifecycle hook for compatibility with Service."""
        pass
