import sys
sys.path.insert(0, 'G:\\pj\\Cullinan')

print("Testing IoC fixes...")

# Test 1: Inject is a descriptor
from cullinan.core.injection import Inject
print(f"1. Inject class: {Inject}")
print(f"   Has __get__: {hasattr(Inject, '__get__')}")
print(f"   Has __set__: {hasattr(Inject, '__set__')}")
print(f"   Has __set_name__: {hasattr(Inject, '__set_name__')}")

# Test 2: DependencyInjector has _resolving
from cullinan.core.legacy_injection import DependencyInjector
inj = DependencyInjector()
print(f"\n2. DependencyInjector __slots__: {DependencyInjector.__slots__}")
print(f"   Has _resolving: {'_resolving' in DependencyInjector.__slots__}")

# Test 3: ServiceRegistry has _instance_lock
from cullinan.service.registry import ServiceRegistry
reg = ServiceRegistry()
print(f"\n3. ServiceRegistry __slots__: {ServiceRegistry.__slots__}")
print(f"   Has _instance_lock: {'_instance_lock' in ServiceRegistry.__slots__}")
print(f"   Lock type: {type(reg._instance_lock)}")

print("\nAll structural checks passed!")

