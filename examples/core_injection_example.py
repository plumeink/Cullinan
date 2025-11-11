# -*- coding: utf-8 -*-
"""Core Dependency Injection System - Complete Example

This example demonstrates the new type-based dependency injection system
in Cullinan framework using cullinan.core.Inject.
"""

from cullinan.core import Inject
from cullinan.service import service, Service


# ============================================================================
# Define Services with Type Injection
# ============================================================================

@service
class DatabaseService(Service):
    """Database service - no dependencies"""

    def query(self, sql: str):
        print(f"[DB] Executing: {sql}")
        return {"result": "data"}


@service
class CacheService(Service):
    """Cache service - no dependencies"""

    def get(self, key: str):
        print(f"[Cache] Get: {key}")
        return None

    def set(self, key: str, value):
        print(f"[Cache] Set: {key} = {value}")


@service
class EmailService(Service):
    """Email service - no dependencies"""

    def send_email(self, to: str, subject: str, body: str):
        print(f"[Email] Sending to {to}: {subject}")
        return True


@service
class UserRepository(Service):
    """User repository - depends on Database and Cache

    Demonstrates:
    - Type annotation injection
    - Multiple dependencies
    """

    # Type injection - automatically injected!
    db: DatabaseService = Inject()
    cache: CacheService = Inject()

    def get_user(self, user_id: int):
        """Get user by ID (with caching)"""
        # Try cache first
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached

        # Query database
        result = self.db.query(f"SELECT * FROM users WHERE id={user_id}")

        # Cache result
        self.cache.set(f"user:{user_id}", result)

        return {"id": user_id, "name": f"User {user_id}"}

    def create_user(self, name: str, email: str):
        """Create a new user"""
        self.db.query(f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')")
        return {"name": name, "email": email}


@service
class UserService(Service):
    """User service - business logic layer

    Demonstrates:
    - Service dependency chain (UserService -> UserRepository -> Database/Cache)
    - Automatic dependency resolution
    """

    # Inject dependencies
    user_repo: UserRepository = Inject()
    email_service: EmailService = Inject()

    def create_user(self, name: str, email: str):
        """Create user and send welcome email"""
        print(f"\n[UserService] Creating user: {name}")

        # Create user via repository
        user = self.user_repo.create_user(name, email)

        # Send welcome email
        self.email_service.send_email(
            to=email,
            subject="Welcome!",
            body=f"Hello {name}, welcome to our service!"
        )

        return user

    def get_user(self, user_id: int):
        """Get user by ID"""
        print(f"\n[UserService] Getting user: {user_id}")
        return self.user_repo.get_user(user_id)


# ============================================================================
# Test the Injection System
# ============================================================================

def test_injection_system():
    """Test the dependency injection system"""
    print("\n" + "="*70)
    print("Testing Core Dependency Injection System")
    print("="*70)

    # Import registries
    from cullinan.service import get_service_registry
    from cullinan.core import get_injection_registry

    # Configure injection system
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n[1] Testing Service Injection")
    print("-" * 70)

    # Get UserService instance (should have all dependencies injected)
    user_service = service_registry.get_instance('UserService')

    print(f"UserService instance: {user_service}")
    print(f"  - user_repo injected: {type(user_service.user_repo).__name__}")
    print(f"  - email_service injected: {type(user_service.email_service).__name__}")
    print(f"  - user_repo.db injected: {type(user_service.user_repo.db).__name__}")
    print(f"  - user_repo.cache injected: {type(user_service.user_repo.cache).__name__}")

    print("\n[2] Testing Functionality")
    print("-" * 70)

    # Test functionality
    user = user_service.create_user("Alice", "alice@example.com")
    print(f"  Created user: {user}")

    user = user_service.get_user(1)
    print(f"  Retrieved user: {user}")

    print("\n[3] Verifying Dependency Chain")
    print("-" * 70)

    # Verify the entire dependency chain is properly injected
    assert user_service.user_repo is not None, "user_repo should be injected"
    assert user_service.email_service is not None, "email_service should be injected"
    assert user_service.user_repo.db is not None, "db should be injected"
    assert user_service.user_repo.cache is not None, "cache should be injected"

    print("  All dependencies properly injected!")
    print("  Dependency chain: UserService -> UserRepository -> Database/Cache")

    print("\n" + "="*70)
    print("SUCCESS: All injection tests passed!")
    print("="*70 + "\n")


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  Cullinan Framework - Core Dependency Injection Example              ║
    ║                                                                      ║
    ║  This example demonstrates:                                          ║
    ║  • Type-based dependency injection (Spring style)                    ║
    ║  • Service -> Service dependency chains                              ║
    ║  • Automatic dependency resolution                                   ║
    ║  • Scan-order independence                                           ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)

    test_injection_system()



# ============================================================================
# Step 1: Define Services with Type Injection
# ============================================================================

@service
class DatabaseService(Service):
    """Database service - no dependencies"""

    def query(self, sql: str):
        print(f"[DB] Executing: {sql}")
        return {"result": "data"}


@service
class CacheService(Service):
    """Cache service - no dependencies"""

    def get(self, key: str):
        print(f"[Cache] Get: {key}")
        return None

    def set(self, key: str, value):
        print(f"[Cache] Set: {key} = {value}")


@service
class EmailService(Service):
    """Email service - no dependencies"""

    def send_email(self, to: str, subject: str, body: str):
        print(f"[Email] Sending to {to}: {subject}")
        return True


@service
class UserRepository(Service):
    """User repository - depends on Database and Cache

    Demonstrates:
    - Type annotation injection
    - Multiple dependencies
    """

    # Type injection - automatically injected!
    db: DatabaseService = Inject()
    cache: CacheService = Inject()

    def get_user(self, user_id: int):
        """Get user by ID (with caching)"""
        # Try cache first
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached

        # Query database
        result = self.db.query(f"SELECT * FROM users WHERE id={user_id}")

        # Cache result
        self.cache.set(f"user:{user_id}", result)

        return {"id": user_id, "name": f"User {user_id}"}

    def create_user(self, name: str, email: str):
        """Create a new user"""
        self.db.query(f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')")
        return {"name": name, "email": email}


@service
class UserService(Service):
    """User service - business logic layer

    Demonstrates:
    - Service dependency chain (UserService -> UserRepository -> Database/Cache)
    - Automatic dependency resolution
    """

    # Inject dependencies
    user_repo: UserRepository = Inject()
    email_service: EmailService = Inject()

    def create_user(self, name: str, email: str):
        """Create user and send welcome email"""
        print(f"\n[UserService] Creating user: {name}")

        # Create user via repository
        user = self.user_repo.create_user(name, email)

        # Send welcome email
        self.email_service.send_email(
            to=email,
            subject="Welcome!",
            body=f"Hello {name}, welcome to our service!"
        )

        return user

    def get_user(self, user_id: int):
        """Get user by ID"""
        print(f"\n[UserService] Getting user: {user_id}")
        return self.user_repo.get_user(user_id)


# ============================================================================
# Step 2: Define Controllers with Type Injection
# ============================================================================

@controller(url='/api/users')
class UserController:
    """User API controller

    Demonstrates:
    - Controller injecting Service
    - Clean separation of concerns
    - Type-safe dependency injection
    """

    # Inject UserService - type annotation makes it clear!
    user_service: UserService = Inject()

    @get('')
    def list_users(self):
        """GET /api/users - List all users"""
        print("\n[Controller] GET /api/users")
        return {
            "users": [
                self.user_service.get_user(1),
                self.user_service.get_user(2)
            ]
        }

    @post('')
    def create_user(self, body_params):
        """POST /api/users - Create a new user"""
        print("\n[Controller] POST /api/users")
        name = body_params.get('name')
        email = body_params.get('email')

        user = self.user_service.create_user(name, email)
        return {
            "success": True,
            "user": user
        }

    @get('/(?P<id>[0-9]+)')
    def get_user(self, url_params):
        """GET /api/users/{id} - Get user by ID"""
        user_id = int(url_params['id'])
        print(f"\n[Controller] GET /api/users/{user_id}")

        user = self.user_service.get_user(user_id)
        return {"user": user}


@controller(url='/api/health')
class HealthController:
    """Health check controller

    Demonstrates:
    - Optional dependency (cache is not required)
    """

    # Optional dependency - won't fail if CacheService is not available
    cache: CacheService = Inject(required=False)

    @get('')
    def health_check(self):
        """GET /api/health - Health check endpoint"""
        print("\n[Controller] GET /api/health")

        status = {
            "status": "healthy",
            "cache_available": not isinstance(self.cache, Inject)
        }

        return status


# ============================================================================
# Step 3: Test the Injection System
# ============================================================================

def test_injection_system():
    """Test the dependency injection system without running the web server"""
    print("\n" + "="*70)
    print("Testing Core Dependency Injection System")
    print("="*70)

    # Import registries
    from cullinan.service import get_service_registry
    from cullinan.core import get_injection_registry

    # Configure injection system
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)

    print("\n[1] Testing Service Injection")
    print("-" * 70)

    # Get UserService instance (should have all dependencies injected)
    user_service = service_registry.get_instance('UserService')

    print(f"UserService instance: {user_service}")
    print(f"  - user_repo injected: {type(user_service.user_repo).__name__}")
    print(f"  - email_service injected: {type(user_service.email_service).__name__}")
    print(f"  - user_repo.db injected: {type(user_service.user_repo.db).__name__}")
    print(f"  - user_repo.cache injected: {type(user_service.user_repo.cache).__name__}")

    # Test functionality
    user_service.create_user("Alice", "alice@example.com")
    user_service.get_user(1)

    print("\n[2] Testing Controller Injection")
    print("-" * 70)

    # Create controller instance
    user_controller = UserController()

    print(f"UserController instance: {user_controller}")
    print(f"  - user_service injected: {type(user_controller.user_service).__name__}")

    # Test controller methods
    result = user_controller.get_user({'id': '1'})
    print(f"  Result: {result}")

    print("\n[3] Testing Optional Dependency")
    print("-" * 70)

    # Create health controller
    health_controller = HealthController()

    print(f"HealthController instance: {health_controller}")
    cache_type = type(health_controller.cache).__name__
    print(f"  - cache injected: {cache_type}")
    print(f"  - cache is optional: {isinstance(health_controller.cache, type(Inject()))}")

    result = health_controller.health_check()
    print(f"  Health check result: {result}")

    print("\n" + "="*70)
    print("All injection tests passed!")
    print("="*70 + "\n")


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  Cullinan Framework - Core Dependency Injection Example              ║
    ║                                                                      ║
    ║  This example demonstrates:                                          ║
    ║  • Type-based dependency injection (Spring style)                    ║
    ║  • Service -> Service dependency chains                              ║
    ║  • Controller -> Service injection                                   ║
    ║  • Optional dependencies                                             ║
    ║  • Scan-order independence                                           ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Test without running the web server
    test_injection_system()

    print("\nTo run as a web server, uncomment the following lines:")
    print("    app = Application()")
    print("    app.run()")

