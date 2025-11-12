# -*- coding: utf-8 -*-
"""Service registry for Cullinan framework.

Provides service registration and management using the core Registry pattern,
with support for dependency injection and lifecycle management.

Performance optimizations:
- Fast O(1) service lookup with direct dict access
- Lazy metadata initialization
- Memory-efficient with __slots__
- Singleton instance caching
"""

from typing import Type, Optional, List, Dict, Any, Set
import logging
import inspect

from cullinan.core import Registry, DependencyInjector, LifecycleManager
from cullinan.core.exceptions import RegistryError, DependencyResolutionError
from .base import Service

logger = logging.getLogger(__name__)


class ServiceRegistry(Registry[Type[Service]]):
    """Optimized registry for service classes with dependency injection support.

    This registry manages service classes and their instances with:
    - Fast O(1) service registration and lookup
    - Automatic dependency injection
    - Lifecycle management (on_init/on_destroy/on_startup/on_shutdown)
    - Singleton instance caching
    - Memory-efficient storage with __slots__

    Performance optimizations:
    - Lazy initialization of injector
    - Direct dict access for instance cache
    - Minimal metadata overhead
    - Single dependency injector from core

    Usage:
        registry = ServiceRegistry()
        registry.register('EmailService', EmailService)
        registry.register('UserService', UserService, dependencies=['EmailService'])
        
        # Initialize all services (calls on_init and on_startup)
        registry.initialize_all()
        
        # Get service instance (O(1) cached lookup)
        user_service = registry.get_instance('UserService')
        
        # Cleanup (calls on_shutdown and on_destroy)
        registry.destroy_all()
    """
    
    __slots__ = ('_injector', '_instances', '_initialized')

    def __init__(self):
        """Initialize the service registry with optimized storage."""
        super().__init__()
        # Use core's DependencyInjector for dependency resolution
        self._injector = DependencyInjector()
        # Fast instance cache (O(1) lookup)
        self._instances: Dict[str, Service] = {}
        # Track initialized services (set for O(1) membership check)
        self._initialized: Set[str] = set()

        # Register self as dependency provider for core's injection system
        # This allows InjectByName to find services
        from cullinan.core import get_injection_registry
        injection_registry = get_injection_registry()
        injection_registry.add_provider_registry(self, priority=10)
        logger.debug("ServiceRegistry registered as dependency provider")
        logger.debug("ServiceRegistry registered as dependency provider")

    def register(self, name: str, service_class: Type[Service], 
                 dependencies: Optional[List[str]] = None, **metadata) -> None:
        """Register a service class with optional dependencies (optimized).

        Performance: O(1) registration

        Args:
            name: Unique identifier for the service
            service_class: The service class (not instance)
            dependencies: List of service names this service depends on
            **metadata: Additional metadata
        
        Raises:
            RegistryError: If name already registered, invalid, or registry frozen
        """
        self._check_frozen()
        self._validate_name(name)
        
        # Fast path: check if already registered
        if name in self._items:
            logger.warning(f"Service already registered: {name}")
            return
        
        # Store the class (O(1))
        self._items[name] = service_class
        
        # Lazy metadata initialization - only create if needed
        if dependencies or metadata:
            if self._metadata is None:
                self._metadata = {}
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
        """Get the service class (not instance) by name (O(1) operation).

        Args:
            name: Service identifier
        
        Returns:
            Service class, or None if not found
        """
        return self._items.get(name)
    
    def get_instance(self, name: str) -> Optional[Service]:
        """Get or create a service instance (O(1) cached lookup).

        Performance: O(1) for cached instances, O(n) for new instances with n dependencies

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
        # Fast path: return cached instance (O(1))
        instance = self._instances.get(name)
        if instance is not None:
            return instance

        # Check if service exists
        if name not in self._items:
            logger.warning(f"Service not found: {name}")
            return None
        
        try:
            # Get dependencies (lazy metadata access)
            deps = []
            if self._metadata is not None and name in self._metadata:
                deps = self._metadata[name].get('dependencies', [])

            # Ensure all dependencies are initialized first
            for dep_name in deps:
                if dep_name not in self._instances:
                    # Recursively get dependencies
                    self.get_instance(dep_name)
            
            # Resolve dependencies and create instance
            instance = self._injector.resolve(name)
            
            # Cache instance immediately (O(1))
            self._instances[name] = instance
            
            # Call on_init lifecycle hook if exists and not yet initialized
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
        
        Creates instances and calls lifecycle hooks:
        1. on_init() - via get_instance()
        2. on_startup() - explicitly called here

        For async methods, use initialize_all_async() instead.
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
                if not instance:
                    logger.warning(f"Failed to create instance for {name}")
            except Exception as e:
                logger.error(f"Failed to create instance for {name}: {e}", exc_info=True)
                raise
        
        logger.info(f"Initialized {len(service_names)} services")

        # Call on_startup() lifecycle methods
        logger.debug("Calling on_startup() for all services...")
        for name in init_order:
            instance = self._instances.get(name)
            if instance:
                try:
                    # Check for on_startup method
                    if hasattr(instance, 'on_startup') and callable(instance.on_startup):
                        result = instance.on_startup()
                        # Check if async
                        if inspect.iscoroutine(result):
                            logger.warning(
                                f"Service {name}.on_startup() is async but called synchronously. "
                                f"Use initialize_all_async() instead or call startup separately."
                            )
                            result.close()
                        logger.debug(f"Called on_startup for service: {name}")

                    # Also check on_post_construct
                    elif hasattr(instance, 'on_post_construct') and callable(instance.on_post_construct):
                        result = instance.on_post_construct()
                        if inspect.iscoroutine(result):
                            logger.warning(f"Service {name}.on_post_construct() is async.")
                            result.close()
                        logger.debug(f"Called on_post_construct for service: {name}")
                except Exception as e:
                    logger.error(f"Error in on_startup/on_post_construct for {name}: {e}", exc_info=True)
                    # Don't raise, continue with other services

        logger.info(f"Startup complete for {len(service_names)} services")

    async def initialize_all_async(self) -> None:
        """Initialize all registered services in dependency order (async version).
        
        Creates instances and calls async lifecycle hooks:
        1. on_init() or on_init_async()
        2. on_startup() or on_startup_async()
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
        
        # Create instances and call on_init (async support)
        for name in init_order:
            try:
                if name not in self._instances:
                    # Create instance
                    instance = self._injector.resolve(name)
                    self._instances[name] = instance

                    # Call on_init (async version if available)
                    if hasattr(instance, 'on_init_async') and callable(instance.on_init_async):
                        await instance.on_init_async()
                        logger.debug(f"Called on_init_async for service: {name}")
                    elif hasattr(instance, 'on_init') and callable(instance.on_init):
                        result = instance.on_init()
                        if inspect.iscoroutine(result):
                            await result
                        logger.debug(f"Called on_init for service: {name}")

                    self._initialized.add(name)
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}", exc_info=True)
                raise
        
        logger.info(f"Initialized {len(service_names)} services")

        # Call on_startup (async support)
        logger.debug("Calling on_startup() for all services...")
        for name in init_order:
            instance = self._instances.get(name)
            if instance:
                try:
                    # Check for async on_startup
                    if hasattr(instance, 'on_startup_async') and callable(instance.on_startup_async):
                        await instance.on_startup_async()
                        logger.debug(f"Called on_startup_async for service: {name}")
                    elif hasattr(instance, 'on_startup') and callable(instance.on_startup):
                        result = instance.on_startup()
                        if inspect.iscoroutine(result):
                            await result
                        logger.debug(f"Called on_startup for service: {name}")
                    # Also check on_post_construct
                    elif hasattr(instance, 'on_post_construct_async') and callable(instance.on_post_construct_async):
                        await instance.on_post_construct_async()
                        logger.debug(f"Called on_post_construct_async for service: {name}")
                    elif hasattr(instance, 'on_post_construct') and callable(instance.on_post_construct):
                        result = instance.on_post_construct()
                        if inspect.iscoroutine(result):
                            await result
                        logger.debug(f"Called on_post_construct for service: {name}")
                except Exception as e:
                    logger.error(f"Error in on_startup for {name}: {e}", exc_info=True)
                    # Don't raise, continue with other services

        logger.info(f"Startup complete for {len(service_names)} services (async)")

    def destroy_all(self) -> None:
        """Destroy all service instances in reverse dependency order.
        
        Calls lifecycle hooks:
        1. on_shutdown() - explicitly called here
        2. on_destroy() - called for cleanup

        For async methods, use destroy_all_async() instead.
        """
        try:
            # Get shutdown order (reverse of initialization)
            if not self._instances:
                logger.debug("No services to destroy")
                return

            # Calculate reverse order
            shutdown_order = list(reversed(list(self._instances.keys())))

            # Call on_shutdown() lifecycle methods
            logger.debug("Calling on_shutdown() for all services...")
            for name in shutdown_order:
                instance = self._instances.get(name)
                if instance:
                    try:
                        # Check for on_shutdown method
                        if hasattr(instance, 'on_shutdown') and callable(instance.on_shutdown):
                            result = instance.on_shutdown()
                            if inspect.iscoroutine(result):
                                logger.warning(
                                    f"Service {name}.on_shutdown() is async but called synchronously. "
                                    f"Use destroy_all_async() instead."
                                )
                                result.close()
                            logger.debug(f"Called on_shutdown for service: {name}")

                        # Also check on_pre_destroy
                        elif hasattr(instance, 'on_pre_destroy') and callable(instance.on_pre_destroy):
                            result = instance.on_pre_destroy()
                            if inspect.iscoroutine(result):
                                logger.warning(f"Service {name}.on_pre_destroy() is async.")
                                result.close()
                            logger.debug(f"Called on_pre_destroy for service: {name}")
                    except Exception as e:
                        logger.error(f"Error in on_shutdown/on_pre_destroy for {name}: {e}", exc_info=True)
                        # Continue with other services

            # Call on_destroy() lifecycle methods
            logger.debug("Calling on_destroy() for all services...")
            for name in shutdown_order:
                instance = self._instances.get(name)
                if instance:
                    try:
                        if hasattr(instance, 'on_destroy') and callable(instance.on_destroy):
                            result = instance.on_destroy()
                            if inspect.iscoroutine(result):
                                logger.warning(
                                    f"Service {name}.on_destroy() is async but called synchronously."
                                )
                                result.close()
                            logger.debug(f"Called on_destroy for service: {name}")
                    except Exception as e:
                        logger.error(f"Error in on_destroy for {name}: {e}", exc_info=True)
                        # Continue with other services

            logger.info(f"Destroyed {len(shutdown_order)} service instances")
        except Exception as e:
            logger.error(f"Service destruction failed: {e}", exc_info=True)
    
    async def destroy_all_async(self) -> None:
        """Destroy all service instances in reverse dependency order (async version).
        
        Calls async lifecycle hooks:
        1. on_shutdown() or on_shutdown_async()
        2. on_destroy() or on_destroy_async()
        """
        try:
            # Get shutdown order (reverse of initialization)
            if not self._instances:
                logger.debug("No services to destroy")
                return

            # Calculate reverse order
            shutdown_order = list(reversed(list(self._instances.keys())))

            # Call on_shutdown() lifecycle methods (async support)
            logger.debug("Calling on_shutdown() for all services...")
            for name in shutdown_order:
                instance = self._instances.get(name)
                if instance:
                    try:
                        # Check for async on_shutdown
                        if hasattr(instance, 'on_shutdown_async') and callable(instance.on_shutdown_async):
                            await instance.on_shutdown_async()
                            logger.debug(f"Called on_shutdown_async for service: {name}")
                        elif hasattr(instance, 'on_shutdown') and callable(instance.on_shutdown):
                            result = instance.on_shutdown()
                            if inspect.iscoroutine(result):
                                await result
                            logger.debug(f"Called on_shutdown for service: {name}")
                        # Also check on_pre_destroy
                        elif hasattr(instance, 'on_pre_destroy_async') and callable(instance.on_pre_destroy_async):
                            await instance.on_pre_destroy_async()
                            logger.debug(f"Called on_pre_destroy_async for service: {name}")
                        elif hasattr(instance, 'on_pre_destroy') and callable(instance.on_pre_destroy):
                            result = instance.on_pre_destroy()
                            if inspect.iscoroutine(result):
                                await result
                            logger.debug(f"Called on_pre_destroy for service: {name}")
                    except Exception as e:
                        logger.error(f"Error in on_shutdown for {name}: {e}", exc_info=True)
                        # Continue with other services

            # Call on_destroy() lifecycle methods (async support)
            logger.debug("Calling on_destroy() for all services...")
            for name in shutdown_order:
                instance = self._instances.get(name)
                if instance:
                    try:
                        # Check for async on_destroy
                        if hasattr(instance, 'on_destroy_async') and callable(instance.on_destroy_async):
                            await instance.on_destroy_async()
                            logger.debug(f"Called on_destroy_async for service: {name}")
                        elif hasattr(instance, 'on_destroy') and callable(instance.on_destroy):
                            result = instance.on_destroy()
                            if inspect.iscoroutine(result):
                                await result
                            logger.debug(f"Called on_destroy for service: {name}")
                    except Exception as e:
                        logger.error(f"Error in on_destroy for {name}: {e}", exc_info=True)
                        # Continue with other services

            logger.info(f"Destroyed {len(shutdown_order)} service instances (async)")
        except Exception as e:
            logger.error(f"Service destruction failed: {e}", exc_info=True)
    
    def clear(self) -> None:
        """Clear all services and instances.
        
        Useful for testing or application reinitialization.
        """
        super().clear()
        self._injector.clear()
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
