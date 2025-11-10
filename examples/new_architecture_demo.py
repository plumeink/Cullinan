#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cullinan v0.8.0 - New Architecture Demonstration

This example demonstrates the new modular architecture with:
- Service layer with dependency injection
- Lifecycle management
- Middleware chain
- Monitoring hooks

Run this file to see the new features in action.
"""

import time
from cullinan import (
    # Service layer
    service, Service, get_service_registry,
    # Middleware
    Middleware, MiddlewareChain,
    # Monitoring
    MonitoringHook, get_monitoring_manager,
)


# =============================================================================
# Service Layer Example
# =============================================================================

@service
class LogService(Service):
    """Simple logging service (no dependencies)."""
    
    def __init__(self):
        super().__init__()
        self.logs = []
    
    def log(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def on_init(self):
        self.log("LogService initialized")
    
    def on_destroy(self):
        self.log("LogService shutting down")
        print(f"Total logs: {len(self.logs)}")


@service(dependencies=['LogService'])
class EmailService(Service):
    """Email service with dependency on LogService."""
    
    def on_init(self):
        self.log = self.dependencies['LogService']
        self.log.log("EmailService initialized")
    
    def send_email(self, to, subject, body):
        self.log.log(f"Sending email to {to}: {subject}")
        # Simulate email sending
        return True
    
    def on_destroy(self):
        self.log.log("EmailService shutting down")


@service(dependencies=['LogService', 'EmailService'])
class UserService(Service):
    """User service with multiple dependencies."""
    
    def on_init(self):
        self.log = self.dependencies['LogService']
        self.email = self.dependencies['EmailService']
        self.log.log("UserService initialized")
    
    def create_user(self, name, email):
        self.log.log(f"Creating user: {name}")
        user = {'name': name, 'email': email}
        
        # Send welcome email
        self.email.send_email(email, "Welcome", f"Welcome {name}!")
        
        return user
    
    def on_destroy(self):
        self.log.log("UserService shutting down")


# =============================================================================
# Middleware Example
# =============================================================================

class TimingMiddleware(Middleware):
    """Middleware to track request timing."""
    
    def process_request(self, request):
        request['start_time'] = time.time()
        print(f"→ Request started: {request.get('path', 'unknown')}")
        return request
    
    def process_response(self, request, response):
        duration = time.time() - request.get('start_time', 0)
        print(f"← Response: {response.get('status', 200)} ({duration:.3f}s)")
        return response


class AuthMiddleware(Middleware):
    """Middleware for authentication."""
    
    def process_request(self, request):
        # Simulate auth check
        if request.get('auth_token'):
            print(f"✓ Auth: Valid token")
            request['user'] = {'id': 1, 'name': 'John'}
            return request
        else:
            print(f"✗ Auth: No token provided")
            # In real app, might return None to short-circuit
            return request


# =============================================================================
# Monitoring Example
# =============================================================================

class MetricsHook(MonitoringHook):
    """Monitoring hook for collecting metrics."""
    
    def __init__(self):
        super().__init__()
        self.metrics = {
            'services_initialized': 0,
            'requests': 0,
            'errors': 0,
        }
    
    def on_service_init(self, service_name, service):
        self.metrics['services_initialized'] += 1
        print(f"📊 Metric: Service initialized - {service_name}")
    
    def on_request_start(self, context):
        self.metrics['requests'] += 1
        print(f"📊 Metric: Request started - Total: {self.metrics['requests']}")
    
    def on_error(self, error, context):
        self.metrics['errors'] += 1
        print(f"📊 Metric: Error occurred - {error}")
    
    def get_metrics(self):
        return self.metrics


# =============================================================================
# Main Demo
# =============================================================================

def main():
    print("=" * 70)
    print("Cullinan v0.8.0 - New Architecture Demo")
    print("=" * 70)
    print()
    
    # 1. Initialize services with DI and lifecycle
    print("1. Initializing Services")
    print("-" * 70)
    registry = get_service_registry()
    registry.initialize_all()  # Initializes in dependency order
    print()
    
    # 2. Setup monitoring
    print("2. Setting up Monitoring")
    print("-" * 70)
    metrics_hook = MetricsHook()
    monitoring = get_monitoring_manager()
    monitoring.register(metrics_hook)
    
    # Simulate service init events
    for name in ['LogService', 'EmailService', 'UserService']:
        service = registry.get_instance(name)
        monitoring.on_service_init(name, service)
    print()
    
    # 3. Setup middleware chain
    print("3. Setting up Middleware")
    print("-" * 70)
    middleware_chain = MiddlewareChain()
    middleware_chain.add(TimingMiddleware())
    middleware_chain.add(AuthMiddleware())
    middleware_chain.initialize_all()
    print("Middleware chain ready")
    print()
    
    # 4. Simulate request processing
    print("4. Processing Request")
    print("-" * 70)
    
    # Create mock request
    request = {
        'method': 'POST',
        'path': '/api/users',
        'auth_token': 'valid_token_123',
        'body': {'name': 'Alice', 'email': 'alice@example.com'}
    }
    
    # Process through middleware
    monitoring.on_request_start(request)
    request = middleware_chain.process_request(request)
    
    # Use service to create user
    user_service = registry.get_instance('UserService')
    user = user_service.create_user(
        request['body']['name'],
        request['body']['email']
    )
    print(f"✓ User created: {user}")
    
    # Create mock response
    response = {
        'status': 201,
        'body': user
    }
    
    # Process response through middleware (reverse order)
    response = middleware_chain.process_response(request, response)
    monitoring.on_request_end(request)
    print()
    
    # 5. Show metrics
    print("5. Metrics Summary")
    print("-" * 70)
    metrics = metrics_hook.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    print()
    
    # 6. Cleanup with lifecycle
    print("6. Shutting Down")
    print("-" * 70)
    middleware_chain.destroy_all()
    registry.destroy_all()  # Destroys in reverse order
    print()
    
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Service layer with dependency injection")
    print("  ✓ Lifecycle management (on_init/on_destroy)")
    print("  ✓ Middleware chain (request/response processing)")
    print("  ✓ Monitoring hooks (metrics collection)")
    print("  ✓ Modular architecture")
    print()


if __name__ == '__main__':
    main()
