# -*- coding: utf-8 -*-
"""Tests for ASGI WebSocket support."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.adapter.asgi_adapter import _handle_websocket
from cullinan.websocket_registry import get_websocket_registry, reset_websocket_registry, websocket_handler

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")


async def main():
    print("=" * 60)
    print("ASGI WebSocket Tests")
    print("=" * 60)

    # Clean slate
    reset_websocket_registry()

    # Register a test WS handler
    message_log = []
    open_called = [False]
    close_called = [False]

    @websocket_handler(url='/ws/echo')
    class EchoHandler:
        def on_open(self):
            open_called[0] = True

        def on_message(self, message):
            message_log.append(message)
            # Echo back
            asyncio.ensure_future(self.write_message(f"echo:{message}"))

        def on_close(self):
            close_called[0] = True

    @websocket_handler(url='/ws/async')
    class AsyncHandler:
        async def on_open(self):
            open_called[0] = True

        async def on_message(self, message):
            message_log.append(f"async:{message}")
            await self.write_message(f"async-echo:{message}")

        async def on_close(self):
            close_called[0] = True

    # ====================================================================
    # 1. Basic WebSocket connect, message, disconnect
    # ====================================================================
    print("\n--- 1. Basic WS lifecycle ---")

    sent_messages = []
    message_queue = asyncio.Queue()

    async def mock_receive():
        return await message_queue.get()

    async def mock_send(msg):
        sent_messages.append(msg)

    scope = {
        'type': 'websocket',
        'path': '/ws/echo',
        'headers': [(b'host', b'localhost:8000')],
        'query_string': b'',
    }

    # Simulate: connect → send message → disconnect
    await message_queue.put({'type': 'websocket.connect'})
    await message_queue.put({'type': 'websocket.receive', 'text': 'hello'})
    await message_queue.put({'type': 'websocket.disconnect'})

    open_called[0] = False
    close_called[0] = False
    message_log.clear()
    sent_messages.clear()

    await _handle_websocket(scope, mock_receive, mock_send)

    check("on_open called", open_called[0] is True)
    check("on_message received", 'hello' in message_log)
    check("on_close called", close_called[0] is True)
    check("websocket.accept sent", any(m.get('type') == 'websocket.accept' for m in sent_messages))

    # Allow echo future to complete
    await asyncio.sleep(0.05)
    echo_sent = [m for m in sent_messages if m.get('type') == 'websocket.send']
    check("Echo response sent", len(echo_sent) >= 1)
    if echo_sent:
        check("Echo content", echo_sent[0].get('text') == 'echo:hello')

    # ====================================================================
    # 2. Async handler
    # ====================================================================
    print("\n--- 2. Async handler ---")

    sent_messages2 = []
    queue2 = asyncio.Queue()

    async def recv2():
        return await queue2.get()

    async def send2(msg):
        sent_messages2.append(msg)

    scope2 = {'type': 'websocket', 'path': '/ws/async', 'headers': [], 'query_string': b''}

    await queue2.put({'type': 'websocket.connect'})
    await queue2.put({'type': 'websocket.receive', 'text': 'test'})
    await queue2.put({'type': 'websocket.disconnect'})

    open_called[0] = False
    close_called[0] = False
    message_log.clear()

    await _handle_websocket(scope2, recv2, send2)

    check("Async on_open called", open_called[0] is True)
    check("Async on_message received", 'async:test' in message_log)
    check("Async on_close called", close_called[0] is True)
    check("Async accept sent", any(m.get('type') == 'websocket.accept' for m in sent_messages2))
    async_echo = [m for m in sent_messages2 if m.get('type') == 'websocket.send']
    check("Async echo sent", len(async_echo) >= 1)
    if async_echo:
        check("Async echo content", async_echo[0].get('text') == 'async-echo:test')

    # ====================================================================
    # 3. No handler registered → close with 4004
    # ====================================================================
    print("\n--- 3. No handler (4004) ---")

    sent_messages3 = []
    queue3 = asyncio.Queue()

    async def recv3():
        return await queue3.get()

    async def send3(msg):
        sent_messages3.append(msg)

    scope3 = {'type': 'websocket', 'path': '/ws/nonexistent', 'headers': [], 'query_string': b''}
    await queue3.put({'type': 'websocket.connect'})

    await _handle_websocket(scope3, recv3, send3)

    close_msgs = [m for m in sent_messages3 if m.get('type') == 'websocket.close']
    check("Close sent for unknown path", len(close_msgs) >= 1)
    if close_msgs:
        check("Close code 4004", close_msgs[0].get('code') == 4004)

    # ====================================================================
    # 4. Binary message support
    # ====================================================================
    print("\n--- 4. Binary messages ---")

    sent_messages4 = []
    queue4 = asyncio.Queue()

    async def recv4():
        return await queue4.get()

    async def send4(msg):
        sent_messages4.append(msg)

    scope4 = {'type': 'websocket', 'path': '/ws/echo', 'headers': [], 'query_string': b''}
    await queue4.put({'type': 'websocket.connect'})
    await queue4.put({'type': 'websocket.receive', 'bytes': b'\x00\x01\x02'})
    await queue4.put({'type': 'websocket.disconnect'})
    message_log.clear()

    await _handle_websocket(scope4, recv4, send4)

    check("Binary message received", b'\x00\x01\x02' in message_log)

    # ====================================================================
    # 5. Multiple messages
    # ====================================================================
    print("\n--- 5. Multiple messages ---")

    sent_messages5 = []
    queue5 = asyncio.Queue()

    async def recv5():
        return await queue5.get()

    async def send5(msg):
        sent_messages5.append(msg)

    scope5 = {'type': 'websocket', 'path': '/ws/echo', 'headers': [], 'query_string': b''}
    await queue5.put({'type': 'websocket.connect'})
    await queue5.put({'type': 'websocket.receive', 'text': 'msg1'})
    await queue5.put({'type': 'websocket.receive', 'text': 'msg2'})
    await queue5.put({'type': 'websocket.receive', 'text': 'msg3'})
    await queue5.put({'type': 'websocket.disconnect'})
    message_log.clear()

    await _handle_websocket(scope5, recv5, send5)

    check("Multiple messages count", len(message_log) == 3)
    check("Multiple messages order", message_log == ['msg1', 'msg2', 'msg3'])

    # ====================================================================
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")
    return failed == 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

