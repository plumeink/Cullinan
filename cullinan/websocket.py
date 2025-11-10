# -*- coding: utf-8 -*-
"""
WebSocket support for Cullinan framework.

This module provides WebSocket decorator support with registry integration.
For v0.7.0+, WebSocket handlers are managed through the unified registry pattern.
"""

from typing import Callable
from cullinan.controller import url_resolver, EncapsulationHandler
from cullinan.websocket_registry import websocket_handler, get_websocket_registry
import warnings


def websocket(**kwargs) -> Callable:
    """WebSocket decorator for v0.6.x compatibility.
    
    Args:
        url: URL pattern for the WebSocket endpoint
    
    Returns:
        Decorator function
    
    Note:
        For new code, use @websocket_handler from websocket_registry instead.
        This function is maintained for backward compatibility.
    """
    url = kwargs.get('url', '')
    global url_params
    url_params = None
    if url != '':
        url, url_params = url_resolver(url)
    
    def inner(cls):
        # Register with both old and new systems for compatibility
        EncapsulationHandler.add_url_ws(url, cls)
        
        # Also register with new WebSocket registry
        registry = get_websocket_registry()
        registry.register(cls.__name__, cls, url=url)
        
        return cls
    
    return inner


# Export new decorator for convenience
__all__ = ['websocket', 'websocket_handler', 'get_websocket_registry']

