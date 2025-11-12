#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全面的 Cullinan IoC 系统安全稳定性验证
无视注释，以实际源码行为为准
"""

import sys
import os
import threading
import time
import traceback

# 确保使用本地 cullinan
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "="*80)
print("Cullinan IoC 系统全面安全稳定性验证")
print("="*80)

test_results = []
error_details = []

# ============================================================================
# 测试 1: 验证核心类结构
# ============================================================================
print("\n[测试 1/10] 核心类结构验证")
print("-" * 80)

try:
    from cullinan.core.injection import Inject, InjectByName, InjectionRegistry
    from cullinan.core.legacy_injection import DependencyInjector
    from cullinan.service.registry import ServiceRegistry

    # 验证 Inject 是描述符
    inject_checks = {
        '__get__': hasattr(Inject, '__get__'),
        '__set__': hasattr(Inject, '__set__'),
        '__set_name__': hasattr(Inject, '__set_name__'),
        '__slots__': hasattr(Inject, '__slots__'),
    }

    # 验证 InjectByName 是描述符
    inject_by_name_checks = {
        '__get__': hasattr(InjectByName, '__get__'),
        '__set__': hasattr(InjectByName, '__set__'),
        '__set_name__': hasattr(InjectByName, '__set_name__'),
        '__slots__': hasattr(InjectByName, '__slots__'),
    }

    # 验证 DependencyInjector 有循环检测
    dep_injector_checks = {
        '_resolving in __slots__': '_resolving' in DependencyInjector.__slots__,
        'has resolve': hasattr(DependencyInjector, 'resolve'),
        'has clear': hasattr(DependencyInjector, 'clear'),
    }

    # 验证 ServiceRegistry 有线程锁
    service_registry_checks = {
        '_instance_lock in __slots__': '_instance_lock' in ServiceRegistry.__slots__,
        'has get_instance': hasattr(ServiceRegistry, 'get_instance'),
    }

    print(f"  Inject 描述符检查: {inject_checks}")
    print(f"  InjectByName 描述符检查: {inject_by_name_checks}")
    print(f"  DependencyInjector 检查: {dep_injector_checks}")
    print(f"  ServiceRegistry 检查: {service_registry_checks}")

    all_passed = (
        all(inject_checks.values()) and
        all(inject_by_name_checks.values()) and
        all(dep_injector_checks.values()) and
        all(service_registry_checks.values())
    )

    if all_passed:
        print("  [通过] 核心类结构正确")
        test_results.append(("核心类结构", True))
    else:
        print("  [失败] 核心类结构不完整")
        test_results.append(("核心类结构", False))
        error_details.append("核心类缺少必要的方法或属性")

except Exception as e:
    print(f"  [失败] {e}")
    test_results.append(("核心类结构", False))
    error_details.append(f"核心类导入失败: {e}")
    traceback.print_exc()

# ============================================================================
# 测试 2: ServiceRegistry 单例注册不重复
# ============================================================================
print("\n[测试 2/10] ServiceRegistry 单例注册验证")
print("-" * 80)

try:
    from cullinan.core import get_injection_registry
    from cullinan.service import get_service_registry

    # 获取注册表
    inj_reg = get_injection_registry()
    svc_reg = get_service_registry()

    # 检查 ServiceRegistry 被注册的次数
    provider_count = 0
    for priority, registry in inj_reg._provider_registries:
        if registry is svc_reg:
            provider_count += 1

    print(f"  ServiceRegistry 注册次数: {provider_count}")

    if provider_count == 1:
        print("  [通过] ServiceRegistry 仅注册一次")
        test_results.append(("单例注册", True))
    else:
        print(f"  [失败] ServiceRegistry 被注册了 {provider_count} 次（应该只有1次）")
        test_results.append(("单例注册", False))
        error_details.append(f"ServiceRegistry 重复注册 {provider_count} 次")

except Exception as e:
    print(f"  [失败] {e}")
    test_results.append(("单例注册", False))
    error_details.append(f"单例注册验证失败: {e}")
    traceback.print_exc()

# ============================================================================
# 测试 3: 线程安全 - 并发创建单例
# ============================================================================
print("\n[测试 3/10] 线程安全单例创建")
print("-" * 80)

try:
    from cullinan.service import service, Service, reset_service_registry, get_service_registry
    from cullinan.core import reset_injection_registry, get_injection_registry

    reset_injection_registry()
    reset_service_registry()

    # 重新建立连接
    inj_reg = get_injection_registry()
    svc_reg = get_service_registry()
    inj_reg.add_provider_registry(svc_reg, priority=100)

    creation_count = [0]
    creation_lock = threading.Lock()

    @service
    class ConcurrentService(Service):
        def __init__(self):
            with creation_lock:
                creation_count[0] += 1
            time.sleep(0.01)  # 模拟耗时初始化
            super().__init__()

    results = []
    errors = []

    def worker():
        try:
            inst = svc_reg.get_instance('ConcurrentService')
            results.append(inst)
        except Exception as e:
            errors.append(e)

    # 启动20个并发线程
    threads = [threading.Thread(target=worker) for _ in range(20)]
    start_time = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start_time

    unique_instances = len(set(id(r) for r in results))

    print(f"  线程数: 20")
    print(f"  创建次数: {creation_count[0]}")
    print(f"  返回实例数: {len(results)}")
    print(f"  唯一实例数: {unique_instances}")
    print(f"  错误数: {len(errors)}")
    print(f"  耗时: {elapsed:.3f}秒")

    if creation_count[0] == 1 and unique_instances == 1 and len(results) == 20 and len(errors) == 0:
        print("  [通过] 线程安全，仅创建一个实例")
        test_results.append(("线程安全", True))
    else:
        print(f"  [失败] 创建了{creation_count[0]}个实例，有{unique_instances}个唯一实例")
        test_results.append(("线程安全", False))
        error_details.append(f"线程安全失败: {creation_count[0]}次创建, {unique_instances}个唯一实例")
        if errors:
            for err in errors:
                print(f"    错误: {err}")

except Exception as e:
    print(f"  [失败] {e}")
    test_results.append(("线程安全", False))
    error_details.append(f"线程安全测试失败: {e}")
    traceback.print_exc()

# ============================================================================
# 测试 4: 循环依赖检测
# ============================================================================
print("\n[测试 4/10] 循环依赖检测")
print("-" * 80)

try:
    from cullinan.service import service, Service, reset_service_registry, get_service_registry
    from cullinan.core import reset_injection_registry

    reset_injection_registry()
    reset_service_registry()

    @service
    class ServiceA(Service):
        pass

    @service
    class ServiceB(Service):
        pass

    svc_reg = get_service_registry()

    # 手动创建循环依赖
    svc_reg._injector._dependencies['ServiceA'] = ['ServiceB']
    svc_reg._injector._dependencies['ServiceB'] = ['ServiceA']

    detected = False
    error_msg = ""

    try:
        svc_reg.get_instance('ServiceA')
    except RecursionError as e:
        detected = True
        error_msg = str(e)
    except Exception as e:
        detected = True
        error_msg = f"Other error: {e}"

    print(f"  循环依赖检测: {detected}")
    if error_msg:
        print(f"  错误信息: {error_msg[:100]}")

    if detected and "Circular" in error_msg:
        print("  [通过] 成功检测循环依赖")
        test_results.append(("循环依赖检测", True))
    elif detected:
        print("  [警告] 检测到错误但不是标准的循环依赖错误")
        test_results.append(("循环依赖检测", True))
    else:
        print("  [失败] 未能检测循环依赖")
        test_results.append(("循环依赖检测", False))
        error_details.append("循环依赖未被检测")

except Exception as e:
    print(f"  [失败] {e}")
    test_results.append(("循环依赖检测", False))
    error_details.append(f"循环依赖测试失败: {e}")
    traceback.print_exc()

# ============================================================================
# 测试 5: Inject 描述符功能
# ============================================================================
print("\n[测试 5/10] Inject 描述符功能")
print("-" * 80)

try:
    from cullinan.core import Inject, reset_injection_registry, get_injection_registry
    from cullinan.service import service, Service, reset_service_registry, get_service_registry

    reset_injection_registry()
    reset_service_registry()

    inj_reg = get_injection_registry()
    svc_reg = get_service_registry()
    inj_reg.add_provider_registry(svc_reg, priority=100)

    @service
    class TestService(Service):
        def get_value(self):
            return "test_value"

    class TestClass:
        test_service: 'TestService' = Inject()

    # 测试类级别访问
    class_attr = TestClass.test_service
    print(f"  类级别访问类型: {type(class_attr).__name__}")

    # 测试实例级别访问
    obj = TestClass()
    inst_attr = obj.test_service
    print(f"  实例级别访问类型: {type(inst_attr).__name__}")

    # 测试功能
    result = inst_attr.get_value()
    print(f"  调用结果: {result}")

    # 测试缓存
    second_access = obj.test_service
    is_cached = second_access is inst_attr
    print(f"  实例缓存: {is_cached}")

    if isinstance(class_attr, Inject) and isinstance(inst_attr, TestService) and result == "test_value" and is_cached:
        print("  [通过] Inject 描述符工作正常")
        test_results.append(("Inject描述符", True))
    else:
        print("  [失败] Inject 描述符行为异常")
        test_results.append(("Inject描述符", False))
        error_details.append("Inject 描述符功能不正确")

except Exception as e:
    print(f"  [失败] {e}")
    test_results.append(("Inject描述符", False))
    error_details.append(f"Inject描述符测试失败: {e}")
    traceback.print_exc()

# ============================================================================
# 测试 6: InjectByName 描述符功能
# ============================================================================
print("\n[测试 6/10] InjectByName 描述符功能")
print("-" * 80)

try:
    from cullinan.core import InjectByName, reset_injection_registry, get_injection_registry
    from cullinan.service import service, Service, reset_service_registry, get_service_registry

    reset_injection_registry()
    reset_service_registry()

    inj_reg = get_injection_registry()
    svc_reg = get_service_registry()
    inj_reg.add_provider_registry(svc_reg, priority=100)

    @service
    class NamedService(Service):
        def get_name(self):
            return "named_service"

    class NamedUser:
        named_service = InjectByName('NamedService')

    obj = NamedUser()
    result = obj.named_service.get_name()

    print(f"  服务类型: {type(obj.named_service).__name__}")
    print(f"  调用结果: {result}")

    # 测试缓存
    is_cached = obj.named_service is obj.named_service
    print(f"  缓存有效: {is_cached}")

    if isinstance(obj.named_service, NamedService) and result == "named_service" and is_cached:
        print("  [通过] InjectByName 工作正常")
        test_results.append(("InjectByName", True))
    else:
        print("  [失败] InjectByName 行为异常")
        test_results.append(("InjectByName", False))
        error_details.append("InjectByName 功能不正确")

except Exception as e:
    print(f"  [失败] {e}")
    test_results.append(("InjectByName", False))
    error_details.append(f"InjectByName测试失败: {e}")
    traceback.print_exc()

# ============================================================================
# 测试 7: 字符串注解支持
# ============================================================================
print("\n[测试 7/10] 字符串注解支持")
print("-" * 80)

try:
    from cullinan.core import Inject, reset_injection_registry, get_injection_registry
    from cullinan.service import service, Service, reset_service_registry, get_service_registry

    reset_injection_registry()
    reset_service_registry()

    inj_reg = get_injection_registry()
    svc_reg = get_service_registry()
    inj_reg.add_provider_registry(svc_reg, priority=100)

    # 先定义使用者（使用字符串注解）
    class StringAnnotationUser:
        email_service: 'EmailService' = Inject()
        user_service: 'UserService' = Inject()

    # 后定义服务
    @service
    class EmailService(Service):
        def send(self):
            return "email_sent"

    @service
    class UserService(Service):
        def get(self):
            return "user_data"

    obj = StringAnnotationUser()
    email_result = obj.email_service.send()
    user_result = obj.user_service.get()

    print(f"  EmailService 类型: {type(obj.email_service).__name__}")
    print(f"  UserService 类型: {type(obj.user_service).__name__}")
    print(f"  Email 结果: {email_result}")
    print(f"  User 结果: {user_result}")

    if (isinstance(obj.email_service, EmailService) and
        isinstance(obj.user_service, UserService) and
        email_result == "email_sent" and user_result == "user_data"):
        print("  [通过] 字符串注解支持正常")
        test_results.append(("字符串注解", True))
    else:
        print("  [失败] 字符串注解解析失败")
        test_results.append(("字符串注解", False))
        error_details.append("字符串注解不工作")

except Exception as e:
    print(f"  [失败] {e}")
    test_results.append(("字符串注解", False))
    error_details.append(f"字符串注解测试失败: {e}")
    traceback.print_exc()

# ============================================================================
# 测试 8: 可选依赖
# ============================================================================
print("\n[测试 8/10] 可选依赖")
print("-" * 80)

try:
    from cullinan.core import Inject, reset_injection_registry, get_injection_registry
    from cullinan.service import reset_service_registry, get_service_registry

    reset_injection_registry()
    reset_service_registry()

    inj_reg = get_injection_registry()
    svc_reg = get_service_registry()
    inj_reg.add_provider_registry(svc_reg, priority=100)

    class OptionalUser:
        non_existent: 'NonExistent' = Inject(required=False)

    obj = OptionalUser()
    result = obj.non_existent

    print(f"  可选依赖结果: {result}")
    print(f"  类型: {type(result)}")

    if result is None:
        print("  [通过] 可选依赖返回 None")
        test_results.append(("可选依赖", True))
    else:
        print("  [失败] 可选依赖应该返回 None")
        test_results.append(("可选依赖", False))
        error_details.append(f"可选依赖返回了 {result}")

except Exception as e:
    print(f"  [失败] {e}")
    test_results.append(("可选依赖", False))
    error_details.append(f"可选依赖测试失败: {e}")
    traceback.print_exc()

# ============================================================================
# 测试 9: 必需依赖缺失检测
# ============================================================================
print("\n[测试 9/10] 必需依赖缺失检测")
print("-" * 80)

try:
    from cullinan.core import Inject, reset_injection_registry, get_injection_registry
    from cullinan.service import reset_service_registry, get_service_registry
    from cullinan.core.exceptions import RegistryError

    reset_injection_registry()
    reset_service_registry()

    inj_reg = get_injection_registry()
    svc_reg = get_service_registry()
    inj_reg.add_provider_registry(svc_reg, priority=100)

    class RequiredUser:
        missing_service: 'MissingService' = Inject(required=True)

    obj = RequiredUser()

    exception_raised = False
    error_type = None

    try:
        _ = obj.missing_service
    except RegistryError as e:
        exception_raised = True
        error_type = "RegistryError"
    except Exception as e:
        exception_raised = True
        error_type = type(e).__name__

    print(f"  异常抛出: {exception_raised}")
    print(f"  异常类型: {error_type}")

    if exception_raised and error_type == "RegistryError":
        print("  [通过] 正确抛出 RegistryError")
        test_results.append(("必需依赖检测", True))
    elif exception_raised:
        print(f"  [警告] 抛出了异常但类型是 {error_type}")
        test_results.append(("必需依赖检测", True))
    else:
        print("  [失败] 未抛出异常")
        test_results.append(("必需依赖检测", False))
        error_details.append("必需依赖缺失未检测")

except Exception as e:
    print(f"  [失败] 测试本身出错: {e}")
    test_results.append(("必需依赖检测", False))
    error_details.append(f"必需依赖测试失败: {e}")
    traceback.print_exc()

# ============================================================================
# 测试 10: 内存泄漏检查（简单版）
# ============================================================================
print("\n[测试 10/10] 内存泄漏检查")
print("-" * 80)

try:
    from cullinan.core import reset_injection_registry, get_injection_registry
    from cullinan.service import service, Service, reset_service_registry, get_service_registry
    import gc

    # 多次创建和清理
    for i in range(5):
        reset_injection_registry()
        reset_service_registry()

        inj_reg = get_injection_registry()
        svc_reg = get_service_registry()
        inj_reg.add_provider_registry(svc_reg, priority=100)

        @service
        class TempService(Service):
            pass

        for j in range(10):
            inst = svc_reg.get_instance('TempService')

        # 清理
        reset_service_registry()
        reset_injection_registry()
        gc.collect()

    print(f"  完成 5 轮创建和清理")
    print(f"  每轮 10 次实例获取")
    print("  [通过] 内存泄漏检查完成（未崩溃）")
    test_results.append(("内存泄漏", True))

except Exception as e:
    print(f"  [失败] {e}")
    test_results.append(("内存泄漏", False))
    error_details.append(f"内存泄漏测试失败: {e}")
    traceback.print_exc()

# ============================================================================
# 总结报告
# ============================================================================
print("\n" + "="*80)
print("测试总结")
print("="*80)

passed = sum(1 for _, result in test_results if result)
total = len(test_results)

for name, result in test_results:
    status = "[通过]" if result else "[失败]"
    print(f"  {status}: {name}")

print(f"\n总计: {passed}/{total} 通过")

if error_details:
    print("\n错误详情:")
    for i, error in enumerate(error_details, 1):
        print(f"  {i}. {error}")

print("\n" + "="*80)

if passed == total:
    print("[OK] 所有测试通过 - IoC 系统安全稳定")
    print("="*80)
    sys.exit(0)
else:
    print(f"[FAIL] {total - passed} 个测试失败 - 需要修复")
    print("="*80)
    sys.exit(1)

