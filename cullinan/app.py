# -*- coding: utf-8 -*-
"""Application Lifecycle Integration for Cullinan Framework

Integrates the lifecycle management system with the application startup/shutdown flow.
"""

import signal
import asyncio
import logging
from typing import Optional, List, Callable
import tornado.ioloop

from cullinan.core.lifecycle_enhanced import get_lifecycle_manager, LifecycleManager
from cullinan.service.registry import get_service_registry
from cullinan.core.injection import get_injection_registry

logger = logging.getLogger(__name__)


class CullinanApplication:
    """Cullinan Application with complete lifecycle management.

    Handles:
    - Dependency injection setup
    - Service discovery and registration
    - Lifecycle-managed startup
    - Graceful shutdown with timeout
    - Signal handling (SIGINT, SIGTERM)

    Usage:
        app = CullinanApplication()
        app.run()
    """

    def __init__(self, shutdown_timeout: int = 30):
        """Initialize the application.

        Args:
            shutdown_timeout: Graceful shutdown timeout in seconds
        """
        self._shutdown_timeout = shutdown_timeout
        self._lifecycle_manager: Optional[LifecycleManager] = None
        self._ioloop: Optional[tornado.ioloop.IOLoop] = None
        self._shutdown_handlers: List[Callable] = []
        self._running = False

    async def startup(self) -> None:
        """Execute application startup sequence.

        Steps:
        1. Configure dependency injection
        2. Discover and instantiate services
        3. Register services with lifecycle manager
        4. Execute lifecycle startup phases
        """
        logger.info("╔═══════════════════════════════════════════════════════════════════╗")
        logger.info("║           Cullinan Framework - Application Starting              ║")
        logger.info("╚═══════════════════════════════════════════════════════════════════╝")

        try:
            # Step 1: Configure dependency injection
            logger.info("\n[1/4] Configuring dependency injection...")
            injection_registry = get_injection_registry()
            service_registry = get_service_registry()
            injection_registry.add_provider_registry(service_registry, priority=100)
            logger.info("  ✓ Dependency injection configured")

            # Step 2: Discover services (they are registered by @service decorator)
            logger.info("\n[2/4] Discovering services...")
            service_count = service_registry.count()
            logger.info(f"  ✓ Found {service_count} registered services")

            # Step 3: Instantiate all services and register with lifecycle manager
            logger.info("\n[3/4] Instantiating services and setting up lifecycle...")
            self._lifecycle_manager = get_lifecycle_manager()

            for service_name in service_registry.list_all():
                # Get or create service instance
                service_instance = service_registry.get_instance(service_name)

                if service_instance is None:
                    logger.warning(f"  ! Failed to instantiate {service_name}")
                    continue

                # Get dependencies for this service
                metadata = service_registry.get_metadata(service_name)
                dependencies = metadata.get('dependencies', []) if metadata else []

                # Register with lifecycle manager
                self._lifecycle_manager.register(
                    service_instance,
                    name=service_name,
                    dependencies=dependencies
                )
                logger.debug(f"  ✓ Registered {service_name} for lifecycle management")

            logger.info(f"  ✓ Lifecycle management configured for {service_count} services")

            # Step 4: Execute lifecycle startup
            logger.info("\n[4/4] Executing lifecycle startup phases...")
            await self._lifecycle_manager.startup()

            self._running = True

            logger.info("\n╔═══════════════════════════════════════════════════════════════════╗")
            logger.info("║         Application Started Successfully - Ready to Serve         ║")
            logger.info("╚═══════════════════════════════════════════════════════════════════╝\n")

        except Exception as e:
            logger.error(f"\n✗ Application startup failed: {e}")
            raise

    async def shutdown(self, force: bool = False) -> None:
        """Execute application shutdown sequence.

        Args:
            force: If True, force shutdown even on errors
        """
        if not self._running:
            return

        logger.info("\n╔═══════════════════════════════════════════════════════════════════╗")
        logger.info("║              Application Shutting Down Gracefully                 ║")
        logger.info("╚═══════════════════════════════════════════════════════════════════╝")

        try:
            # Execute lifecycle shutdown
            if self._lifecycle_manager:
                await self._lifecycle_manager.shutdown(
                    timeout=self._shutdown_timeout,
                    force=force
                )

            # Execute custom shutdown handlers
            logger.info("\nExecuting custom shutdown handlers...")
            for handler in self._shutdown_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler()
                    else:
                        handler()
                except Exception as e:
                    logger.error(f"  ✗ Shutdown handler error: {e}")
                    if not force:
                        raise

            self._running = False

            logger.info("\n╔═══════════════════════════════════════════════════════════════════╗")
            logger.info("║              Application Shutdown Completed                       ║")
            logger.info("╚═══════════════════════════════════════════════════════════════════╝\n")

        except Exception as e:
            logger.error(f"\n✗ Shutdown error: {e}")
            if not force:
                raise

    def add_shutdown_handler(self, handler: Callable) -> None:
        """Add a custom shutdown handler.

        Args:
            handler: Callable to execute during shutdown (can be async)
        """
        self._shutdown_handlers.append(handler)

    def run(self) -> None:
        """Run the application with IOLoop.

        This method:
        1. Executes startup
        2. Registers signal handlers
        3. Starts the IOLoop
        4. Handles graceful shutdown on signals
        """
        self._ioloop = tornado.ioloop.IOLoop.current()

        # Execute startup
        logger.info("Initializing application...")
        self._ioloop.run_sync(self.startup)

        # Register signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            sig_name = signal.Signals(signum).name
            logger.info(f"\n\nReceived signal {sig_name}, initiating graceful shutdown...")

            async def _shutdown():
                await self.shutdown()
                self._ioloop.stop()

            self._ioloop.add_callback(_shutdown)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start the IOLoop
        logger.info("Starting IOLoop...\n")
        try:
            self._ioloop.start()
        except KeyboardInterrupt:
            # Already handled by signal handler
            pass
        finally:
            logger.info("IOLoop stopped")


def create_app(shutdown_timeout: int = 30) -> CullinanApplication:
    """Factory function to create a Cullinan application.

    Args:
        shutdown_timeout: Graceful shutdown timeout in seconds

    Returns:
        Configured CullinanApplication instance
    """
    return CullinanApplication(shutdown_timeout=shutdown_timeout)


__all__ = [
    'CullinanApplication',
    'create_app',
]

