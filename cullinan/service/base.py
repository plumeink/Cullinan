# -*- coding: utf-8 -*-
"""Service base class for Cullinan framework.

Provides lifecycle management through the unified core lifecycle system.
All components (@service, @controller, @component) share the same lifecycle.
"""

import logging
from cullinan.core.lifecycle_enhanced import SmartLifecycle

logger = logging.getLogger(__name__)


class Service(SmartLifecycle):
    """Base class for services with unified lifecycle support.

    Lifecycle Hooks (from SmartLifecycle / LifecycleAware):

    1. on_post_construct() - Called after dependency injection
       - Use for: validation, simple setup

    2. on_startup() - Called during application startup
       - Use for: connecting to services, warming up caches, starting background tasks

    3. on_shutdown() - Called during application shutdown
       - Use for: graceful shutdown, closing connections, flushing buffers

    4. on_pre_destroy() - Called before destruction
       - Use for: saving state, quick cleanup

    All hooks have async versions (append _async to method name).

    Phase Control:
    - Override get_phase() to control startup/shutdown order
    - Lower phase = starts earlier, stops later
    - Default is 0

    Examples:
        # Simple service
        @service
        class EmailService(Service):
            def send_email(self, to, subject, body):
                print(f"Sending email to {to}")

        # Service with lifecycle hooks
        @service
        class CacheService(Service):
            def on_post_construct(self):
                self._cache = {}
                logger.info("Cache initialized")

            def on_startup(self):
                self._redis = redis.Redis(host='localhost')
                logger.info("Connected to Redis")

            def on_shutdown(self):
                if self._redis:
                    self._redis.close()
                logger.info("Redis connection closed")

        # Service with async lifecycle and phase control
        @service
        class BotService(Service):
            def get_phase(self):
                return -100  # Start early

            async def on_startup_async(self):
                self._bot = discord.Client()
                await self._bot.login('token')
                logger.info("Bot started")

            async def on_shutdown_async(self):
                await self._bot.close()
                logger.info("Bot disconnected")
    """
    pass
