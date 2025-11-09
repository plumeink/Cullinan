# -*- coding: utf-8 -*-
"""
Cullinan Framework Exception Hierarchy

Provides a comprehensive exception system with error codes, structured messages,
and detailed context information for better debugging and monitoring.
"""

from typing import Optional, Dict, Any
import traceback


class CullinanError(Exception):
    """Base exception class for all Cullinan framework errors.
    
    Attributes:
        error_code: Unique error code for categorization and monitoring
        message: Human-readable error message
        details: Additional context information about the error
        original_exception: The original exception if this wraps another error
    """
    
    error_code = "CULLINAN_ERROR"
    
    def __init__(
        self, 
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.error_code
        self.details = details or {}
        self.original_exception = original_exception
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format a structured error message with code and details."""
        parts = [f"[{self.error_code}] {self.message}"]
        
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"Details: {details_str}")
        
        if self.original_exception:
            parts.append(f"Caused by: {type(self.original_exception).__name__}: {self.original_exception}")
        
        return " | ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to a dictionary for structured logging."""
        result = {
            "error_code": self.error_code,
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }
        
        if self.original_exception:
            result["caused_by"] = {
                "type": type(self.original_exception).__name__,
                "message": str(self.original_exception),
            }
        
        return result


class ConfigurationError(CullinanError):
    """Configuration-related errors."""
    error_code = "CONFIG_ERROR"


class PackageDiscoveryError(CullinanError):
    """Module and package discovery errors."""
    error_code = "PACKAGE_DISCOVERY_ERROR"


class CallerPackageException(PackageDiscoveryError):
    """Failed to determine the caller's package directory.
    
    This exception maintains backward compatibility while inheriting
    from the new exception hierarchy.
    """
    error_code = "CALLER_PACKAGE_ERROR"
    
    def __init__(self, message="Failed to get the caller package directory", **kwargs):
        super().__init__(message=message, **kwargs)


class RoutingError(CullinanError):
    """URL routing and handler registration errors."""
    error_code = "ROUTING_ERROR"


class RequestError(CullinanError):
    """HTTP request processing errors."""
    error_code = "REQUEST_ERROR"


class MissingHeaderException(RequestError):
    """Required HTTP header is missing.
    
    This exception maintains backward compatibility while inheriting
    from the new exception hierarchy.
    """
    error_code = "MISSING_HEADER"
    
    def __init__(self, header_name: str, message: str = "Missing required header", **kwargs):
        self.header_name = header_name
        details = kwargs.get("details", {})
        details["header_name"] = header_name
        kwargs["details"] = details
        super().__init__(message=f"{message}: {header_name}", **kwargs)


class ParameterError(RequestError):
    """Parameter validation and processing errors."""
    error_code = "PARAMETER_ERROR"


class ResponseError(CullinanError):
    """Response building and formatting errors."""
    error_code = "RESPONSE_ERROR"


class HandlerError(CullinanError):
    """Request handler execution errors."""
    error_code = "HANDLER_ERROR"


class ServiceError(CullinanError):
    """Service layer errors."""
    error_code = "SERVICE_ERROR"