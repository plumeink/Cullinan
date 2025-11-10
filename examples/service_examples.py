# -*- coding: utf-8 -*-
"""
Comprehensive examples demonstrating the enhanced Cullinan service layer.

This file shows various usage patterns from simple to advanced.
"""

from cullinan.service_new import Service, service, get_service_registry


# ============================================================================
# Example 1: Simple Service (Backward Compatible)
# ============================================================================

print("\n" + "="*70)
print("Example 1: Simple Service (Backward Compatible)")
print("="*70)

@service
class LogService(Service):
    """Simple logging service with no dependencies."""
    
    def log(self, message):
        print(f"[LOG] {message}")
        return message


# Initialize and use
registry = get_service_registry()
registry.initialize_all()

log_service = registry.get_instance('LogService')
log_service.log("Application started")


# ============================================================================
# Example 2: Service with Dependencies
# ============================================================================

print("\n" + "="*70)
print("Example 2: Service with Dependencies")
print("="*70)

# Clear registry for fresh start
from cullinan.service_new import reset_service_registry
reset_service_registry()

@service
class EmailService(Service):
    """Email service for sending notifications."""
    
    def send_email(self, to, subject, body):
        print(f"[EMAIL] Sending to {to}: {subject}")
        return True


@service(dependencies=['EmailService'])
class UserService(Service):
    """User service that depends on EmailService."""
    
    def on_init(self):
        """Called after dependencies are injected."""
        self.email = self.dependencies['EmailService']
        print("[UserService] Initialized with EmailService dependency")
    
    def create_user(self, name, email):
        print(f"[UserService] Creating user: {name}")
        user = {'name': name, 'email': email}
        
        # Use injected dependency
        self.email.send_email(email, "Welcome", f"Welcome {name}!")
        
        return user


# Initialize and use
registry = get_service_registry()
registry.initialize_all()

user_service = registry.get_instance('UserService')
user = user_service.create_user('John Doe', 'john@example.com')
print(f"[Result] Created user: {user}")


# ============================================================================
# Example 3: Service with Lifecycle Management
# ============================================================================

print("\n" + "="*70)
print("Example 3: Service with Lifecycle Management")
print("="*70)

reset_service_registry()

@service
class DatabaseService(Service):
    """Database service with connection lifecycle."""
    
    def __init__(self):
        super().__init__()
        self.connection = None
    
    def on_init(self):
        """Initialize database connection."""
        print("[DatabaseService] Opening database connection")
        self.connection = "DB_CONNECTION_OBJECT"
    
    def on_destroy(self):
        """Close database connection."""
        print("[DatabaseService] Closing database connection")
        self.connection = None
    
    def query(self, sql):
        if self.connection:
            print(f"[DatabaseService] Executing: {sql}")
            return f"Result for: {sql}"
        return None


@service(dependencies=['DatabaseService'])
class OrderService(Service):
    """Order service that uses database."""
    
    def on_init(self):
        self.db = self.dependencies['DatabaseService']
        print("[OrderService] Initialized with DatabaseService")
    
    def create_order(self, user_id, amount):
        result = self.db.query(f"INSERT INTO orders VALUES ({user_id}, {amount})")
        return result


# Initialize
registry = get_service_registry()
registry.initialize_all()

# Use services
order_service = registry.get_instance('OrderService')
order = order_service.create_order(123, 99.99)
print(f"[Result] {order}")

# Cleanup (calls on_destroy)
print("\n[Cleanup] Destroying services...")
registry.destroy_all()


# ============================================================================
# Example 4: Multiple Dependencies
# ============================================================================

print("\n" + "="*70)
print("Example 4: Multiple Dependencies")
print("="*70)

reset_service_registry()

@service
class CacheService(Service):
    """Cache service for caching data."""
    
    def __init__(self):
        super().__init__()
        self.cache = {}
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value):
        print(f"[CacheService] Caching {key}")
        self.cache[key] = value


@service
class MetricsService(Service):
    """Metrics service for tracking operations."""
    
    def record(self, metric_name, value):
        print(f"[MetricsService] {metric_name} = {value}")


@service(dependencies=['CacheService', 'MetricsService'])
class ProductService(Service):
    """Product service with multiple dependencies."""
    
    def on_init(self):
        self.cache = self.dependencies['CacheService']
        self.metrics = self.dependencies['MetricsService']
        print("[ProductService] Initialized with CacheService and MetricsService")
    
    def get_product(self, product_id):
        # Try cache first
        cached = self.cache.get(f'product:{product_id}')
        if cached:
            self.metrics.record('cache_hit', 1)
            return cached
        
        # Simulate fetch from database
        self.metrics.record('cache_miss', 1)
        product = {'id': product_id, 'name': f'Product {product_id}'}
        
        # Cache it
        self.cache.set(f'product:{product_id}', product)
        
        return product


# Initialize
registry = get_service_registry()
registry.initialize_all()

# Use service
product_service = registry.get_instance('ProductService')

# First call - cache miss
print("\n[First call]")
product1 = product_service.get_product(101)
print(f"[Result] {product1}")

# Second call - cache hit
print("\n[Second call]")
product2 = product_service.get_product(101)
print(f"[Result] {product2}")


# ============================================================================
# Example 5: Testing with Mocks
# ============================================================================

print("\n" + "="*70)
print("Example 5: Testing with Mocks")
print("="*70)

from cullinan.testing import MockService, TestRegistry

class MockEmailService(MockService):
    """Mock email service for testing."""
    
    def send_email(self, to, subject, body):
        self.record_call('send_email', to=to, subject=subject, body=body)
        print(f"[MOCK] Email sent to {to}")
        return True


# Create isolated test registry
test_registry = TestRegistry()

# Define service to test
class NotificationService(Service):
    def on_init(self):
        self.email = self.dependencies.get('EmailService')
    
    def notify_user(self, user_email, message):
        return self.email.send_email(user_email, "Notification", message)


# Register mock and service under test
test_registry.register('EmailService', MockEmailService)
test_registry.register('NotificationService', NotificationService, 
                       dependencies=['EmailService'])

# Initialize
test_registry.initialize_all()

# Test
notification_service = test_registry.get_instance('NotificationService')
email_mock = test_registry.get_instance('EmailService')

result = notification_service.notify_user('test@example.com', 'Hello!')

# Verify
print(f"\n[Test] Email service was called: {email_mock.was_called('send_email')}")
print(f"[Test] Call count: {email_mock.call_count('send_email')}")

call_args = email_mock.get_call_args('send_email')
print(f"[Test] Called with: to={call_args['to']}, subject={call_args['subject']}")

# Cleanup
test_registry.destroy_all()


print("\n" + "="*70)
print("All Examples Completed Successfully!")
print("="*70)
