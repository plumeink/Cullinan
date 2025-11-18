"""
Run minimal Cullinan core examples for documentation smoke tests.
Example 1: ProviderRegistry + SingletonScope + ScopedProvider + InjectionRegistry + @injectable property injection
Example 2: Constructor injection with @inject_constructor

Run from repo root: python docs\work\core_examples.py (ensure you have a Python environment with required dependencies installed)
"""
from cullinan.core import (
    SingletonScope, ScopedProvider, ProviderRegistry,
    inject_constructor, injectable, Inject,
    get_injection_registry, reset_injection_registry
)

class Database:
    _instance_count = 0
    def __init__(self):
        Database._instance_count += 1
        self.id = Database._instance_count


def example_property_injection():
    print('\n[Example] Property injection with SingletonScope')
    reset_injection_registry()
    injection_registry = get_injection_registry()
    provider_registry = ProviderRegistry()
    singleton_scope = SingletonScope()

    # register singleton Database provider
    provider_registry.register_provider(
        'Database',
        ScopedProvider(lambda: Database(), singleton_scope, 'Database')
    )
    injection_registry.add_provider_registry(provider_registry)

    @injectable
    class ServiceA:
        database: Database = Inject()

    @injectable
    class ServiceB:
        database: Database = Inject()

    a = ServiceA()
    b = ServiceB()
    print('ServiceA.database.id =', a.database.id)
    print('ServiceB.database.id =', b.database.id)
    print('Same instance?', a.database is b.database)


def example_constructor_injection():
    print('\n[Example] Constructor injection with SingletonScope')
    reset_injection_registry()
    injection_registry = get_injection_registry()
    provider_registry = ProviderRegistry()
    singleton_scope = SingletonScope()

    Database._instance_count = 0
    provider_registry.register_provider(
        'Database',
        ScopedProvider(lambda: Database(), singleton_scope, 'Database')
    )
    injection_registry.add_provider_registry(provider_registry)

    @inject_constructor
    class Controller:
        def __init__(self, database: Database):
            self.database = database

    c1 = Controller()
    c2 = Controller()
    print('Controller1.database.id =', c1.database.id)
    print('Controller2.database.id =', c2.database.id)
    print('Same instance?', c1.database is c2.database)


if __name__ == '__main__':
    try:
        example_property_injection()
        example_constructor_injection()
        print('\nAll core examples ran successfully')
    except Exception as e:
        print('\nCore examples failed:', e)
        raise
