# -*- coding: utf-8 -*-
"""Enhanced Service base class for Cullinan framework.

Provides lifecycle management and dependency injection support
while maintaining backward compatibility with simple Service usage.
"""

import logging
from cullinan.core.lifecycle_enhanced import LifecycleAware, SmartLifecycle

logger = logging.getLogger(__name__)


class Service(SmartLifecycle):
    """Enhanced base class for services with complete lifecycle support.

    Lifecycle Hooks (Spring Boot style):

    1. on_post_construct() - Quick initialization after dependency injection
       - Equivalent to @PostConstruct in Spring
       - Use for: validation, simple setup

    2. on_startup() - Application startup phase (before accepting requests)
       - Equivalent to SmartLifecycle.start() in Spring
       - Use for: connecting to external services, warming up caches, starting background tasks

    3. on_pre_destroy() - Quick cleanup before shutdown
       - Equivalent to @PreDestroy in Spring
       - Use for: saving state, quick cleanup

    4. on_shutdown() - Application shutdown phase
       - Equivalent to SmartLifecycle.stop() in Spring
       - Use for: graceful shutdown, closing connections, flushing buffers

    All hooks have async versions (append _async to method name).

    Phase Control:
    - Override get_phase() to control startup/shutdown order
    - Lower phase = starts earlier, stops later
    - Default is 0

    Examples:
        # Simple service (backward compatible)
        @service
        class EmailService(Service):
            def send_email(self, to, subject, body):
                print(f"Sending email to {to}")
        
        # Service with lifecycle hooks
        @service
        class CacheService(Service):
            def on_post_construct(self):
                # Quick setup after injection
                self._cache = {}
                logger.info("Cache initialized")

            def on_startup(self):
                # Connect to Redis during startup
                self._redis = redis.Redis(host='localhost')
                logger.info("Connected to Redis")

            def on_shutdown(self):
                # Close connection during shutdown
                if self._redis:
                    self._redis.close()
                logger.info("Redis connection closed")

        # Service with async lifecycle and phase control
        @service
        class BotService(Service):
            def get_phase(self):
                # Start early (before web server)
                return -100

            async def on_startup_async(self):
                # Bot needs to login before web server starts
                self._bot = discord.Client()
                await self._bot.login('token')
                asyncio.create_task(self._bot.connect())
                logger.info("Bot started and logged in")

            async def on_shutdown_async(self):
                # Gracefully disconnect bot
                await self._bot.close()
                logger.info("Bot disconnected")

        # Backward compatible (old style)
        @service(dependencies=['EmailService'])
        class UserService(Service):
            def on_init(self):
                # Old style, still works
                self.email = self.dependencies['EmailService']
    """
    
    def __init__(self):
        """Initialize the service.
        
        Dependencies will be injected by the ServiceRegistry before on_init is called.
        """
        self.dependencies = {}
    
    def on_init(self):
        """Lifecycle hook called after service is created and dependencies are injected.
        
        Override this method to perform initialization that requires dependencies.
        Can be sync or async.
        """
        pass
    
    def on_destroy(self):
        """Lifecycle hook called when service is being destroyed.
        
        Override this method to perform cleanup (close connections, release resources, etc.).
        Can be sync or async.
        """
        pass
