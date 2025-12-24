# -*- coding: utf-8 -*-
"""Simple diagnostic to check async detection logic.

Author: Plumeink
"""
import inspect
import asyncio


async def test_async_func():
    """Test async function"""
    await asyncio.sleep(0.001)
    return {"executed": True}


def test_sync_func():
    """Test sync function"""
    return {"executed": True}


def test_detection_methods():
    """Test different detection methods"""
    
    print("=" * 60)
    print("Testing async function detection")
    print("=" * 60)
    
    # Test 1: Check function type
    print(f"\n1. Function type checks:")
    print(f"   test_async_func is coroutine function: {inspect.iscoroutinefunction(test_async_func)}")
    print(f"   test_sync_func is coroutine function: {inspect.iscoroutinefunction(test_sync_func)}")
    
    # Test 2: Check call result
    print(f"\n2. Call result checks:")
    async_result = test_async_func()
    sync_result = test_sync_func()
    
    print(f"   async_result is coroutine: {inspect.iscoroutine(async_result)}")
    print(f"   async_result is awaitable: {inspect.isawaitable(async_result)}")
    print(f"   sync_result is coroutine: {inspect.iscoroutine(sync_result)}")
    print(f"   sync_result is awaitable: {inspect.isawaitable(sync_result)}")
    
    # Clean up coroutine
    async_result.close()
    
    # Test 3: Wrapper scenarios
    print(f"\n3. Wrapper scenarios:")
    
    def bad_wrapper(func):
        """Sync wrapper that doesn't await"""
        def wrapper():
            return func()  # Returns coroutine without awaiting!
        return wrapper
    
    def good_async_wrapper(func):
        """Async wrapper that properly awaits"""
        async def wrapper():
            if inspect.isawaitable(func):
                return await func
            result = func()
            if inspect.isawaitable(result):
                return await result
            return result
        return wrapper
    
    wrapped_bad = bad_wrapper(test_async_func)
    wrapped_good = good_async_wrapper(test_async_func)
    
    print(f"   wrapped_bad is coroutine function: {inspect.iscoroutinefunction(wrapped_bad)}")
    bad_result = wrapped_bad()
    print(f"   wrapped_bad() returns coroutine: {inspect.iscoroutine(bad_result)}")
    print(f"   wrapped_bad() returns awaitable: {inspect.isawaitable(bad_result)}")
    bad_result.close()
    
    print(f"   wrapped_good is coroutine function: {inspect.iscoroutinefunction(wrapped_good)}")
    good_result = wrapped_good()
    print(f"   wrapped_good() returns coroutine: {inspect.iscoroutine(good_result)}")
    print(f"   wrapped_good() returns awaitable: {inspect.isawaitable(good_result)}")
    good_result.close()
    
    print(f"\n4. Key insight:")
    print(f"   - Use inspect.iscoroutinefunction() to check if a function is async")
    print(f"   - Use inspect.isawaitable() to check if result needs await")
    print(f"   - inspect.isawaitable() covers more cases than inspect.iscoroutine()")
    print("=" * 60)


if __name__ == "__main__":
    test_detection_methods()

