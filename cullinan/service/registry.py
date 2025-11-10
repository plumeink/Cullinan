# -*- coding: utf-8 -*-
"""Service registry for Cullinan framework.

Provides service registration and management using the core Registry pattern,
with support for dependency injection and lifecycle management.
"""

from typing import Type, Optional, List, Dict, Any
import logging
import inspect

from cullinan.core import Registry, DependencyInjector, LifecycleManager
from cullinan.core.exceptions import RegistryError, DependencyResolutionError
from .base import Service

logger = logging.getLogger(__name__)


class ServiceRegistry(Registry[Type[Service]]):
    """Registry for service classes with dependency injection support.
    
    This registry manages service classes and their instances, handling:
    - Service registration with optional dependencies
    - Dependency injection
    - Lifecycle management (on_init/on_destroy)
    - Singleton instance caching
    
    Usage:
        registry = ServiceRegistry()
        registry.register('EmailService', EmailService)
        registry.register('UserService', UserService, dependencies=['EmailService'])
        
        # Initialize all services
        registry.initialize_all()
        
        # Get service instance
        user_service = registry.get_instance('UserService')
        
        # Cleanup
        registry.destroy_all()
    """
    
    def __init__(self):
        """Initialize the service registry."""
        super().__init__()
        self._injector = DependencyInjector()
        self._lifecycle = LifecycleManager()
        self._instances: Dict[str, Service] = {}
        self._initialized: set = set()  # Track which services have had on_init called
    
    def register(self, name: str, service_class: Type[Service], 
                 dependencies: Optional[List[str]] = None, **metadata) -> None:
        """Register a service class with optional dependencies.
        
        Args:
            name: Unique identifier for the service
            service_class: The service class (not instance)
            dependencies: List of service names this service depends on
            **metadata: Additional metadata
        
        Raises:
            RegistryError: If name already registered or invalid
        """
        self._validate_name(name)
        
        if name in self._items:
            logger.warning(f"Service already registered: {name}")
            return
        
        # Store the class
        self._items[name] = service_class
        
        # Store dependencies in metadata
        meta = metadata.copy()
        meta['dependencies'] = dependencies or []
        self._metadata[name] = meta
        
        # Register with dependency injector
        self._injector.register_provider(
            name, 
            service_class,
            dependencies=dependencies,
            singleton=True
        )
        
        logger.debug(f"Registered service: {name}")
    
    def get(self, name: str) -> Optional[Type[Service]]:
        """Get the service class (not instance) by name.
        
        Args:
            name: Service identifier
        
        Returns:
            Service class, or None if not found
        """
        return self._items.get(name)
    
    def get_instance(self, name: str) -> Optional[Service]:
        """Get or create a service instance.
        
        If the service hasn't been instantiated yet, it will be created
        with its dependencies resolved and on_init() will be called.
        
        Note: This method only supports synchronous on_init(). If your service
        has an async on_init(), use initialize_all_async() instead.
        
        Args:
            name: Service identifier
        
        Returns:
            Service instance, or None if not found
        
        Raises:
            DependencyResolutionError: If dependencies cannot be resolved
        """
        if name in self._instances:
            return self._instances[name]
        
        if name not in self._items:
            logger.warning(f"Service not found: {name}")
            return None
        
        try:
            # First ensure all dependencies are initialized
            deps = self._metadata.get(name, {}).get('dependencies', [])
            for dep_name in deps:
                if dep_name not in self._instances:
                    # Recursively get dependencies first
                    self.get_instance(dep_name)
            
            # Resolve dependencies and create instance
            instance = self._injector.resolve(name)
            
            # Store instance first
            self._instances[name] = instance
            
            # Call on_init lifecycle hook if it exists and hasn't been called yet
            if name not in self._initialized:
                if hasattr(instance, 'on_init') and callable(instance.on_init):
                    try:
                        result = instance.on_init()
                        # Check if on_init is async
                        if inspect.iscoroutine(result):
                            logger.warning(
                                f"Service {name}.on_init() is async but called synchronously. "
                                f"Use initialize_all_async() instead for proper async support."
                            )
                            # Clean up the coroutine to avoid warnings
                            result.close()
                        self._initialized.add(name)
                        logger.debug(f"Called on_init for service: {name}")
                    except Exception as e:
                        logger.error(f"Error in on_init for {name}: {e}", exc_info=True)
                        # Remove from instances if initialization failed
                        self._instances.pop(name, None)
                        raise
                else:
                    # Mark as initialized even if no on_init method
                    self._initialized.add(name)
            
            return instance
        except Exception as e:
            logger.error(f"Failed to instantiate service {name}: {e}", exc_info=True)
            raise
    
    def initialize_all(self) -> None:
        """Initialize all registered services in dependency order.
        
        Creates instances and calls on_init() for each service.
        For async on_init methods, use initialize_all_async() instead.
        """
        # Get all service names
        service_names = list(self._items.keys())
        
        if not service_names:
            logger.debug("No services to initialize")
            return
        
        # Get initialization order
        try:
            init_order = self._injector.get_dependency_order(service_names)
        except Exception as e:
            logger.error(f"Failed to determine initialization order: {e}")
            raise
        
        # Create instances in order (get_instance will call on_init)
        for name in init_order:
            try:
                instance = self.get_instance(name)
                if instance:
                    # Register with lifecycle manager for destroy_all support
                    deps = self._metadata.get(name, {}).get('dependencies', [])
                    self._lifecycle.register_component(name, instance, dependencies=deps)
                    # Mark as initialized since get_instance already called on_init
                    from cullinan.core.types import LifecycleState
                    self._lifecycle._states[name] = LifecycleState.INITIALIZED
                else:
                    logger.warning(f"Failed to create instance for {name}")
            except Exception as e:
                logger.error(f"Failed to create instance for {name}: {e}", exc_info=True)
                raise
        
        # Set initialization order for destroy_all
        self._lifecycle._initialization_order = init_order
        
        logger.info(f"Initialized {len(service_names)} services")
    
    async def initialize_all_async(self) -> None:
        """Initialize all registered services in dependency order (async version).
        
        Creates instances and calls on_init() for each service, properly handling async methods.
        """
        # Get all service names
        service_names = list(self._items.keys())
        
        if not service_names:
            logger.debug("No services to initialize")
            return
        
        # Get initialization order
        try:
            init_order = self._injector.get_dependency_order(service_names)
        except Exception as e:
            logger.error(f"Failed to determine initialization order: {e}")
            raise
        
        # Create instances in order and initialize them with async support
        for name in init_order:
            try:
                # Create instance without calling on_init (we'll do it via LifecycleManager)
                if name not in self._instances:
                    instance = self._injector.resolve(name)
                    self._instances[name] = instance
                else:
                    instance = self._instances[name]
                
                # Register with lifecycle manager if not already initialized
                if name not in self._initialized:
                    deps = self._metadata.get(name, {}).get('dependencies', [])
                    self._lifecycle.register_component(name, instance, dependencies=deps)
            except Exception as e:
                logger.error(f"Failed to create instance for {name}: {e}", exc_info=True)
                raise
        
        # Initialize all (handles async on_init properly)
        try:
            await self._lifecycle.initialize_all_async()
            # Mark all as initialized
            for name in init_order:
                self._initialized.add(name)
            logger.info(f"Initialized {len(service_names)} services (async)")
        except Exception as e:
            logger.error(f"Service initialization failed: {e}", exc_info=True)
            raise
    
    def destroy_all(self) -> None:
        """Destroy all service instances in reverse dependency order.
        
        Calls on_destroy() for each service instance.
        For async on_destroy methods, use destroy_all_async() instead.
        """
        try:
            self._lifecycle.destroy_all()
            logger.info("Destroyed all service instances")
        except Exception as e:
            logger.error(f"Service destruction failed: {e}", exc_info=True)
    
    async def destroy_all_async(self) -> None:
        """Destroy all service instances in reverse dependency order (async version).
        
        Calls on_destroy() for each service instance, properly handling async methods.
        """
        try:
            await self._lifecycle.destroy_all_async()
            logger.info("Destroyed all service instances (async)")
        except Exception as e:
            logger.error(f"Service destruction failed: {e}", exc_info=True)
    
    def clear(self) -> None:
        """Clear all services and instances.
        
        Useful for testing or application reinitialization.
        """
        super().clear()
        self._injector.clear()
        self._lifecycle.clear()
        self._instances.clear()
        self._initialized.clear()
        logger.debug("Cleared service registry")
    
    def list_instances(self) -> Dict[str, Service]:
        """Get all service instances that have been created.
        
        Returns:
            Dictionary mapping service names to instances
        """
        return self._instances.copy()
    
    def has_instance(self, name: str) -> bool:
        """Check if a service instance has been created.
        
        Args:
            name: Service identifier
        
        Returns:
            True if instance exists, False otherwise
        """
        return name in self._instances


# Global service registry instance (for backward compatibility)
_global_service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance.
    
    Returns:
        The global ServiceRegistry instance
    """
    return _global_service_registry


def reset_service_registry() -> None:
    """Reset the global service registry.
    
    Useful for testing to ensure clean state between tests.
    """
    _global_service_registry.clear()
    logger.debug("Reset global service registry")
