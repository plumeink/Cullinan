# -*- coding: utf-8 -*-
"""Integration test for complete application flow"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.core import Inject
from cullinan.service import service, Service
from cullinan.controller import controller, get_api


# Define services
@service
class DatabaseService(Service):
    def query(self, sql):
        return f"Query: {sql}"


@service
class UserService(Service):
    db: DatabaseService = Inject()

    def get_user(self, user_id):
        result = self.db.query(f"SELECT * FROM users WHERE id={user_id}")
        return {"id": user_id, "result": result}


# Define controller
@controller(url='/api/users')
class UserController:
    user_service: UserService = Inject()

    @get_api(url='')
    def list_users(self, query_params):
        return {"users": ["user1", "user2"]}

    @get_api(url='/(?P<id>[0-9]+)')
    def get_user(self, url_params):
        user_id = int(url_params['id'])
        user = self.user_service.get_user(user_id)
        return {"user": user}


def test_complete_flow():
    """Test the complete application flow"""
    from cullinan.service import get_service_registry
    from cullinan.controller import get_controller_registry
    from cullinan.handler import get_handler_registry
    from cullinan.core import get_injection_registry

    print("\n=== Complete Flow Integration Test ===\n")

    # Configure injection (simulating what application.py does)
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()
    injection_registry.add_provider_registry(service_registry, priority=100)
    print("[OK] Dependency injection configured")

    # Check service registration
    print(f"\n[Services]")
    print(f"  DatabaseService registered: {service_registry.has('DatabaseService')}")
    print(f"  UserService registered: {service_registry.has('UserService')}")

    # Check controller registration
    controller_registry = get_controller_registry()
    print(f"\n[Controllers]")
    print(f"  UserController registered: {controller_registry.has('UserController')}")
    print(f"  UserController methods: {controller_registry.get_method_count('UserController')}")

    # Check handler registration
    handler_registry = get_handler_registry()
    print(f"\n[Handlers]")
    print(f"  Handler count: {handler_registry.count()}")
    handlers = handler_registry.get_handlers()
    for url, servlet in handlers:
        print(f"    {url}")

    # Test dependency injection
    print(f"\n[Dependency Injection Test]")
    user_service = service_registry.get_instance('UserService')
    print(f"  UserService instance: {user_service}")
    print(f"  UserService.db: {user_service.db}")
    print(f"  UserService.db type: {type(user_service.db).__name__}")

    # Test functionality
    print(f"\n[Functionality Test]")
    user = user_service.get_user(123)
    print(f"  user_service.get_user(123): {user}")

    # Test controller instantiation
    print(f"\n[Controller Instantiation Test]")
    controller = UserController()
    print(f"  UserController instance: {controller}")
    print(f"  UserController.user_service: {controller.user_service}")
    print(f"  UserController.user_service type: {type(controller.user_service).__name__}")

    # Verify all
    success = True
    if not service_registry.has('DatabaseService'):
        print("\nERROR: DatabaseService not registered")
        success = False
    if not service_registry.has('UserService'):
        print("\nERROR: UserService not registered")
        success = False
    if not controller_registry.has('UserController'):
        print("\nERROR: UserController not registered")
        success = False
    if controller_registry.get_method_count('UserController') < 2:
        print("\nERROR: UserController methods not registered")
        success = False
    if handler_registry.count() < 2:
        print("\nERROR: Handlers not registered")
        success = False
    if not isinstance(user_service.db, DatabaseService):
        print("\nERROR: UserService.db not properly injected")
        success = False
    if not isinstance(controller.user_service, UserService):
        print("\nERROR: UserController.user_service not properly injected")
        success = False

    if success:
        print("\n" + "="*50)
        print("SUCCESS: All checks passed!")
        print("="*50)

    return success


if __name__ == '__main__':
    try:
        success = test_complete_flow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

