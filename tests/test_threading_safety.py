# -*- coding: utf-8 -*-
"""测试修复 #02: 注册表线程安全（加锁）

验证多线程环境下注册表操作的安全性。
"""

import threading
import time
import sys
import os

project_path = r'G:\pj\Cullinan'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from cullinan.core.registry import SimpleRegistry
from cullinan.core import get_injection_registry, reset_injection_registry, Inject, injectable


def test_concurrent_registry_operations():
    """测试并发注册表操作"""
    print("测试: 并发注册表操作...")

    registry = SimpleRegistry()
    errors = []
    success_count = [0]  # 使用列表以便在内部函数中修改

    def register_items(thread_id, count):
        """每个线程注册指定数量的项"""
        try:
            for i in range(count):
                name = f"item_{thread_id}_{i}"
                registry.register(name, f"value_{thread_id}_{i}")
                success_count[0] += 1
        except Exception as e:
            errors.append((thread_id, str(e)))

    # 创建 10 个线程，每个注册 100 个项
    threads = []
    num_threads = 10
    items_per_thread = 100

    for i in range(num_threads):
        t = threading.Thread(target=register_items, args=(i, items_per_thread))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    # 验证
    expected_count = num_threads * items_per_thread
    actual_count = registry.count()

    print(f"  预期注册数: {expected_count}")
    print(f"  实际注册数: {actual_count}")
    print(f"  成功操作数: {success_count[0]}")
    print(f"  错误数: {len(errors)}")

    if errors:
        print("  错误列表:")
        for thread_id, error in errors[:5]:  # 只显示前5个错误
            print(f"    线程 {thread_id}: {error}")

    if actual_count == expected_count and len(errors) == 0:
        print("[OK] 测试通过: 并发注册操作安全")
        return True
    else:
        print("[FAIL] 测试失败: 注册数量不匹配或有错误")
        return False


def test_concurrent_read_write():
    """测试并发读写操作"""
    print("\n测试: 并发读写操作...")

    registry = SimpleRegistry()

    # 预先注册一些项
    for i in range(100):
        registry.register(f"item_{i}", f"value_{i}")

    errors = []
    read_count = [0]
    write_count = [0]

    def reader(thread_id):
        """读取线程"""
        try:
            for i in range(500):
                name = f"item_{i % 100}"
                value = registry.get(name)
                if value:
                    read_count[0] += 1
        except Exception as e:
            errors.append((f"reader_{thread_id}", str(e)))

    def writer(thread_id):
        """写入线程"""
        try:
            for i in range(50):
                name = f"new_item_{thread_id}_{i}"
                registry.register(name, f"new_value_{thread_id}_{i}")
                write_count[0] += 1
        except Exception as e:
            errors.append((f"writer_{thread_id}", str(e)))

    # 创建读写线程
    threads = []

    # 5个读线程
    for i in range(5):
        t = threading.Thread(target=reader, args=(i,))
        threads.append(t)

    # 5个写线程
    for i in range(5):
        t = threading.Thread(target=writer, args=(i,))
        threads.append(t)

    # 启动所有线程
    for t in threads:
        t.start()

    # 等待完成
    for t in threads:
        t.join()

    print(f"  读取操作数: {read_count[0]}")
    print(f"  写入操作数: {write_count[0]}")
    print(f"  错误数: {len(errors)}")

    if len(errors) == 0:
        print("[OK] 测试通过: 并发读写操作安全")
        return True
    else:
        print("[FAIL] 测试失败: 有错误发生")
        for name, error in errors[:5]:
            print(f"    {name}: {error}")
        return False


def test_concurrent_clear():
    """测试并发清空操作"""
    print("\n测试: 并发清空操作...")

    registry = SimpleRegistry()
    errors = []

    def register_and_clear(thread_id):
        """注册后清空"""
        try:
            for i in range(10):
                # 注册一些项
                for j in range(10):
                    registry.register(f"item_{thread_id}_{i}_{j}", f"value_{thread_id}_{i}_{j}")

                # 清空
                registry.clear()
        except Exception as e:
            errors.append((thread_id, str(e)))

    threads = []
    for i in range(5):
        t = threading.Thread(target=register_and_clear, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"  最终注册表大小: {registry.count()}")
    print(f"  错误数: {len(errors)}")

    if len(errors) == 0:
        print("[OK] 测试通过: 并发清空操作安全")
        return True
    else:
        print("[FAIL] 测试失败")
        return False


def test_concurrent_injection():
    """测试并发注入操作"""
    print("\n测试: 并发注入操作...")

    reset_injection_registry()
    injection_registry = get_injection_registry()

    # 创建服务注册表
    service_registry = SimpleRegistry()

    class TestService:
        def __init__(self, name):
            self.name = name

    # 注册多个服务
    for i in range(10):
        service_registry.register(f'TestService{i}', TestService(f'service_{i}'))

    injection_registry.add_provider_registry(service_registry)

    errors = []
    instances = []

    def create_and_inject(thread_id):
        """创建并注入实例"""
        try:
            # 动态创建类
            class_name = f'TestClass{thread_id}'

            @injectable
            class TestClass:
                service: TestService = Inject(name=f'TestService{thread_id % 10}')

            TestClass.__name__ = class_name

            # 创建实例
            instance = TestClass()
            instances.append((thread_id, instance))

        except Exception as e:
            errors.append((thread_id, str(e)))

    threads = []
    for i in range(20):
        t = threading.Thread(target=create_and_inject, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print(f"  成功创建实例数: {len(instances)}")
    print(f"  错误数: {len(errors)}")

    if len(errors) == 0 and len(instances) == 20:
        print("[OK] 测试通过: 并发注入操作安全")
        return True
    else:
        print("[FAIL] 测试失败")
        if errors:
            for tid, err in errors[:3]:
                print(f"    线程 {tid}: {err}")
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("验证修复 #02: 注册表线程安全（加锁）")
    print("=" * 70)

    results = []
    results.append(test_concurrent_registry_operations())
    results.append(test_concurrent_read_write())
    results.append(test_concurrent_clear())
    results.append(test_concurrent_injection())

    print("\n" + "=" * 70)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 70)

    if all(results):
        print("\n[OK] 所有测试通过！修复 #02 验证成功。")
        sys.exit(0)
    else:
        print("\n[FAIL] 部分测试失败，需要修复。")
        sys.exit(1)

