# -*- coding: utf-8 -*-
"""Complete Example: Discord Bot Service with Lifecycle Management

This example demonstrates:
1. Bot service that starts BEFORE web server
2. Proper lifecycle management with async operations
3. Integration with other services
4. Graceful shutdown

Requirements:
    pip install discord.py aiohttp
"""

import asyncio
import logging
from typing import Optional
import discord
from discord.ext import commands

from cullinan.core import Inject
from cullinan.service import service, Service
from cullinan.controller import controller, get_api

logger = logging.getLogger(__name__)


# ============================================================================
# Services
# ============================================================================

@service
class ConfigService(Service):
    """Configuration service (loads first)"""

    def get_phase(self) -> int:
        # Start very early (config needed by everyone)
        return -200

    def on_post_construct(self) -> None:
        """Load configuration"""
        logger.info("Loading configuration...")
        # In real app, load from file/env
        self.config = {
            'bot_token': 'YOUR_BOT_TOKEN_HERE',
            'bot_prefix': '!',
            'db_url': 'postgresql://localhost/mydb'
        }
        logger.info("Configuration loaded")

    def get(self, key: str, default=None):
        return self.config.get(key, default)


@service
class DatabaseService(Service):
    """Database service with connection pooling"""

    config: ConfigService = Inject()

    def get_phase(self) -> int:
        # Start early (many services depend on database)
        return -100

    async def on_startup_async(self) -> None:
        """Initialize database connection pool"""
        logger.info("Creating database connection pool...")

        # Simulate async connection
        await asyncio.sleep(0.5)

        db_url = self.config.get('db_url')
        logger.info(f"Connected to database: {db_url}")
        self._connected = True

    async def on_shutdown_async(self) -> None:
        """Close database connections"""
        logger.info("Closing database connections...")
        await asyncio.sleep(0.2)
        self._connected = False
        logger.info("Database connections closed")

    async def execute(self, query: str):
        """Execute a database query"""
        if not self._connected:
            raise RuntimeError("Database not connected")
        logger.debug(f"Executing query: {query}")
        # Simulate query
        await asyncio.sleep(0.1)
        return {"result": "success"}


@service
class DiscordBotService(Service):
    """Discord Bot Service with full lifecycle management

    This bot:
    - Starts BEFORE the web server (phase -50)
    - Logs in and connects during on_startup_async
    - Runs in background while web server handles requests
    - Gracefully disconnects during shutdown
    """

    config: ConfigService = Inject()
    database: DatabaseService = Inject()

    def __init__(self):
        super().__init__()
        self._bot: Optional[discord.Client] = None
        self._bot_task: Optional[asyncio.Task] = None
        self._ready = asyncio.Event()

    def get_phase(self) -> int:
        # Start before web server, but after database
        return -50

    def on_post_construct(self) -> None:
        """Create bot instance (sync, quick)"""
        logger.info("Creating Discord bot instance...")

        intents = discord.Intents.default()
        intents.message_content = True

        self._bot = commands.Bot(
            command_prefix=self.config.get('bot_prefix', '!'),
            intents=intents
        )

        # Register event handlers
        @self._bot.event
        async def on_ready():
            logger.info(f"Bot logged in as {self._bot.user}")
            self._ready.set()

        @self._bot.event
        async def on_message(message):
            if message.author == self._bot.user:
                return

            # Log message to database
            await self.database.execute(
                f"INSERT INTO messages VALUES ('{message.content}')"
            )

            # Process commands
            await self._bot.process_commands(message)

        # Add commands
        @self._bot.command(name='hello')
        async def hello(ctx):
            await ctx.send(f'Hello {ctx.author.mention}!')

        @self._bot.command(name='ping')
        async def ping(ctx):
            await ctx.send(f'Pong! Latency: {round(self._bot.latency * 1000)}ms')

        logger.info("Discord bot instance created")

    async def on_startup_async(self) -> None:
        """Start and login bot (async, can take time)"""
        logger.info("Starting Discord bot...")
        logger.info("  - Logging in to Discord...")

        token = self.config.get('bot_token')
        if not token or token == 'YOUR_BOT_TOKEN_HERE':
            logger.warning("  ! No valid bot token configured, using mock mode")
            # For demo purposes, simulate bot startup
            await asyncio.sleep(1)
            self._ready.set()
            logger.info("  ✓ Bot started in MOCK mode")
            return

        # Start bot in background
        self._bot_task = asyncio.create_task(self._bot.start(token))

        # Wait for bot to be ready (with timeout)
        try:
            await asyncio.wait_for(self._ready.wait(), timeout=30)
            logger.info("  ✓ Bot logged in and ready")
            logger.info(f"  ✓ Bot is serving {len(self._bot.guilds)} guilds")
        except asyncio.TimeoutError:
            logger.error("  ✗ Bot startup timeout")
            raise

    async def on_shutdown_async(self) -> None:
        """Gracefully disconnect bot"""
        logger.info("Shutting down Discord bot...")

        if self._bot and not self._bot.is_closed():
            logger.info("  - Closing bot connection...")
            await self._bot.close()
            logger.info("  ✓ Bot connection closed")

        if self._bot_task and not self._bot_task.done():
            logger.info("  - Cancelling bot task...")
            self._bot_task.cancel()
            try:
                await self._bot_task
            except asyncio.CancelledError:
                pass
            logger.info("  ✓ Bot task cancelled")

        logger.info("  ✓ Discord bot shutdown complete")

    # Public API for controllers

    def is_ready(self) -> bool:
        """Check if bot is ready"""
        return self._ready.is_set() and self._bot is not None

    async def send_message(self, channel_id: int, content: str):
        """Send a message to a channel"""
        if not self.is_ready():
            raise RuntimeError("Bot is not ready")

        channel = self._bot.get_channel(channel_id)
        if channel:
            await channel.send(content)

    def get_guild_count(self) -> int:
        """Get number of guilds bot is in"""
        if not self.is_ready():
            return 0
        return len(self._bot.guilds)

    def get_latency(self) -> float:
        """Get bot latency in milliseconds"""
        if not self.is_ready():
            return -1
        return round(self._bot.latency * 1000, 2)


# ============================================================================
# Controllers (start AFTER bot)
# ============================================================================

@controller(url='/api/bot')
class BotController:
    """Web API for bot management

    This controller starts AFTER the bot service,
    so it can immediately handle requests without waiting.
    """

    bot: DiscordBotService = Inject()

    @get_api(url='/status')
    def get_bot_status(self, query_params):
        """Get bot status"""
        return {
            'ready': self.bot.is_ready(),
            'guilds': self.bot.get_guild_count(),
            'latency_ms': self.bot.get_latency()
        }

    @get_api(url='/send', query_params=['channel_id', 'message'])
    async def send_message(self, query_params):
        """Send a message through bot"""
        channel_id = int(query_params.get('channel_id', 0))
        message = query_params.get('message', 'Hello!')

        if not self.bot.is_ready():
            return {'error': 'Bot is not ready'}

        try:
            await self.bot.send_message(channel_id, message)
            return {'success': True, 'message': 'Message sent'}
        except Exception as e:
            return {'error': str(e)}


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    """
    To run this example:
    
    1. Set your Discord bot token in ConfigService or environment variable
    2. python -m examples.discord_bot_lifecycle_example
    
    Expected startup order:
    1. ConfigService (phase -200)
    2. DatabaseService (phase -100)
    3. DiscordBotService (phase -50)
    4. BotController (phase 0)
    5. Web server starts
    
    The bot will be fully logged in and running BEFORE
    the first web request can be handled!
    """

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run application
    from cullinan.app import create_app

    app = create_app(shutdown_timeout=30)

    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║     Discord Bot + Web Service Lifecycle Example                  ║
    ║                                                                   ║
    ║  The bot will start BEFORE the web server accepts requests       ║
    ║  This ensures no request arrives before the bot is ready         ║
    ║                                                                   ║
    ║  Try:                                                             ║
    ║    GET /api/bot/status - Check bot status                        ║
    ║    GET /api/bot/send?channel_id=123&message=Hi - Send message    ║
    ║                                                                   ║
    ║  Press Ctrl+C for graceful shutdown                              ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)

    app.run()

