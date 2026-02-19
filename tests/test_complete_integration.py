# -*- coding: utf-8 -*-
"""Integration test for complete application flow

Updated to use ApplicationContext (IoC 2.0 unified lifecycle).
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.core import Inject, ApplicationContext, set_application_context
from cullinan.core.pending import PendingRegistry
from cullinan.service import service, Service
from cullinan.controller import controller, get_api


def test_complete_flow():
    """Test the complete application flow using ApplicationContext"""
    from cullinan.controller import get_controller_registry
    from cullinan.handler import get_handler_registry

    print("\n=== Complete Flow Integration Test ===\n")

    # Reset state at the beginning of each test
    PendingRegistry.reset()

    # Define services inside test function to avoid cross-test pollution
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

    # Create and configure ApplicationContext (unified IoC container)
    ctx = ApplicationContext()
    set_application_context(ctx)
    ctx.refresh()

    print("[OK] ApplicationContext initialized with unified lifecycle")

    # Check service registration via ApplicationContext
    print(f"\n[Services via ApplicationContext]")
    definitions = ctx.list_definitions()
    db_service_registered = 'DatabaseService' in definitions
    user_service_registered = 'UserService' in definitions
    print(f"  DatabaseService registered: {db_service_registered}")
    print(f"  UserService registered: {user_service_registered}")

    # Check controller registration
    controller_registry = get_controller_registry()
    print(f"\n[Controllers]")
    controller_registered = 'UserController' in definitions
    print(f"  UserController registered in ApplicationContext: {controller_registered}")
    print(f"  UserController in controller_registry: {controller_registry.has('UserController')}")
    method_count = controller_registry.get_method_count('UserController')
    print(f"  UserController methods: {method_count}")

    # Check handler registration
    handler_registry = get_handler_registry()
    print(f"\n[Handlers]")
    print(f"  Handler count: {handler_registry.count()}")
    handlers = handler_registry.get_handlers()
    for url, servlet in handlers:
        print(f"    {url}")

    # Test dependency injection via ApplicationContext
    print(f"\n[Dependency Injection Test via ApplicationContext]")
    user_service = ctx.get('UserService')
    print(f"  UserService instance: {user_service}")
    print(f"  UserService.db: {user_service.db}")
    print(f"  UserService.db type: {type(user_service.db).__name__}")

    # Test functionality
    print(f"\n[Functionality Test]")
    user = user_service.get_user(123)
    print(f"  user_service.get_user(123): {user}")

    # Test controller instantiation via ApplicationContext
    print(f"\n[Controller Instantiation Test]")
    user_controller = ctx.get('UserController')
    print(f"  UserController instance: {user_controller}")
    print(f"  UserController.user_service: {user_controller.user_service}")
    print(f"  UserController.user_service type: {type(user_controller.user_service).__name__}")

    # Verify all
    success = True
    if not db_service_registered:
        print("\nERROR: DatabaseService not registered")
        success = False
    if not user_service_registered:
        print("\nERROR: UserService not registered")
        success = False
    if not controller_registered:
        print("\nERROR: UserController not registered")
        success = False
    if method_count < 2:
        print("\nERROR: UserController methods not registered")
        success = False
    if handler_registry.count() < 2:
        print("\nERROR: Handlers not registered")
        success = False
    if not isinstance(user_service.db, DatabaseService):
        print("\nERROR: UserService.db not properly injected")
        success = False
    if not isinstance(user_controller.user_service, UserService):
        print("\nERROR: UserController.user_service not properly injected")
        success = False

    if success:
        print("\n" + "="*50)
        print("SUCCESS: All checks passed!")
        print("="*50)

    # Cleanup
    ctx.shutdown()

    assert success, "Some checks failed"


if __name__ == '__main__':
    try:
        test_complete_flow()
        exit(0)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

