"""Test to understand the async detection issue."""
import inspect
import asyncio


async def original_async_func():
    """Original async function defined by user."""
    print("Original async function executed")
    return {"status": "ok"}


def test_detection():
    """Test different detection methods."""

    # Test 1: Direct async function
    print(f"Is coroutine function (original): {inspect.iscoroutinefunction(original_async_func)}")

    # Test 2: Calling it returns coroutine
    result = original_async_func()
    print(f"Is coroutine (result): {inspect.iscoroutine(result)}")
    print(f"Is awaitable (result): {inspect.isawaitable(result)}")

    # Clean up
    result.close()

    # Test 3: Wrapper that doesn't properly await
    def bad_wrapper(func):
        def wrapper():
            return func()  # Returns coroutine without awaiting
        return wrapper

    wrapped_bad = bad_wrapper(original_async_func)
    print(f"\nBad wrapper:")
    print(f"Is coroutine function (wrapped): {inspect.iscoroutinefunction(wrapped_bad)}")
    result = wrapped_bad()
    print(f"Is coroutine (result): {inspect.iscoroutine(result)}")
    print(f"Is awaitable (result): {inspect.isawaitable(result)}")
    result.close()

    # Test 4: Proper async wrapper
    def good_wrapper(func):
        async def wrapper():
            return await func()
        return wrapper

    wrapped_good = good_wrapper(original_async_func)
    print(f"\nGood wrapper:")
    print(f"Is coroutine function (wrapped): {inspect.iscoroutinefunction(wrapped_good)}")


if __name__ == "__main__":
    test_detection()

