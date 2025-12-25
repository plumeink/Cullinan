# -*- coding: utf-8 -*-
"""Application Lifecycle Integration for Cullinan Framework

Integrates the lifecycle management system with the application startup/shutdown flow.
"""

import signal
import asyncio
import logging
from typing import Optional, List, Callable
import tornado.ioloop

from cullinan.service.registry import get_service_registry
from cullinan.core.injection import get_injection_registry

logger = logging.getLogger(__name__)


class CullinanApplication:
    """Cullinan Application with complete lifecycle management.

    Handles:
    - Dependency injection setup
    - Service discovery and registration
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
        self._ioloop: Optional[tornado.ioloop.IOLoop] = None
        self._shutdown_handlers: List[Callable] = []
        self._running = False

    async def startup(self) -> None:
        """Execute application startup sequence.

        Steps:
        1. Configure dependency injection
        2. Discover and instantiate services
        """
        logger.info("╔═══════════════════════════════════════════════════════════════════╗")
        logger.info("║           Cullinan Framework - Application Starting              ║")
        logger.info("╚═══════════════════════════════════════════════════════════════════╝")

        try:
            # Step 1: Configure dependency injection
            logger.info("\n[1/4] Configuring dependency injection...")
            # Get registries (ServiceRegistry auto-registers itself as provider)
            injection_registry = get_injection_registry()
            service_registry = get_service_registry()

            # Initialize InjectionExecutor with the registry
            from cullinan.core.injection_executor import InjectionExecutor, set_injection_executor
            executor = InjectionExecutor(injection_registry)
            set_injection_executor(executor)
            logger.info("  [OK] Dependency injection configured (InjectionExecutor initialized)")

            # Step 2: Discover services (they are registered by @service decorator)
            logger.info("\n[2/4] Discovering services...")
            service_count = service_registry.count()
            logger.info(f"  [OK] Found {service_count} registered services")

            # Step 3: Initialize all services (按依赖顺序实例化 + 调用 on_init)
            logger.info("\n[3/4] Initializing services...")
            if service_count > 0:
                # 使用 initialize_all() 按依赖顺序初始化所有 Service
                service_registry.initialize_all()
                logger.info(f"  [OK] All {service_count} services initialized")
            else:
                logger.info("  [INFO] No services to initialize")

            # Step 4: Verify injection system
            logger.info("\n[4/4] Verifying injection system...")
            from cullinan.core.injection_executor import has_injection_executor
            if has_injection_executor():
                cache_stats = executor.get_cache_stats()
                logger.info(f"  [OK] Injection system ready (cache: {cache_stats['hits']} hits, {cache_stats['misses']} misses)")
            else:
                logger.warning("  [WARN] InjectionExecutor not properly initialized")

            self._running = True

            logger.info("\n╔═══════════════════════════════════════════════════════════════════╗")
            logger.info("║         Application Started Successfully - Ready to Serve         ║")
            logger.info("╚═══════════════════════════════════════════════════════════════════╝\n")

        except Exception as e:
            logger.error(f"\n[ERROR] Application startup failed: {e}")
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
            # Execute custom shutdown handlers
            logger.info("\nExecuting shutdown handlers...")
            for handler in self._shutdown_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler()
                    else:
                        handler()
                except Exception as e:
                    logger.error(f"  [ERROR] Shutdown handler error: {e}")
                    if not force:
                        raise

            self._running = False

            logger.info("\n╔═══════════════════════════════════════════════════════════════════╗")
            logger.info("║              Application Shutdown Completed                       ║")
            logger.info("╚═══════════════════════════════════════════════════════════════════╝\n")

        except Exception as e:
            logger.error(f"\n[ERROR] Shutdown error: {e}")
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

