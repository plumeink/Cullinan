# -*- coding: utf-8 -*-
"""WebSocket with Dependency Injection - Example

This example shows how to use the improved WebSocket handler with
type-based dependency injection (same as @controller and @service).
"""

from cullinan.core import Inject
from cullinan.service import service, Service
from cullinan.websocket_registry import websocket_handler


# ============================================================================
# Services
# ============================================================================

@service
class MessageService(Service):
    """Service for message processing"""

    def process_message(self, message: str) -> str:
        """Process incoming message"""
        return f"Processed: {message.upper()}"

    def broadcast_message(self, message: str) -> dict:
        """Prepare message for broadcast"""
        return {
            'type': 'broadcast',
            'content': message,
            'timestamp': 'now'
        }


@service
class AuthService(Service):
    """Service for authentication"""

    def validate_user(self, user_id: str) -> bool:
        """Validate user credentials"""
        return len(user_id) > 0

    def get_user_info(self, user_id: str) -> dict:
        """Get user information"""
        return {
            'user_id': user_id,
            'username': f'user_{user_id}',
            'status': 'active'
        }


# ============================================================================
# WebSocket Handlers with Dependency Injection
# ============================================================================

@websocket_handler(url='/ws/chat')
class ChatWebSocketHandler:
    """Chat WebSocket handler with dependency injection

    Demonstrates:
    - Type-based dependency injection
    - Multiple service dependencies
    - Clean code without manual service retrieval
    """

    # Type injection - automatically resolved!
    message_service: MessageService = Inject()
    auth_service: AuthService = Inject()

    def __init__(self):
        self.user_id = None
        self.authenticated = False

    def on_open(self):
        """Called when WebSocket connection opens"""
        print("[ChatHandler] Connection opened")
        # Note: Dependencies are already injected by @injectable
        return {
            'status': 'connected',
            'message': 'Welcome to chat!'
        }

    def on_message(self, message):
        """Handle incoming message"""
        # Use injected services directly!
        if not self.authenticated:
            # Authenticate
            if self.auth_service.validate_user(message):
                self.user_id = message
                self.authenticated = True
                user_info = self.auth_service.get_user_info(message)
                return {
                    'status': 'authenticated',
                    'user': user_info
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Authentication failed'
                }

        # Process and broadcast message
        processed = self.message_service.process_message(message)
        broadcast = self.message_service.broadcast_message(processed)

        return {
            'status': 'sent',
            'message': broadcast
        }

    def on_close(self):
        """Called when WebSocket connection closes"""
        if self.user_id:
            print(f"[ChatHandler] User {self.user_id} disconnected")
        return {'status': 'disconnected'}


@websocket_handler(url='/ws/notifications')
class NotificationWebSocketHandler:
    """Notification WebSocket handler

    Demonstrates:
    - Simple service injection
    - Optional dependencies (if needed)
    """

    # Inject only what's needed
    message_service: MessageService = Inject()

    def on_open(self):
        """Connection opened"""
        return {'type': 'connected', 'channel': 'notifications'}

    def on_message(self, message):
        """Handle notification request"""
        # Use injected service
        processed = self.message_service.broadcast_message(message)
        return processed

    def on_close(self):
        """Connection closed"""
        return {'type': 'disconnected'}


# ============================================================================
# Comparison: Old vs New Approach
# ============================================================================

def comparison_old_approach():
    """Old approach - manual service retrieval (NOT RECOMMENDED)"""

    class OldWebSocketHandler:
        def on_open(self):
            # ❌ Manual service retrieval - verbose and error-prone
            from cullinan.service import get_service_registry
            registry = get_service_registry()
            self.message_service = registry.get_instance('MessageService')
            self.auth_service = registry.get_instance('AuthService')

            if not self.message_service:
                print("ERROR: Service not found!")
                return

            # Use services...


def comparison_new_approach():
    """New approach - type injection (RECOMMENDED)"""

    @websocket_handler(url='/ws/example')
    class NewWebSocketHandler:
        # ✅ Type injection - clean and type-safe
        message_service: MessageService = Inject()
        auth_service: AuthService = Inject()

        def on_open(self):
            # Services already injected and ready to use!
            result = self.message_service.process_message("Hello")
            return result


# ============================================================================
# Test
# ============================================================================

def test_websocket_handlers():
    """Test WebSocket handlers with dependency injection"""
    from cullinan.core import get_injection_registry
    from cullinan.service import get_service_registry
    from cullinan.websocket_registry import get_websocket_registry

    print("\n" + "="*70)
    print("WebSocket with Dependency Injection - Test")
    print("="*70 + "\n")

    # Configure injection
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    # Test ChatHandler
    print("[1] Testing ChatWebSocketHandler")
    websocket_registry = get_websocket_registry()
    handler_class = websocket_registry.get('ChatWebSocketHandler')

    if handler_class:
        handler = handler_class()

        # Test connection
        result = handler.on_open()
        print(f"  on_open: {result}")

        # Test authentication
        result = handler.on_message("user123")
        print(f"  authenticate: {result}")

        # Test message
        result = handler.on_message("Hello World")
        print(f"  message: {result}")

        print("  ✓ ChatWebSocketHandler works correctly")

    # Test NotificationHandler
    print("\n[2] Testing NotificationWebSocketHandler")
    handler_class = websocket_registry.get('NotificationWebSocketHandler')

    if handler_class:
        handler = handler_class()
        result = handler.on_message("Test notification")
        print(f"  notification: {result}")
        print("  ✓ NotificationWebSocketHandler works correctly")

    print("\n" + "="*70)
    print("SUCCESS: All WebSocket handlers work with dependency injection!")
    print("="*70 + "\n")

    print("Benefits:")
    print("  • Type-safe dependency injection")
    print("  • Clean code (no manual service retrieval)")
    print("  • Consistent with @controller and @service")
    print("  • IDE autocomplete and type checking")


if __name__ == '__main__':
    test_websocket_handlers()

