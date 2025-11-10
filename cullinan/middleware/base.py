# -*- coding: utf-8 -*-
"""Base middleware classes for Cullinan framework.

Provides abstract base classes for implementing middleware that can
intercept and process HTTP requests and responses.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, List
import logging

logger = logging.getLogger(__name__)


class Middleware(ABC):
    """Abstract base class for middleware components.
    
    Middleware can intercept requests before they reach handlers and
    responses before they are sent to clients. Middleware can also
    implement lifecycle methods for initialization and cleanup.
    
    Example:
        class LoggingMiddleware(Middleware):
            def process_request(self, request):
                logger.info(f"Request: {request.method} {request.path}")
                return request
            
            def process_response(self, request, response):
                logger.info(f"Response: {response.status_code}")
                return response
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
    
    def on_init(self):
        """Lifecycle hook called after middleware is registered.
        
        Override this method to perform initialization.
        """
        pass
    
    def on_destroy(self):
        """Lifecycle hook called during application shutdown.
        
        Override this method to perform cleanup.
        """
        pass


class MiddlewareChain:
    """Manages a chain of middleware components.
    
    Middleware are executed in the order they are registered for requests,
    and in reverse order for responses.
    
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
        """Initialize all middleware in the chain."""
        for middleware in self._middleware:
            try:
                middleware.on_init()
                logger.debug(f"Initialized middleware: {middleware.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to initialize {middleware.__class__.__name__}: {e}", exc_info=True)
                raise
    
    def destroy_all(self) -> None:
        """Destroy all middleware in reverse order."""
        for middleware in reversed(self._middleware):
            try:
                middleware.on_destroy()
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
