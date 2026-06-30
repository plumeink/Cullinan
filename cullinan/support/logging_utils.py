# -*- coding: utf-8 -*-
"""
Cullinan Framework Logging Utilities

Provides structured logging capabilities with context enrichment,
performance tracking, and flexible output formats.
"""

import logging
import json
import time
import functools
from typing import Any, Dict, Optional, Callable
from contextvars import ContextVar


# Context variable for request-level logging context
_logging_context: ContextVar[Dict[str, Any]] = ContextVar('logging_context', default={})


class StructuredLogger:
    """Wrapper around Python logger that adds structured logging capabilities.
    
    Features:
    - Structured JSON output for machine parsing
    - Context enrichment (request ID, user info, etc.)
    - Conditional logging to avoid unnecessary overhead
    - Performance tracking helpers
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def set_context(self, **kwargs) -> None:
        """Set logging context for the current request/task."""
        ctx = _logging_context.get().copy()
        ctx.update(kwargs)
        _logging_context.set(ctx)
    
    def clear_context(self) -> None:
        """Clear logging context."""
        _logging_context.set({})
    
    def get_context(self) -> Dict[str, Any]:
        """Get current logging context."""
        return _logging_context.get().copy()
    
    def _enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich log data with context."""
        ctx = _logging_context.get()
        if ctx:
            data['context'] = ctx
        return data
    
    def structured(
        self,
        level: int,
        message: str,
        **kwargs
    ) -> None:
        """Log structured data at specified level.
        
        Args:
            level: Logging level (logging.INFO, logging.ERROR, etc.)
            message: Log message
            **kwargs: Additional structured data to include
        """
        if not self.logger.isEnabledFor(level):
            return
        
        data = {
            'message': message,
            'timestamp': time.time(),
        }
        data.update(kwargs)
        data = self._enrich(data)
        
        # Log as JSON for structured output
        self.logger.log(level, json.dumps(data, ensure_ascii=False, default=str))
    
    def debug_structured(self, message: str, **kwargs) -> None:
        """Log structured debug message."""
        self.structured(logging.DEBUG, message, **kwargs)
    
    def info_structured(self, message: str, **kwargs) -> None:
        """Log structured info message."""
        self.structured(logging.INFO, message, **kwargs)
    
    def warning_structured(self, message: str, **kwargs) -> None:
        """Log structured warning message."""
        self.structured(logging.WARNING, message, **kwargs)
    
    def error_structured(self, message: str, **kwargs) -> None:
        """Log structured error message."""
        self.structured(logging.ERROR, message, **kwargs)
    
    def exception_structured(
        self,
        message: str,
        exc_info: Any = True,
        **kwargs
    ) -> None:
        """Log exception with structured data."""
        if not self.logger.isEnabledFor(logging.ERROR):
            return
        
        data = {
            'message': message,
            'timestamp': time.time(),
            'exception': True,
        }
        data.update(kwargs)
        data = self._enrich(data)
        
        self.logger.error(
            json.dumps(data, ensure_ascii=False, default=str),
            exc_info=exc_info
        )


class PerformanceLogger:
    """Helper for logging performance metrics."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_timing(
        self,
        operation: str,
        duration: float,
        threshold: Optional[float] = None,
        **context
    ) -> None:
        """Log operation timing, optionally only if above threshold.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            threshold: Optional threshold - only log if duration exceeds this
            **context: Additional context to include
        """
        if threshold is not None and duration < threshold:
            return
        
        if not self.logger.isEnabledFor(logging.INFO):
            return
        
        data = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'duration_s': round(duration, 3),
        }
        data.update(context)
        
        level = logging.WARNING if (threshold and duration > threshold) else logging.INFO
        self.logger.log(
            level,
            f"Performance: {operation} took {data['duration_ms']}ms",
            extra={'performance_data': data}
        )
    
    def timed(
        self,
        operation: Optional[str] = None,
        threshold: Optional[float] = None
    ) -> Callable:
        """Decorator to automatically log function execution time.
        
        Args:
            operation: Operation name (defaults to function name)
            threshold: Optional threshold - only log if duration exceeds this
        
        Example:
            @perf_logger.timed(threshold=1.0)
            def slow_operation():
                pass
        """
        def decorator(func: Callable) -> Callable:
            op_name = operation or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.time() - start
                    self.log_timing(op_name, duration, threshold)
            
            return wrapper
        return decorator


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger for the given name."""
    return StructuredLogger(logging.getLogger(name))


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger for the given name."""
    return PerformanceLogger(logging.getLogger(name))


# Conditional logging helpers
def should_log(logger: logging.Logger, level: int) -> bool:
    """Check if logging is enabled for the given level.
    
    Use this before expensive string formatting operations:
    
    Example:
        if should_log(logger, logging.DEBUG):
            logger.debug("Complex data: %s", expensive_operation())
    """
    return logger.isEnabledFor(level)


def log_if_enabled(
    logger: logging.Logger,
    level: int,
    message: str,
    *args,
    **kwargs
) -> None:
    """Log only if the level is enabled.
    
    Convenience wrapper that checks level before logging.
    """
    if logger.isEnabledFor(level):
        logger.log(level, message, *args, **kwargs)
