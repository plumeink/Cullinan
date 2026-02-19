# -*- coding: utf-8 -*-
"""Base handler class for Cullinan framework.

Provides a base class for HTTP request handlers with unified lifecycle support.
"""

import logging

logger = logging.getLogger(__name__)


class BaseHandler(object):
    """Base class for HTTP request handlers.
    
    Handlers use Duck Typing for lifecycle - NO base class inheritance required!
    Just define the lifecycle methods you need:

    - on_post_construct(): Called after handler instance creation
    - on_startup(): Called during application startup
    - on_shutdown(): Called during application shutdown
    - on_pre_destroy(): Called before destruction
    
    All lifecycle methods are managed by ApplicationContext.
    """
    
    def __init__(self):
        """Initialize the handler."""
        pass
    
    # Unified lifecycle hooks (Duck Typing - no base class needed)
    
    def on_post_construct(self):
        """Lifecycle hook: called after dependency injection."""
        pass
    
    def on_startup(self):
        """Lifecycle hook: called during application startup."""
        pass
    
    def on_shutdown(self):
        """Lifecycle hook: called during application shutdown."""
        pass
    
    def on_pre_destroy(self):
        """Lifecycle hook: called before destruction."""
        pass
