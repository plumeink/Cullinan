# -*- coding: utf-8 -*-
"""Test registry for isolated testing.

Provides a separate registry instance for testing without affecting
the global registry.
"""

from typing import Type, Optional, List, Any
import logging

from cullinan.service import ServiceRegistry, Service

logger = logging.getLogger(__name__)


class TestRegistry(ServiceRegistry):
    """Isolated service registry for testing.
    
    Provides a clean registry that doesn't interfere with the global
    registry, making tests independent and repeatable.
    
    Usage:
        def test_user_service():
            # Create isolated registry
            registry = TestRegistry()
            
            # Register mock dependencies
            registry.register('EmailService', MockEmailService)
            
            # Register service under test
            registry.register('UserService', UserService, dependencies=['EmailService'])
            
            # Initialize and test
            registry.initialize_all()
            user_svc = registry.get_instance('UserService')
            
            # Test...
            
            # Cleanup
            registry.destroy_all()
    """
    
    def __init__(self):
        """Initialize an isolated test registry."""
        super().__init__()
        logger.debug("Created isolated test registry")
    
    def register_mock(self, name: str, mock_instance: Any, 
                     dependencies: Optional[List[str]] = None) -> None:
        """Register a mock service instance directly.
        
        This is a convenience method for registering pre-created mock instances
        without going through the normal class registration.
        
        Args:
            name: Service name
            mock_instance: Pre-created mock instance
            dependencies: List of dependency names
        """
        # Create a wrapper class that returns the instance
        class MockWrapper:
            _instance = mock_instance
            
            def __new__(cls):
                return cls._instance
        
        self.register(name, MockWrapper, dependencies=dependencies)
        logger.debug(f"Registered mock instance: {name}")
