# -*- coding: utf-8 -*-
"""Test WebSocket Handler with Dependency Injection"""

from cullinan.core import Inject, get_injection_registry, reset_injection_registry
from cullinan.service import service, Service, get_service_registry, reset_service_registry
from cullinan.websocket_registry import websocket_handler, get_websocket_registry, reset_websocket_registry


def test_websocket_with_injection():
    """Test that WebSocket handlers support dependency injection"""

    # Reset all registries
    reset_injection_registry()
    reset_service_registry()
    reset_websocket_registry()

    # Configure injection
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n=== WebSocket Dependency Injection Test ===\n")

    # Define a service
    @service
    class NotificationService(Service):
        def send_notification(self, message):
            return f"Notification: {message}"

    # Define WebSocket handler with dependency injection
    @websocket_handler(url='/ws/test')
    class TestWebSocketHandler:
        # Type injection!
        notification_service: NotificationService = Inject()

        def on_open(self):
            return "Connected"

        def on_message(self, message):
            # Use injected service
            result = self.notification_service.send_notification(message)
            return f"Echo: {result}"

    # Check registrations
    websocket_registry = get_websocket_registry()

    print("[1] WebSocket Handler Registration")
    assert websocket_registry.has('TestWebSocketHandler'), "Handler not registered"
    print("  [OK] Handler registered")

    url = websocket_registry.get_url('TestWebSocketHandler')
    assert url == '/ws/test', f"Expected '/ws/test', got '{url}'"
    print(f"  [OK] URL: {url}")

    # Check dependency injection
    print("\n[2] Dependency Injection")
    handler_class = websocket_registry.get('TestWebSocketHandler')
    assert handler_class is not None, "Handler class not found"

    # Instantiate handler (should auto-inject)
    handler = handler_class()

    assert hasattr(handler, 'notification_service'), "notification_service not injected"
    assert isinstance(handler.notification_service, NotificationService), \
        "notification_service is not NotificationService instance"
    print("  [OK] NotificationService injected")

    # Test functionality
    print("\n[3] Functionality Test")
    result = handler.on_message("test message")
    expected = "Echo: Notification: test message"
    assert result == expected, f"Expected '{expected}', got '{result}'"
    print(f"  [OK] Result: {result}")

    print("\n" + "="*50)
    print("SUCCESS: WebSocket dependency injection works!")
    print("="*50)

    return True


if __name__ == '__main__':
    try:
        success = test_websocket_with_injection()
        if success:
            print("\n[OK] WebSocket injection test passed")
            exit(0)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

