# -*- coding: utf-8 -*-
"""Minimal demonstration of the async fix.

Author: Plumeink
"""
import inspect


async def example_async_function():
    """Example async function."""
    return {"result": "async"}


def test_original_vs_fixed():
    """Demonstrate the difference between iscoroutine and isawaitable."""
    
    print("=" * 70)
    print("Async Detection: iscoroutine() vs isawaitable()")
    print("=" * 70)
    
    # Call the async function (returns a coroutine object)
    coro = example_async_function()
    
    print(f"\nResult of calling example_async_function():")
    print(f"  Type: {type(coro)}")
    print(f"  inspect.iscoroutine(): {inspect.iscoroutine(coro)}")
    print(f"  inspect.isawaitable(): {inspect.isawaitable(coro)}")
    
    print(f"\n✓ Both return True for native coroutines")
    
    # Clean up
    coro.close()
    
    # Test with a custom awaitable
    class CustomAwaitable:
        def __await__(self):
            return iter([42])
    
    custom = CustomAwaitable()
    
    print(f"\nCustom awaitable object:")
    print(f"  Type: {type(custom)}")
    print(f"  inspect.iscoroutine(): {inspect.iscoroutine(custom)}")
    print(f"  inspect.isawaitable(): {inspect.isawaitable(custom)}")
    
    print(f"\n✓ isawaitable() catches custom awaitables!")
    
    # Test with regular object
    regular = {"not": "awaitable"}
    
    print(f"\nRegular dict object:")
    print(f"  Type: {type(regular)}")
    print(f"  inspect.iscoroutine(): {inspect.iscoroutine(regular)}")
    print(f"  inspect.isawaitable(): {inspect.isawaitable(regular)}")
    
    print(f"\n✓ Both return False for non-awaitable objects")
    
    print("\n" + "=" * 70)
    print("CONCLUSION:")
    print("  - inspect.isawaitable() is MORE COMPREHENSIVE")
    print("  - It catches all awaitable types, not just native coroutines")
    print("  - Using isawaitable() makes the framework more robust")
    print("=" * 70)


if __name__ == "__main__":
    test_original_vs_fixed()

