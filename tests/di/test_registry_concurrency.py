# -*- coding: utf-8 -*-
"""测试 Registry 的并发安全性

验证多线程环境下的 register/unregister/clear/freeze 操作
"""

import threading
import time
import pytest
from cullinan.core.registry import SimpleRegistry


def test_concurrent_register():
    """测试：并发注册不会导致数据丢失或异常"""

    registry = SimpleRegistry()
    results = []
    errors = []

    def register_items(thread_id, count):
        try:
            for i in range(count):
                name = f"item_{thread_id}_{i}"
                registry.register(name, f"value_{thread_id}_{i}")
            results.append(thread_id)
        except Exception as e:
            errors.append((thread_id, e))

    threads = []
    thread_count = 10
    items_per_thread = 100

    for i in range(thread_count):
        t = threading.Thread(target=register_items, args=(i, items_per_thread))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == thread_count
    assert registry.count() == thread_count * items_per_thread


def test_concurrent_register_unregister():
    """测试：并发注册和删除操作"""

    registry = SimpleRegistry()
    errors = []

    for i in range(100):
        registry.register(f"item_{i}", f"value_{i}")

    def register_worker():
        try:
            for i in range(100, 150):
                registry.register(f"item_{i}", f"value_{i}")
        except Exception as e:
            errors.append(e)

    def unregister_worker():
        try:
            for i in range(50):
                registry.unregister(f"item_{i}")
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=register_worker)
    t2 = threading.Thread(target=unregister_worker)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(errors) == 0, f"Errors: {errors}"

    final_count = registry.count()
    assert 100 <= final_count <= 150


def test_concurrent_freeze_operations():
    """测试：freeze/unfreeze 的并发安全"""

    registry = SimpleRegistry()
    errors = []

    def freeze_worker():
        try:
            for _ in range(100):
                registry.freeze()
                time.sleep(0.001)
                registry.unfreeze()
        except Exception as e:
            errors.append(e)

    def register_worker():
        try:
            for i in range(100):
                try:
                    registry.register(f"item_{i}", f"value_{i}")
                except:
                    pass
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=freeze_worker)
    t2 = threading.Thread(target=register_worker)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(errors) == 0, f"Errors: {errors}"


def test_concurrent_clear():
    """测试：并发 clear 操作"""

    registry = SimpleRegistry()
    errors = []

    def register_clear_cycle():
        try:
            for cycle in range(10):
                for i in range(50):
                    registry.register(f"item_{threading.current_thread().ident}_{i}", f"value_{i}")
                registry.clear()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=register_clear_cycle) for _ in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors: {errors}"


def test_concurrent_metadata_operations():
    """测试：并发元数据操作"""

    registry = SimpleRegistry()
    errors = []

    for i in range(10):
        registry.register(f"item_{i}", f"value_{i}")

    def update_metadata():
        try:
            for i in range(10):
                registry.set_metadata(f"item_{i}", key1="val1", key2="val2")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=update_metadata) for _ in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors: {errors}"

    for i in range(10):
        meta = registry.get_metadata(f"item_{i}")
        assert meta is not None
        assert meta.get('key1') == 'val1'


def test_concurrent_hook_registration():
    """测试：并发 hook 注册"""

    registry = SimpleRegistry()
    errors = []
    hook_calls = []

    def hook_callback(name, item):
        hook_calls.append(name)

    def add_hooks():
        try:
            for _ in range(10):
                registry.add_hook('post_register', hook_callback)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=add_hooks) for _ in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors: {errors}"

    registry.register("test", "value")

    assert len(hook_calls) == 50


def test_concurrent_update():
    """测试：并发 update 操作"""

    registry = SimpleRegistry()
    errors = []

    registry.register("shared_item", "initial")

    def update_worker(value):
        try:
            for _ in range(100):
                registry.update("shared_item", value)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=update_worker, args=(f"value_{i}",)) for i in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors: {errors}"

    final_value = registry.get("shared_item")
    assert final_value is not None
    assert final_value.startswith("value_")


def test_lazyproxy_concurrent_resolve_single_call():
    """测试：_LazyProxy 并发 resolve 仅调用一次 resolver（Issue 1 修复验证）"""
    from cullinan.core.application_context import _LazyProxy

    call_count = [0]  # 用 list 实现跨线程可变计数器
    call_lock = threading.Lock()

    def resolver_with_side_effect():
        with call_lock:
            call_count[0] += 1
        return {"data": "resolved"}

    proxy = _LazyProxy(resolver_with_side_effect)
    errors = []
    barrier = threading.Barrier(20)  # 所有线程同时启动

    def access_proxy():
        try:
            barrier.wait()  # 最大化竞态窗口
            result = proxy._resolve()
            assert result == {"data": "resolved"}
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=access_proxy) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors: {errors}"
    assert call_count[0] == 1, f"Resolver called {call_count[0]} times, expected 1"


def test_lazyproxy_resolve_returns_same_value():
    """测试：_LazyProxy 多次 resolve 返回同一实例"""
    from cullinan.core.application_context import _LazyProxy
    import random

    obj = object()
    proxy = _LazyProxy(lambda: obj)
    assert proxy._resolve() is obj
    assert proxy._resolve() is obj  # 第二次应返回缓存值

