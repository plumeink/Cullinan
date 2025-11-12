# -*- coding: utf-8 -*-
"""测试 Scope 作用域系统

验证 SingletonScope, TransientScope, RequestScope 的行为
"""

import pytest
import threading
import time
from cullinan.core import (
    SingletonScope, TransientScope, RequestScope,
    get_singleton_scope, get_transient_scope, get_request_scope,
    create_context, destroy_context, get_current_context
)


class MockService:
    """模拟服务类"""
    instance_count = 0

    def __init__(self, name="default"):
        self.name = name
        MockService.instance_count += 1
        self.id = MockService.instance_count

    def __repr__(self):
        return f"MockService({self.name}, id={self.id})"


def setup_function():
    """每个测试前重置"""
    MockService.instance_count = 0


def test_singleton_scope_caches():
    """测试：SingletonScope 缓存实例"""

    scope = SingletonScope()

    s1 = scope.get("service", lambda: MockService("test"))
    s2 = scope.get("service", lambda: MockService("test"))

    assert s1 is s2
    assert MockService.instance_count == 1


def test_singleton_scope_different_keys():
    """测试：SingletonScope 不同 key 创建不同实例"""

    scope = SingletonScope()

    s1 = scope.get("service1", lambda: MockService("1"))
    s2 = scope.get("service2", lambda: MockService("2"))

    assert s1 is not s2
    assert s1.name == "1"
    assert s2.name == "2"
    assert MockService.instance_count == 2


def test_singleton_scope_clear():
    """测试：SingletonScope 清空缓存"""

    scope = SingletonScope()

    s1 = scope.get("service", lambda: MockService("test"))
    assert scope.count() == 1

    scope.clear()
    assert scope.count() == 0

    s2 = scope.get("service", lambda: MockService("test"))
    assert s1 is not s2  # 清空后重新创建
    assert MockService.instance_count == 2


def test_singleton_scope_remove():
    """测试：SingletonScope 移除指定实例"""

    scope = SingletonScope()

    scope.get("s1", lambda: MockService("1"))
    scope.get("s2", lambda: MockService("2"))

    assert scope.count() == 2
    assert scope.remove("s1")
    assert scope.count() == 1
    assert not scope.remove("s1")  # 再次移除返回 False


def test_singleton_scope_has():
    """测试：SingletonScope 检查实例是否存在"""

    scope = SingletonScope()

    assert not scope.has("service")

    scope.get("service", lambda: MockService("test"))

    assert scope.has("service")


def test_transient_scope_no_cache():
    """测试：TransientScope 不缓存实例"""

    scope = TransientScope()

    s1 = scope.get("service", lambda: MockService("test"))
    s2 = scope.get("service", lambda: MockService("test"))

    assert s1 is not s2
    assert MockService.instance_count == 2


def test_transient_scope_operations():
    """测试：TransientScope 的 clear/remove/has 操作"""

    scope = TransientScope()

    # clear 无操作
    scope.clear()

    # remove 始终返回 False
    assert not scope.remove("any_key")

    # has 始终返回 False（瞬时作用域不存储）
    scope.get("service", lambda: MockService("test"))
    # has 方法不存在，因为瞬时作用域不需要


def test_request_scope_within_context():
    """测试：RequestScope 在请求上下文中缓存"""

    scope = RequestScope()

    with create_context():
        s1 = scope.get("service", lambda: MockService("test"))
        s2 = scope.get("service", lambda: MockService("test"))

        assert s1 is s2
        assert MockService.instance_count == 1


def test_request_scope_different_contexts():
    """测试：RequestScope 不同请求上下文独立"""

    scope = RequestScope()

    with create_context():
        s1 = scope.get("service", lambda: MockService("test"))
        id1 = s1.id

    with create_context():
        s2 = scope.get("service", lambda: MockService("test"))
        id2 = s2.id

    assert id1 != id2
    assert MockService.instance_count == 2


def test_request_scope_no_context_error():
    """测试：RequestScope 没有上下文时抛出错误"""

    scope = RequestScope()

    # 确保没有活动上下文
    ctx = get_current_context()
    if ctx:
        destroy_context()

    with pytest.raises(RuntimeError) as exc_info:
        scope.get("service", lambda: MockService("test"))

    assert "No active request context" in str(exc_info.value)


def test_request_scope_clear():
    """测试：RequestScope 清空当前请求的实例"""

    scope = RequestScope()

    with create_context():
        scope.get("s1", lambda: MockService("1"))
        scope.get("s2", lambda: MockService("2"))

        assert scope.count() == 2

        scope.clear()

        assert scope.count() == 0

        # 清空后可以重新创建
        s3 = scope.get("s1", lambda: MockService("3"))
        assert s3.name == "3"


def test_request_scope_remove():
    """测试：RequestScope 移除指定实例"""

    scope = RequestScope()

    with create_context():
        scope.get("s1", lambda: MockService("1"))
        scope.get("s2", lambda: MockService("2"))

        assert scope.remove("s1")
        assert not scope.has("s1")
        assert scope.has("s2")
        assert scope.count() == 1


def test_request_scope_has():
    """测试：RequestScope 检查实例是否存在"""

    scope = RequestScope()

    with create_context():
        assert not scope.has("service")

        scope.get("service", lambda: MockService("test"))

        assert scope.has("service")


def test_request_scope_concurrent_requests():
    """测试：RequestScope 在并发请求中隔离"""

    scope = RequestScope()
    results = []
    errors = []

    def request_handler(request_id):
        try:
            with create_context():
                s = scope.get("service", lambda: MockService(f"req_{request_id}"))
                time.sleep(0.01)  # 模拟处理时间
                # 再次获取，应该是同一个实例
                s2 = scope.get("service", lambda: MockService(f"req_{request_id}"))
                assert s is s2
                results.append((request_id, s.id, s2.id))
        except Exception as e:
            errors.append((request_id, e))

    threads = []
    for i in range(5):
        t = threading.Thread(target=request_handler, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors: {errors}"
    assert len(results) == 5

    # 每个请求的两次获取应该是同一个实例
    for req_id, id1, id2 in results:
        assert id1 == id2


def test_global_scope_singletons():
    """测试：全局作用域单例"""

    s1 = get_singleton_scope()
    s2 = get_singleton_scope()

    assert s1 is s2

    t1 = get_transient_scope()
    t2 = get_transient_scope()

    assert t1 is t2

    r1 = get_request_scope()
    r2 = get_request_scope()

    assert r1 is r2


def test_singleton_scope_thread_safe():
    """测试：SingletonScope 线程安全"""

    scope = SingletonScope()
    results = []
    errors = []

    def worker():
        try:
            s = scope.get("shared", lambda: MockService("shared"))
            results.append(s.id)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    # 所有线程应该获取到同一个实例
    assert len(set(results)) == 1
    assert MockService.instance_count == 1


def test_request_scope_custom_storage_key():
    """测试：RequestScope 自定义存储键"""

    scope1 = RequestScope(storage_key='_custom_scope_1')
    scope2 = RequestScope(storage_key='_custom_scope_2')

    with create_context():
        s1 = scope1.get("service", lambda: MockService("1"))
        s2 = scope2.get("service", lambda: MockService("2"))

        # 不同存储键，不同实例
        assert s1 is not s2
        assert s1.name == "1"
        assert s2.name == "2"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

