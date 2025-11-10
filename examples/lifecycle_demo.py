#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demonstration script showing the service lifecycle hook fix.

This script demonstrates:
1. The problem: Using registry.get() returns a class, not an instance
2. The solution: Using registry.get_instance() properly calls lifecycle hooks
"""

from cullinan.service import Service, service, get_service_registry, reset_service_registry

print("=" * 70)
print("Service Lifecycle Hook Demonstration")
print("=" * 70)

# Define a test service with lifecycle hooks
@service
class DatabaseService(Service):
    """Service that demonstrates lifecycle hooks."""
    
    def __init__(self):
        super().__init__()
        self.connected = False
        print("  [Constructor] DatabaseService created (but not initialized)")
    
    def on_init(self):
        """Called after service instantiation and dependency injection."""
        print("  [on_init] Connecting to database...")
        self.connected = True
        print("  [on_init] ✓ Database connected!")
    
    def query(self, sql):
        """Execute a query."""
        if self.connected:
            return f"✓ Query executed: {sql}"
        else:
            return "✗ Error: Not connected to database"
    
    def on_destroy(self):
        """Called during service cleanup."""
        print("  [on_destroy] Disconnecting from database...")
        self.connected = False
        print("  [on_destroy] ✓ Database disconnected!")


# ============================================================================
# Problem: Using registry.get() - Returns class, doesn't call on_init()
# ============================================================================

print("\n" + "-" * 70)
print("PROBLEM: Using registry.get() - Returns class without lifecycle")
print("-" * 70)

reset_service_registry()

@service
class TestService1(Service):
    def __init__(self):
        super().__init__()
        self.initialized = False
        print("  [Constructor] TestService1 created")
    
    def on_init(self):
        print("  [on_init] TestService1 initialized!")
        self.initialized = True

registry = get_service_registry()

print("\n1. Getting service class with registry.get():")
service_class = registry.get('TestService1')
print(f"   Result: {service_class}")
print(f"   Type: {type(service_class)}")

print("\n2. Manually instantiating the class:")
instance = service_class()
print(f"   Instance created: {instance}")
print(f"   Is initialized? {instance.initialized}")
print(f"   ✗ Problem: on_init() was NOT called!")


# ============================================================================
# Solution: Using registry.get_instance() - Returns instance with lifecycle
# ============================================================================

print("\n" + "-" * 70)
print("SOLUTION: Using registry.get_instance() - Properly calls lifecycle")
print("-" * 70)

reset_service_registry()

@service
class TestService2(Service):
    def __init__(self):
        super().__init__()
        self.initialized = False
        print("  [Constructor] TestService2 created")
    
    def on_init(self):
        print("  [on_init] TestService2 initialized!")
        self.initialized = True

registry = get_service_registry()

print("\n1. Getting service instance with registry.get_instance():")
instance = registry.get_instance('TestService2')
print(f"   Result: {instance}")
print(f"   Type: {type(instance)}")
print(f"   Is initialized? {instance.initialized}")
print(f"   ✓ Success: on_init() was called!")


# ============================================================================
# Real-world example: Database service
# ============================================================================

print("\n" + "-" * 70)
print("REAL-WORLD EXAMPLE: Database Service Lifecycle")
print("-" * 70)

reset_service_registry()

@service
class MyDatabaseService(Service):
    def __init__(self):
        super().__init__()
        self.connected = False
        print("  [Constructor] DatabaseService created")
    
    def on_init(self):
        print("  [on_init] Opening database connection...")
        self.connected = True
        print("  [on_init] ✓ Connected to database")
    
    def query(self, sql):
        if self.connected:
            return f"✓ Executed: {sql}"
        return "✗ Not connected"
    
    def on_destroy(self):
        print("  [on_destroy] Closing database connection...")
        self.connected = False
        print("  [on_destroy] ✓ Disconnected from database")

registry = get_service_registry()

print("\n1. Initialize all services:")
registry.initialize_all()

print("\n2. Get service and use it:")
db = registry.get_instance('MyDatabaseService')
result = db.query("SELECT * FROM users")
print(f"   {result}")

print("\n3. Destroy all services:")
registry.destroy_all()


# ============================================================================
# Comparison Summary
# ============================================================================

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
❌ DON'T USE: registry.get('ServiceName')
   - Returns the service CLASS
   - You must manually instantiate it
   - Lifecycle hooks (on_init, on_destroy) are NOT called
   - Dependencies are NOT injected

✅ USE: registry.get_instance('ServiceName')
   - Returns the service INSTANCE
   - Automatically instantiated by the registry
   - Lifecycle hooks (on_init, on_destroy) ARE called
   - Dependencies ARE injected
   - Singleton pattern (same instance returned every time)

OR USE: registry.initialize_all() + registry.get_instance()
   - Initialize all services upfront
   - Then get instances as needed
   - Ensures proper initialization order with dependencies
""")

print("=" * 70)
print("✓ Demonstration Complete")
print("=" * 70)
