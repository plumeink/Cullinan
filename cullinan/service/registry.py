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
    - Lifecycle management (on_init/on_destroy)
    - Singleton instance caching
    - Memory-efficient storage with __slots__

    Performance optimizations:
    - Lazy initialization of injector and lifecycle manager
    - Direct dict access for instance cache
    - Minimal metadata overhead

    Usage:
        registry = ServiceRegistry()
        registry.register('EmailService', EmailService)
        registry.register('UserService', UserService, dependencies=['EmailService'])
        
        # Initialize all services
        registry.initialize_all()
        
        # Get service instance (O(1) cached lookup)
        user_service = registry.get_instance('UserService')
        
        # Cleanup
        registry.destroy_all()
    """
    
    __slots__ = ('_injector', '_lifecycle', '_instances', '_initialized')

    def __init__(self):
        """Initialize the service registry with optimized storage."""
        super().__init__()
        self._injector = DependencyInjector()
        self._lifecycle = LifecycleManager()
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
                    # Handle lazy metadata initialization
                    deps = []
                    if self._metadata is not None and name in self._metadata:
                        deps = self._metadata[name].get('dependencies', [])
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

        # 🔥 调用 on_startup() 生命周期方法
        logger.debug("Calling on_startup() for all services...")
        for name in init_order:
            instance = self._instances.get(name)
            if instance:
                try:
                    # 检查是否有 on_startup 方法
                    if hasattr(instance, 'on_startup') and callable(instance.on_startup):
                        result = instance.on_startup()
                        # 检查是否是 async 方法
                        if inspect.iscoroutine(result):
                            logger.warning(
                                f"Service {name}.on_startup() is async but called synchronously. "
                                f"Use initialize_all_async() instead or call startup_all_async() separately."
                            )
                            result.close()
                        logger.debug(f"Called on_startup for service: {name}")

                    # 也检查 on_post_construct（如果没有 on_init）
                    elif hasattr(instance, 'on_post_construct') and callable(instance.on_post_construct):
                        result = instance.on_post_construct()
                        if inspect.iscoroutine(result):
                            logger.warning(
                                f"Service {name}.on_post_construct() is async but called synchronously."
                            )
                            result.close()
                        logger.debug(f"Called on_post_construct for service: {name}")
                except Exception as e:
                    logger.error(f"Error in on_startup/on_post_construct for {name}: {e}", exc_info=True)
                    # 不 raise，继续启动其他服务

        logger.info(f"Startup complete for {len(service_names)} services")

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
                    # Handle lazy metadata initialization
                    deps = []
                    if self._metadata is not None and name in self._metadata:
                        deps = self._metadata[name].get('dependencies', [])
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
        
        Calls on_shutdown() and on_destroy() for each service instance.
        For async methods, use destroy_all_async() instead.
        """
        try:
            # 🔥 首先调用 on_shutdown() 生命周期方法（按逆序）
            if hasattr(self._lifecycle, '_initialization_order'):
                shutdown_order = list(reversed(self._lifecycle._initialization_order))
                logger.debug("Calling on_shutdown() for all services...")

                for name in shutdown_order:
                    instance = self._instances.get(name)
                    if instance:
                        try:
                            # 检查是否有 on_shutdown 方法
                            if hasattr(instance, 'on_shutdown') and callable(instance.on_shutdown):
                                result = instance.on_shutdown()
                                # 检查是否是 async 方法
                                if inspect.iscoroutine(result):
                                    logger.warning(
                                        f"Service {name}.on_shutdown() is async but called synchronously. "
                                        f"Use destroy_all_async() instead."
                                    )
                                    result.close()
                                logger.debug(f"Called on_shutdown for service: {name}")

                            # 也检查 on_pre_destroy
                            elif hasattr(instance, 'on_pre_destroy') and callable(instance.on_pre_destroy):
                                result = instance.on_pre_destroy()
                                if inspect.iscoroutine(result):
                                    logger.warning(
                                        f"Service {name}.on_pre_destroy() is async but called synchronously."
                                    )
                                    result.close()
                                logger.debug(f"Called on_pre_destroy for service: {name}")
                        except Exception as e:
                            logger.error(f"Error in on_shutdown/on_pre_destroy for {name}: {e}", exc_info=True)
                            # 继续关闭其他服务

            # 然后调用 on_destroy()
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
