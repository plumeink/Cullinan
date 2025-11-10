# -*- coding: utf-8 -*-
"""Base handler class for Cullinan framework.

Provides a base class for HTTP request handlers with lifecycle support.
"""

import logging

logger = logging.getLogger(__name__)


class BaseHandler(object):
    """Base class for HTTP request handlers.
    
    This is a placeholder base class that can be extended in the future
    to provide common functionality for all handlers.
    
    Handlers can optionally implement lifecycle methods:
    - on_init(): Called after handler is registered
    - on_destroy(): Called during application shutdown
    """
    
    def __init__(self):
        """Initialize the handler."""
        pass
    
    def on_init(self):
        """Lifecycle hook called after handler is registered.
        
        Override this method to perform initialization.
        """
        pass
    
    def on_destroy(self):
        """Lifecycle hook called during application shutdown.
        
        Override this method to perform cleanup.
        """
        pass
