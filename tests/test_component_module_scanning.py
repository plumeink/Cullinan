# -*- coding: utf-8 -*-
"""Diagnostic test for @component decorator in module scanning scenario.

This test simulates the full application startup to diagnose why
@component decorated classes might not be registered.
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_component_module_scanning():
    """Test that @component modules are scanned and imported correctly."""
    # Create a temporary package structure
    temp_dir = tempfile.mkdtemp(prefix='cullinan_test_')
    pkg_dir = os.path.join(temp_dir, 'test_app')

    try:
        # Create package structure
        os.makedirs(pkg_dir)

        # Create __init__.py
        with open(os.path.join(pkg_dir, '__init__.py'), 'w') as f:
            f.write('# Test app package\n')

        # Create service module
        with open(os.path.join(pkg_dir, 'services.py'), 'w') as f:
            f.write('''
from cullinan.service import service, Service

@service
class UserService(Service):
    def get_user(self, id):
        return {"id": id}
''')

        # Create component module
        with open(os.path.join(pkg_dir, 'components.py'), 'w') as f:
            f.write('''
from cullinan.core.decorators import component
from cullinan.core.lifecycle_enhanced import SmartLifecycle

@component
class CacheManager(SmartLifecycle):
    def __init__(self):
        self._cache = {}
    
    def get(self, key):
        return self._cache.get(key)
    
    def set(self, key, value):
        self._cache[key] = value
''')

        # Create controller module
        with open(os.path.join(pkg_dir, 'controllers.py'), 'w') as f:
            f.write('''
from cullinan.core.decorators import controller

@controller(url='/api')
class ApiController:
    pass
''')

        # Add temp_dir to sys.path so we can import the package
        sys.path.insert(0, temp_dir)

        # Reset PendingRegistry
        from cullinan.core.pending import PendingRegistry
        PendingRegistry.reset()

        # Import all modules (simulating what scan_service and scan_controller do)
        print("\n=== Importing modules ===")

        import importlib

        # Import service module
        services_mod = importlib.import_module('test_app.services')
        print(f"Imported: test_app.services")

        # Import component module
        components_mod = importlib.import_module('test_app.components')
        print(f"Imported: test_app.components")

        # Import controller module
        controllers_mod = importlib.import_module('test_app.controllers')
        print(f"Imported: test_app.controllers")

        # Check PendingRegistry
        pending = PendingRegistry.get_instance()
        all_regs = pending.get_all()

        print(f"\n=== PendingRegistry contents ===")
        print(f"Total registrations: {len(all_regs)}")
        for reg in all_regs:
            print(f"  - {reg.name}: type={reg.component_type.value}, scope={reg.scope}")

        # Verify all types are registered
        from cullinan.core.pending import ComponentType
        services = pending.get_by_type(ComponentType.SERVICE)
        controllers = pending.get_by_type(ComponentType.CONTROLLER)
        components = pending.get_by_type(ComponentType.COMPONENT)

        print(f"\n=== By type ===")
        print(f"  Services: {len(services)} - {[s.name for s in services]}")
        print(f"  Controllers: {len(controllers)} - {[c.name for c in controllers]}")
        print(f"  Components: {len(components)} - {[c.name for c in components]}")

        assert len(services) >= 1, f"Expected at least 1 service, got {len(services)}"
        assert len(controllers) >= 1, f"Expected at least 1 controller, got {len(controllers)}"
        assert len(components) >= 1, f"Expected at least 1 component, got {len(components)}"

        # Now test ApplicationContext
        from cullinan.core import ApplicationContext, set_application_context

        ctx = ApplicationContext()
        set_application_context(ctx)
        ctx.refresh()

        definitions = ctx.list_definitions()
        print(f"\n=== ApplicationContext definitions ===")
        print(f"Definitions: {definitions}")

        assert 'UserService' in definitions
        assert 'CacheManager' in definitions
        assert 'ApiController' in definitions

        # Get instances
        user_service = ctx.get('UserService')
        cache_manager = ctx.get('CacheManager')
        api_controller = ctx.get('ApiController')

        assert user_service is not None
        assert cache_manager is not None
        assert api_controller is not None

        # Test cache manager
        cache_manager.set('test', 'value')
        assert cache_manager.get('test') == 'value'

        ctx.shutdown()

        print("\n✅ test_component_module_scanning passed!")

    finally:
        # Cleanup
        sys.path.remove(temp_dir)

        # Remove from sys.modules
        mods_to_remove = [m for m in sys.modules if m.startswith('test_app')]
        for m in mods_to_remove:
            del sys.modules[m]

        # Remove temp directory
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Diagnostic: @component in module scanning scenario")
    print("=" * 60)

    test_component_module_scanning()

    print("\n" + "=" * 60)
    print("Test passed!")
    print("=" * 60 + "\n")
