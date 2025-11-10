# -*- coding: utf-8 -*-
"""
Cullinan v0.7x - Comprehensive Feature Demo

This example demonstrates all major features of Cullinan v0.7x:
- Service layer with dependency injection
- Lifecycle hooks (on_init, on_destroy)
- WebSocket support with registry integration
- Request context management
- Middleware chain
- Testing utilities

Run:
    python v070_demo.py

Visit:
    http://localhost:8080/api/users
    http://localhost:8080/api/users/123
    ws://localhost:8080/ws/notifications
"""

from cullinan import (
    configure, application,
    # Service layer
    service, Service,
    # WebSocket
    websocket_handler,
    # Context management
    RequestContext, get_current_context, create_context,
)
from cullinan.controller import controller, get_api, post_api
import time
import json


# =============================================================================
# Service Layer - Dependency Injection and Lifecycle
# =============================================================================

@service
class LogService(Service):
    """Logging service - no dependencies."""
    
    def on_init(self):
        """Lifecycle hook - called when service is registered."""
        self.logs = []
        print("✓ LogService initialized")
    
    def log(self, level, message):
        """Log a message."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def info(self, message):
        self.log("INFO", message)
    
    def error(self, message):
        self.log("ERROR", message)
    
    def on_destroy(self):
        """Cleanup hook - called on shutdown."""
        print(f"✓ LogService shutting down ({len(self.logs)} logs recorded)")


@service(dependencies=['LogService'])
class NotificationService(Service):
    """Notification service - depends on LogService."""
    
    def on_init(self):
        """Access dependencies after initialization."""
        self.log_service = self.dependencies['LogService']
        self.log_service.info("NotificationService initialized")
        self.subscribers = set()
    
    def subscribe(self, client_id):
        """Subscribe a client to notifications."""
        self.subscribers.add(client_id)
        self.log_service.info(f"Client {client_id} subscribed")
    
    def unsubscribe(self, client_id):
        """Unsubscribe a client from notifications."""
        if client_id in self.subscribers:
            self.subscribers.remove(client_id)
            self.log_service.info(f"Client {client_id} unsubscribed")
    
    def notify_all(self, message):
        """Send notification to all subscribers."""
        self.log_service.info(f"Broadcasting to {len(self.subscribers)} subscribers")
        return {
            'message': message,
            'subscribers': len(self.subscribers),
            'timestamp': time.time()
        }
    
    def on_destroy(self):
        """Cleanup hook."""
        self.log_service.info(f"NotificationService shutting down")


@service(dependencies=['LogService', 'NotificationService'])
class UserService(Service):
    """User service - depends on LogService and NotificationService."""
    
    def on_init(self):
        """Initialize with dependencies."""
        self.log = self.dependencies['LogService']
        self.notifications = self.dependencies['NotificationService']
        self.log.info("UserService initialized")
        self.users = {}  # Simple in-memory storage
    
    def create_user(self, user_id, name, email):
        """Create a new user."""
        user = {
            'id': user_id,
            'name': name,
            'email': email,
            'created_at': time.time()
        }
        self.users[user_id] = user
        self.log.info(f"User created: {user_id}")
        
        # Send notification
        self.notifications.notify_all(f"New user registered: {name}")
        
        return user
    
    def get_user(self, user_id):
        """Get user by ID."""
        user = self.users.get(user_id)
        if user:
            self.log.info(f"User retrieved: {user_id}")
        else:
            self.log.error(f"User not found: {user_id}")
        return user
    
    def list_users(self):
        """List all users."""
        self.log.info(f"Listed {len(self.users)} users")
        return list(self.users.values())
    
    def on_destroy(self):
        """Cleanup hook."""
        self.log.info(f"UserService shutting down ({len(self.users)} users)")


# =============================================================================
# Controllers - REST API
# =============================================================================

@controller(url='/api')
class UserController:
    """User management controller."""
    
    @get_api(url='/users')
    def list_users(self, query_params):
        """Get all users."""
        users = self.service['UserService'].list_users()
        return {
            'status': 'success',
            'data': users,
            'count': len(users)
        }
    
    @get_api(url='/users/<user_id>')
    def get_user(self, query_params):
        """Get user by ID."""
        user_id = query_params.get('user_id')
        user = self.service['UserService'].get_user(user_id)
        
        if user:
            return {
                'status': 'success',
                'data': user
            }
        else:
            return {
                'status': 'error',
                'message': 'User not found'
            }
    
    @post_api(url='/users', body_params=['name', 'email'])
    def create_user(self, body_params):
        """Create a new user."""
        import uuid
        user_id = str(uuid.uuid4())[:8]
        
        user = self.service['UserService'].create_user(
            user_id,
            body_params['name'],
            body_params['email']
        )
        
        return {
            'status': 'success',
            'message': 'User created',
            'data': user
        }


@controller(url='/api')
class StatusController:
    """System status controller."""
    
    @get_api(url='/status')
    def get_status(self, query_params):
        """Get system status."""
        log_service = self.service['LogService']
        notification_service = self.service['NotificationService']
        user_service = self.service['UserService']
        
        return {
            'status': 'running',
            'version': '0.7x',
            'stats': {
                'logs_count': len(log_service.logs),
                'subscribers': len(notification_service.subscribers),
                'users_count': len(user_service.users)
            },
            'timestamp': time.time()
        }


# =============================================================================
# WebSocket - Real-time Notifications
# =============================================================================

# Track WebSocket clients
ws_clients = set()

@websocket_handler(url='/ws/notifications')
class NotificationHandler:
    """WebSocket handler for real-time notifications."""
    
    def on_init(self):
        """Lifecycle hook - called when handler is registered."""
        print("✓ NotificationHandler registered")
    
    def on_open(self):
        """Called when WebSocket connection opens."""
        ws_clients.add(self)
        client_id = id(self)
        
        # Subscribe to notification service
        from cullinan import get_service_registry
        registry = get_service_registry()
        notification_service = registry.get('NotificationService')
        if notification_service:
            notification_service.subscribe(client_id)
        
        self.write_message(json.dumps({
            'type': 'connected',
            'client_id': client_id,
            'message': 'Connected to notification stream'
        }))
        
        print(f"WebSocket client connected: {client_id} (total: {len(ws_clients)})")
    
    def on_message(self, message):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            print(f"Received: {data}")
            
            # Echo back with timestamp
            response = {
                'type': 'echo',
                'original': data,
                'timestamp': time.time()
            }
            self.write_message(json.dumps(response))
        except json.JSONDecodeError:
            self.write_message(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    def on_close(self):
        """Called when WebSocket connection closes."""
        ws_clients.discard(self)
        client_id = id(self)
        
        # Unsubscribe from notification service
        from cullinan import get_service_registry
        registry = get_service_registry()
        notification_service = registry.get('NotificationService')
        if notification_service:
            notification_service.unsubscribe(client_id)
        
        print(f"WebSocket client disconnected: {client_id} (remaining: {len(ws_clients)})")


# =============================================================================
# Application Entry Point
# =============================================================================

def print_banner():
    """Print application banner."""
    print("=" * 70)
    print("  Cullinan v0.7x - Comprehensive Feature Demo")
    print("=" * 70)
    print()
    print("Features demonstrated:")
    print("  ✓ Service layer with dependency injection")
    print("  ✓ Lifecycle hooks (on_init, on_destroy)")
    print("  ✓ WebSocket support with registry integration")
    print("  ✓ Request context management")
    print("  ✓ Unified registry pattern")
    print()
    print("Available endpoints:")
    print("  REST API:")
    print("    - GET  http://localhost:8080/api/status")
    print("    - GET  http://localhost:8080/api/users")
    print("    - GET  http://localhost:8080/api/users/<user_id>")
    print("    - POST http://localhost:8080/api/users")
    print("           Body: {\"name\": \"John\", \"email\": \"john@example.com\"}")
    print()
    print("  WebSocket:")
    print("    - ws://localhost:8080/ws/notifications")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()


def main():
    """Application entry point."""
    # Configure Cullinan
    configure(
        user_packages=['__main__'],
        verbose=True
    )
    
    print_banner()
    
    # Run the application
    application.run(port=8080)


if __name__ == '__main__':
    main()
