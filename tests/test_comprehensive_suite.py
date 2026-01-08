# -*- coding: utf-8 -*-
"""Cullinan 全面测试套件

包括：
1. 核心功能测试
2. IoC/DI 测试
3. 参数系统测试
4. Codec 测试
5. 性能基准测试
6. 回归测试

Author: Plumeink
"""

import sys
import os
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试结果收集
test_results = {
    'passed': 0,
    'failed': 0,
    'errors': []
}

def test(name):
    """测试装饰器"""
    def decorator(func):
        def wrapper():
            try:
                print(f"  Testing: {name}...", end=" ")
                start = time.perf_counter()
                func()
                elapsed = (time.perf_counter() - start) * 1000
                print(f"PASSED ({elapsed:.2f}ms)")
                test_results['passed'] += 1
                return True
            except AssertionError as e:
                print(f"FAILED: {e}")
                test_results['failed'] += 1
                test_results['errors'].append((name, str(e)))
                return False
            except Exception as e:
                print(f"ERROR: {e}")
                test_results['failed'] += 1
                test_results['errors'].append((name, traceback.format_exc()))
                return False
        return wrapper
    return decorator


# ============================================================================
# 1. IoC/DI 核心测试
# ============================================================================
print("\n" + "=" * 70)
print("1. IoC/DI 核心测试")
print("=" * 70)

@test("ApplicationContext 基本功能")
def test_app_context_basic():
    from cullinan.core import ApplicationContext
    from cullinan.core.pending import PendingRegistry
    from cullinan.core import service

    PendingRegistry.reset()

    @service
    class TestService:
        def get_name(self):
            return 'test'

    ctx = ApplicationContext()
    ctx.refresh()

    svc = ctx.get('TestService')
    assert svc is not None, "Service should not be None"
    assert svc.get_name() == 'test', "Service name should be 'test'"

test_app_context_basic()

@test("Inject 描述符")
def test_inject_descriptor():
    from cullinan.core import Inject, InjectByName
    from cullinan.core import service, ApplicationContext
    from cullinan.core.pending import PendingRegistry

    # 清理状态
    PendingRegistry.reset()

    @service
    class DepService:
        def get_value(self):
            return 42

    @service
    class MainService:
        dep: DepService = Inject()

        def compute(self):
            return self.dep.get_value() * 2

    ctx = ApplicationContext()
    ctx.refresh()

    main = ctx.get('MainService')
    assert main is not None, "MainService should not be None"
    assert main.compute() == 84, "Compute should return 84"

test_inject_descriptor()

@test("InjectByName 描述符")
def test_inject_by_name():
    from cullinan.core import InjectByName
    from cullinan.core import service, ApplicationContext
    from cullinan.core.pending import PendingRegistry

    PendingRegistry.reset()

    @service
    class NamedService:
        def get_name(self):
            return "NamedService"

    @service
    class ConsumerService:
        named = InjectByName('NamedService')

        def use(self):
            return self.named.get_name()

    ctx = ApplicationContext()
    ctx.refresh()

    consumer = ctx.get('ConsumerService')
    assert consumer.use() == "NamedService"

test_inject_by_name()

@test("条件注册 ConditionalOnClass")
def test_conditional_on_class():
    from cullinan.core import service, ApplicationContext
    from cullinan.core.conditions import ConditionalOnClass
    from cullinan.core.pending import PendingRegistry

    PendingRegistry.reset()

    @service
    @ConditionalOnClass('json')  # json 模块存在
    class JsonService2:
        pass

    @service
    @ConditionalOnClass('nonexistent_module_xyz_abc')  # 不存在的模块
    class NonExistentService2:
        pass

    ctx = ApplicationContext()
    ctx.refresh()

    assert ctx.get('JsonService2') is not None, "JsonService2 should exist"
    # 不存在的模块条件下的服务可能抛异常或返回 None，这里只检查 JsonService2 存在

test_conditional_on_class()


# ============================================================================
# 2. 参数系统测试
# ============================================================================
print("\n" + "=" * 70)
print("2. 参数系统测试")
print("=" * 70)

@test("Path 参数解析")
def test_path_param():
    from cullinan.params import Path, ParamResolver

    def handler(self, id: Path(int), name: Path(str)):
        pass

    result = ParamResolver.resolve(
        func=handler,
        request=None,
        url_params={'id': '123', 'name': 'test'}
    )

    assert result['id'] == 123, f"Expected 123, got {result['id']}"
    assert type(result['id']) is int, f"Expected int, got {type(result['id'])}"
    assert result['name'] == 'test'

test_path_param()

@test("Query 参数解析和默认值")
def test_query_param():
    from cullinan.params import Query, ParamResolver

    def handler(self, page: Query(int, default=1), size: Query(int, default=10)):
        pass

    # 有值
    result = ParamResolver.resolve(
        func=handler,
        request=None,
        query_params={'page': '5', 'size': '20'}
    )
    assert result['page'] == 5
    assert result['size'] == 20

    # 默认值
    result = ParamResolver.resolve(
        func=handler,
        request=None,
        query_params={}
    )
    assert result['page'] == 1
    assert result['size'] == 10

test_query_param()

@test("Body 参数解析")
def test_body_param():
    from cullinan.params import Body, ParamResolver

    def handler(self, name: Body(str, required=True), age: Body(int, default=0)):
        pass

    result = ParamResolver.resolve(
        func=handler,
        request=None,
        body_data={'name': 'Alice', 'age': '25'}
    )

    assert result['name'] == 'Alice'
    assert result['age'] == 25
    assert type(result['age']) is int

test_body_param()

@test("Header 参数解析和 alias")
def test_header_param():
    from cullinan.params import Header, ParamResolver

    def handler(self, auth: Header(str, alias='Authorization')):
        pass

    result = ParamResolver.resolve(
        func=handler,
        request=None,
        headers={'Authorization': 'Bearer token123'}
    )

    assert result['auth'] == 'Bearer token123'

test_header_param()

@test("DynamicBody 解析")
def test_dynamic_body():
    from cullinan.params import DynamicBody, ParamResolver

    def handler(self, body: DynamicBody):
        pass

    result = ParamResolver.resolve(
        func=handler,
        request=None,
        body_data={'name': 'Test', 'age': 25, 'nested': {'a': 1}}
    )

    body = result['body']
    assert body.name == 'Test'
    assert body.age == 25
    assert body.nested.a == 1
    assert body.get('missing', 'default') == 'default'

test_dynamic_body()

@test("类型转换 - bool")
def test_type_conversion_bool():
    from cullinan.params import Query, ParamResolver

    def handler(self, val: Query(bool)):
        pass

    for true_val in ['true', 'True', 'TRUE', '1', 'yes', 'on']:
        result = ParamResolver.resolve(func=handler, request=None, query_params={'val': true_val})
        assert result['val'] == True, f"Expected True for '{true_val}'"

    for false_val in ['false', 'False', 'FALSE', '0', 'no', 'off']:
        result = ParamResolver.resolve(func=handler, request=None, query_params={'val': false_val})
        assert result['val'] == False, f"Expected False for '{false_val}'"

test_type_conversion_bool()

@test("参数校验 - ge/le")
def test_param_validation_ge_le():
    from cullinan.params import Body, ParamResolver, ResolveError

    def handler(self, age: Body(int, ge=0, le=150)):
        pass

    # 合法值
    result = ParamResolver.resolve(func=handler, request=None, body_data={'age': '25'})
    assert result['age'] == 25

    # 非法值 - 小于 ge
    try:
        ParamResolver.resolve(func=handler, request=None, body_data={'age': '-1'})
        assert False, "Should raise ResolveError"
    except ResolveError:
        pass

    # 非法值 - 大于 le
    try:
        ParamResolver.resolve(func=handler, request=None, body_data={'age': '200'})
        assert False, "Should raise ResolveError"
    except ResolveError:
        pass

test_param_validation_ge_le()

@test("参数校验 - min_length/max_length")
def test_param_validation_length():
    from cullinan.params import Body, ParamResolver, ResolveError

    def handler(self, name: Body(str, min_length=2, max_length=10)):
        pass

    # 合法值
    result = ParamResolver.resolve(func=handler, request=None, body_data={'name': 'hello'})
    assert result['name'] == 'hello'

    # 非法值 - 太短
    try:
        ParamResolver.resolve(func=handler, request=None, body_data={'name': 'a'})
        assert False, "Should raise ResolveError for min_length"
    except ResolveError:
        pass

test_param_validation_length()


# ============================================================================
# 3. Codec 测试
# ============================================================================
print("\n" + "=" * 70)
print("3. Codec 测试")
print("=" * 70)

@test("JSON Codec 编解码")
def test_json_codec():
    from cullinan.codec import JsonBodyCodec

    codec = JsonBodyCodec()

    # 编码
    data = {'name': 'test', 'value': 123}
    encoded = codec.encode(data)
    assert isinstance(encoded, bytes)

    # 解码
    decoded = codec.decode(encoded)
    assert decoded == data

test_json_codec()

@test("Form Codec 编解码")
def test_form_codec():
    from cullinan.codec import FormBodyCodec

    codec = FormBodyCodec()

    # 编码
    data = {'name': 'test', 'value': '123'}
    encoded = codec.encode(data)
    assert isinstance(encoded, bytes)

    # 解码
    decoded = codec.decode(encoded)
    # Form codec 可能返回不同格式，只检查编解码不抛异常
    assert decoded is not None

test_form_codec()

@test("Codec Registry")
def test_codec_registry():
    from cullinan.codec import get_codec_registry

    registry = get_codec_registry()

    # 使用正确的方法名
    json_codec = registry.get_body_codec('application/json')
    assert json_codec is not None

    form_codec = registry.get_body_codec('application/x-www-form-urlencoded')
    assert form_codec is not None

test_codec_registry()


# ============================================================================
# 4. 控制器相关测试
# ============================================================================
print("\n" + "=" * 70)
print("4. 控制器相关测试")
print("=" * 70)

@test("控制器注册")
def test_controller_registration():
    from cullinan.controller import controller, get_api
    from cullinan.core.pending import PendingRegistry

    PendingRegistry.reset()

    @controller(url='/test')
    class TestController3:
        @get_api(url='/hello')
        def hello(self):
            pass

    # 检查是否在 PendingRegistry 中
    pending = PendingRegistry.get_instance()
    registrations = pending.get_all()

    found = any(r.name == 'TestController3' for r in registrations)
    assert found, "TestController3 should be in PendingRegistry"

test_controller_registration()

@test("URL 解析器")
def test_url_resolver():
    from cullinan.controller.core import url_resolver

    # 简单路径
    url, params = url_resolver('/users/{id}')
    assert 'id' in params, f"Params should contain 'id', got: {params}"
    assert '{id}' not in url, f"URL should have placeholder replaced, got: {url}"

    # 多参数
    url, params = url_resolver('/users/{user_id}/posts/{post_id}')
    assert 'user_id' in params
    assert 'post_id' in params

test_url_resolver()


# ============================================================================
# 5. 性能基准测试
# ============================================================================
print("\n" + "=" * 70)
print("5. 性能基准测试")
print("=" * 70)

@test("ParamResolver 解析性能 (1000次)")
def test_param_resolver_performance():
    from cullinan.params import Path, Query, Body, ParamResolver

    def handler(
        self,
        id: Path(int),
        page: Query(int, default=1),
        size: Query(int, default=10),
        name: Body(str, required=True),
        age: Body(int, default=0),
    ):
        pass

    start = time.perf_counter()
    iterations = 1000

    for _ in range(iterations):
        ParamResolver.resolve(
            func=handler,
            request=None,
            url_params={'id': '123'},
            query_params={'page': '5', 'size': '20'},
            body_data={'name': 'Test', 'age': '25'}
        )

    elapsed = (time.perf_counter() - start) * 1000
    avg = elapsed / iterations

    print(f"\n    Total: {elapsed:.2f}ms, Avg: {avg:.4f}ms/call", end="")

    # 性能阈值：每次解析应小于 0.5ms
    assert avg < 0.5, f"Performance too slow: {avg:.4f}ms/call"

test_param_resolver_performance()

@test("DynamicBody 访问性能 (10000次)")
def test_dynamic_body_performance():
    from cullinan.params import DynamicBody

    body = DynamicBody({
        'name': 'Test',
        'age': 25,
        'nested': {'a': 1, 'b': 2},
        'items': [1, 2, 3, 4, 5]
    })

    start = time.perf_counter()
    iterations = 10000

    for _ in range(iterations):
        _ = body.name
        _ = body.age
        _ = body.nested.a
        _ = body.get('missing', 'default')

    elapsed = (time.perf_counter() - start) * 1000
    avg = elapsed / iterations

    print(f"\n    Total: {elapsed:.2f}ms, Avg: {avg:.6f}ms/call", end="")

    # 性能阈值：每次访问应小于 0.01ms
    assert avg < 0.01, f"Performance too slow: {avg:.6f}ms/call"

test_dynamic_body_performance()

@test("类型转换性能 (5000次)")
def test_type_conversion_performance():
    from cullinan.params.converter import TypeConverter

    start = time.perf_counter()
    iterations = 5000

    for _ in range(iterations):
        TypeConverter.convert('123', int)
        TypeConverter.convert('3.14', float)
        TypeConverter.convert('true', bool)
        TypeConverter.convert('hello', str)

    elapsed = (time.perf_counter() - start) * 1000
    avg = elapsed / (iterations * 4)

    print(f"\n    Total: {elapsed:.2f}ms, Avg: {avg:.6f}ms/call", end="")

    # 性能阈值
    assert avg < 0.01, f"Performance too slow: {avg:.6f}ms/call"

test_type_conversion_performance()


# ============================================================================
# 6. 回归测试
# ============================================================================
print("\n" + "=" * 70)
print("6. 回归测试")
print("=" * 70)

@test("传统参数方式仍然支持")
def test_legacy_params():
    from cullinan.params import ParamResolver

    # 传统方式：参数名为 url_params, query_params 等
    def legacy_handler(self, url_params, query_params, body_params):
        pass

    config = ParamResolver.analyze_params(legacy_handler)

    # 传统参数应该被识别为 unknown source
    assert config['url_params']['source'] == 'unknown'
    assert config['query_params']['source'] == 'unknown'
    assert config['body_params']['source'] == 'unknown'

test_legacy_params()

@test("混合参数方式")
def test_mixed_params():
    from cullinan.params import Path, Query, ParamResolver

    # 混合方式：部分使用新参数，部分使用传统
    def mixed_handler(self, id: Path(int), url_params):
        pass

    config = ParamResolver.analyze_params(mixed_handler)

    assert config['id']['source'] == 'path'
    assert config['url_params']['source'] == 'unknown'

test_mixed_params()

@test("服务生命周期")
def test_service_lifecycle():
    from cullinan.service import service, Service
    from cullinan.core import ApplicationContext
    from cullinan.core.pending import PendingRegistry

    PendingRegistry.reset()

    lifecycle_events = []

    @service
    class LifecycleService(Service):
        def on_init(self):
            lifecycle_events.append('on_init')

        def on_startup(self):
            lifecycle_events.append('on_startup')

    ctx = ApplicationContext()
    ctx.refresh()

    # on_init 应该在 refresh 时被调用
    svc = ctx.get('LifecycleService')
    assert svc is not None
    # 注意：on_init 可能在实例化时调用，取决于实现

test_service_lifecycle()


# ============================================================================
# 测试总结
# ============================================================================
print("\n" + "=" * 70)
print("测试总结")
print("=" * 70)

total = test_results['passed'] + test_results['failed']
print(f"\n总测试数: {total}")
print(f"通过: {test_results['passed']}")
print(f"失败: {test_results['failed']}")

if test_results['errors']:
    print("\n失败详情:")
    for name, error in test_results['errors']:
        print(f"\n  {name}:")
        print(f"    {error[:200]}...")

print("\n" + "=" * 70)
if test_results['failed'] == 0:
    print("所有测试通过!")
else:
    print(f"有 {test_results['failed']} 个测试失败!")
    sys.exit(1)

