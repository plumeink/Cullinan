# -*- coding: utf-8 -*-
"""Base middleware classes for Cullinan framework.

Provides abstract base classes for implementing middleware that can
intercept and process HTTP requests and responses.

Lifecycle is managed by ApplicationContext using Duck Typing.
"""

from abc import ABC
from typing import Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class Middleware(ABC):
    """Abstract base class for middleware components.
    
    Middleware can intercept requests before they reach handlers and
    responses before they are sent to clients.

    Lifecycle hooks (Duck Typing - no base class inheritance required):
    - on_post_construct(): Called after instance creation
    - on_startup(): Called during application startup
    - on_shutdown(): Called during application shutdown
    - on_pre_destroy(): Called before destruction

    Example:
        class LoggingMiddleware(Middleware):
            def process_request(self, request):
                logger.info(f"Request: {request.method} {request.path}")
                return request
            
            def process_response(self, request, response):
                logger.info(f"Response: {response.status_code}")
                return response

            def on_startup(self):
                logger.info("LoggingMiddleware started")
    """
    
    def __init__(self):
        """Initialize the middleware."""
        pass
    
    def process_request(self, request: Any) -> Any:
        """Process an incoming request before it reaches the handler.
        
        Args:
            request: The request object
        
        Returns:
            Modified request object or the original request
            
        Note:
            Return None to short-circuit and prevent further processing
        """
        return request
    
    def process_response(self, request: Any, response: Any) -> Any:
        """Process a response before it's sent to the client.
        
        Args:
            request: The original request object
            response: The response object
        
        Returns:
            Modified response object or the original response
        """
        return response
    
    # Unified lifecycle hooks (Duck Typing - managed by ApplicationContext)

    def on_post_construct(self):
        """Lifecycle hook: called after instance creation."""
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


class MiddlewareChain:
    """Manages a chain of middleware components.
    
    Middleware are executed in the order they are registered for requests,
    and in reverse order for responses.
    
    Note: Lifecycle is managed by ApplicationContext.

    Example:
        chain = MiddlewareChain()
        chain.add(AuthMiddleware())
        chain.add(LoggingMiddleware())
        
        # Process request through chain
        request = chain.process_request(request)
        
        # Process response through chain (reverse order)
        response = chain.process_response(request, response)
    """
    
    def __init__(self):
        """Initialize an empty middleware chain."""
        self._middleware: List[Middleware] = []
    
    def add(self, middleware: Middleware) -> None:
        """Add a middleware to the chain.
        
        Args:
            middleware: The middleware instance to add
        """
        if not isinstance(middleware, Middleware):
            raise TypeError(f"Expected Middleware instance, got {type(middleware)}")
        
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__class__.__name__}")
    
    def process_request(self, request: Any) -> Optional[Any]:
        """Process request through all middleware in order.
        
        Args:
            request: The request object
        
        Returns:
            Modified request, or None if processing was short-circuited
        """
        for middleware in self._middleware:
            request = middleware.process_request(request)
            if request is None:
                logger.debug(f"Request processing short-circuited by {middleware.__class__.__name__}")
                return None
        return request
    
    def process_response(self, request: Any, response: Any) -> Any:
        """Process response through all middleware in reverse order.
        
        Args:
            request: The original request object
            response: The response object
        
        Returns:
            Modified response object
        """
        # Process in reverse order
        for middleware in reversed(self._middleware):
            response = middleware.process_response(request, response)
        return response
    
    def initialize_all(self) -> None:
        """Initialize all middleware in the chain.

        Calls unified lifecycle methods:
        1. on_post_construct()
        2. on_startup()
        """
        for middleware in self._middleware:
            try:
                if hasattr(middleware, 'on_post_construct'):
                    middleware.on_post_construct()
                if hasattr(middleware, 'on_startup'):
                    middleware.on_startup()
                logger.debug(f"Initialized middleware: {middleware.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to initialize {middleware.__class__.__name__}: {e}", exc_info=True)
                raise
    
    def destroy_all(self) -> None:
        """Destroy all middleware in reverse order.

        Calls unified lifecycle methods:
        1. on_shutdown()
        2. on_pre_destroy()
        """
        for middleware in reversed(self._middleware):
            try:
                if hasattr(middleware, 'on_shutdown'):
                    middleware.on_shutdown()
                if hasattr(middleware, 'on_pre_destroy'):
                    middleware.on_pre_destroy()
                logger.debug(f"Destroyed middleware: {middleware.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error destroying {middleware.__class__.__name__}: {e}", exc_info=True)
                # Continue destroying other middleware even if one fails
    
    def clear(self) -> None:
        """Clear all middleware from the chain.
        
        Useful for testing or reinitialization.
        """
        self._middleware.clear()
        logger.debug("Cleared middleware chain")
    
    def count(self) -> int:
        """Get the number of middleware in the chain.
        
        Returns:
            Number of middleware components
        """
        return len(self._middleware)
