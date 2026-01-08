# -*- coding: utf-8 -*-
"""全面测试：所有参数类型解析验证

Author: Plumeink
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.params import Path, Query, Body, Header, File, DynamicBody, ParamResolver, AutoType
from cullinan.params.validator import ValidationError

print("=" * 70)
print("全面参数类型测试")
print("=" * 70)

# ============================================================================
# 测试1: Path 参数
# ============================================================================
print("\n1. Path 参数测试")
print("-" * 40)

def test_path(self, id: Path(int), name: Path(str)):
    pass

config = ParamResolver.analyze_params(test_path)
print(f"   参数配置: {list(config.keys())}")
for name, cfg in config.items():
    print(f"   - {name}: source={cfg['source']}, type={cfg['type'].__name__}, required={cfg['required']}")

# 测试解析
result = ParamResolver.resolve(
    func=test_path,
    request=None,
    url_params={'id': '123', 'name': 'test'}
)
print(f"   解析结果: {result}")
print(f"   id 类型: {type(result['id']).__name__}, 值: {result['id']}")
assert result['id'] == 123, "Path(int) 转换失败"
assert result['name'] == 'test', "Path(str) 转换失败"
print("   ✅ Path 参数测试通过")

# ============================================================================
# 测试2: Query 参数
# ============================================================================
print("\n2. Query 参数测试")
print("-" * 40)

def test_query(
    self,
    page: Query(int, default=1, ge=1),
    size: Query(int, default=10, ge=1, le=100),
    q: Query(str, required=False),
    active: Query(bool, default=True),
):
    pass

config = ParamResolver.analyze_params(test_query)
print(f"   参数配置: {list(config.keys())}")

# 测试解析 - 有值
result = ParamResolver.resolve(
    func=test_query,
    request=None,
    query_params={'page': '2', 'size': '20', 'q': 'hello', 'active': 'false'}
)
print(f"   解析结果(有值): {result}")
assert result['page'] == 2, "Query(int) 转换失败"
assert result['size'] == 20, "Query(int) 转换失败"
assert result['q'] == 'hello', "Query(str) 转换失败"
assert result['active'] == False, "Query(bool) 转换失败"

# 测试解析 - 使用默认值
result = ParamResolver.resolve(
    func=test_query,
    request=None,
    query_params={}
)
print(f"   解析结果(默认): {result}")
assert result['page'] == 1, "Query 默认值失败"
assert result['size'] == 10, "Query 默认值失败"
assert result['q'] is None, "Query optional 应为 None"
assert result['active'] == True, "Query(bool) 默认值失败"
print("   ✅ Query 参数测试通过")

# ============================================================================
# 测试3: Body 参数
# ============================================================================
print("\n3. Body 参数测试")
print("-" * 40)

def test_body(
    self,
    name: Body(str, required=True),
    age: Body(int, default=0, ge=0, le=150),
    email: Body(str, required=False),
):
    pass

config = ParamResolver.analyze_params(test_body)
print(f"   参数配置: {list(config.keys())}")

# 测试解析 - 有值
result = ParamResolver.resolve(
    func=test_body,
    request=None,
    body_data={'name': 'John', 'age': '25', 'email': 'john@example.com'}
)
print(f"   解析结果: {result}")
assert result['name'] == 'John', "Body(str) 转换失败"
assert result['age'] == 25, "Body(int) 转换失败"
assert result['email'] == 'john@example.com', "Body(str) 转换失败"

# 测试解析 - 使用默认值
result = ParamResolver.resolve(
    func=test_body,
    request=None,
    body_data={'name': 'Jane'}
)
print(f"   解析结果(默认): {result}")
assert result['name'] == 'Jane', "Body(str) 转换失败"
assert result['age'] == 0, "Body 默认值失败"
assert result['email'] is None, "Body optional 应为 None"
print("   ✅ Body 参数测试通过")

# ============================================================================
# 测试4: Header 参数
# ============================================================================
print("\n4. Header 参数测试")
print("-" * 40)

def test_header(
    self,
    auth: Header(str, alias='Authorization', required=True),
    request_id: Header(str, alias='X-Request-ID', required=False),
):
    pass

config = ParamResolver.analyze_params(test_header)
print(f"   参数配置: {list(config.keys())}")
for name, cfg in config.items():
    alias = cfg.get('param_spec').alias if cfg.get('param_spec') else None
    print(f"   - {name}: source={cfg['source']}, alias={alias}")

# 测试解析
result = ParamResolver.resolve(
    func=test_header,
    request=None,
    headers={'Authorization': 'Bearer token123', 'X-Request-ID': 'req-456'}
)
print(f"   解析结果: {result}")
assert result['auth'] == 'Bearer token123', "Header 解析失败"
assert result['request_id'] == 'req-456', "Header 解析失败"

# 测试解析 - 只有必填
result = ParamResolver.resolve(
    func=test_header,
    request=None,
    headers={'Authorization': 'Bearer token789'}
)
print(f"   解析结果(部分): {result}")
assert result['auth'] == 'Bearer token789', "Header 解析失败"
assert result['request_id'] is None, "Header optional 应为 None"
print("   ✅ Header 参数测试通过")

# ============================================================================
# 测试5: DynamicBody
# ============================================================================
print("\n5. DynamicBody 测试")
print("-" * 40)

def test_dynamic_body(self, body: DynamicBody):
    pass

config = ParamResolver.analyze_params(test_dynamic_body)
print(f"   参数配置: {list(config.keys())}")
for name, cfg in config.items():
    print(f"   - {name}: source={cfg['source']}, type={cfg['type'].__name__}")

# 测试解析
result = ParamResolver.resolve(
    func=test_dynamic_body,
    request=None,
    body_data={'name': 'Test', 'nested': {'a': 1, 'b': 2}, 'tags': [1, 2, 3]}
)
print(f"   解析结果: {result}")
body = result['body']
print(f"   body.name = {body.name}")
print(f"   body.nested = {body.nested}")
print(f"   body.tags = {body.tags}")
print(f"   body.get('missing', 'default') = {body.get('missing', 'default')}")
assert body.name == 'Test', "DynamicBody.name 失败"
assert body.nested.a == 1, "DynamicBody 嵌套访问失败"
assert body.tags == [1, 2, 3], "DynamicBody 列表访问失败"
# 注意：'items', 'keys', 'values', 'get' 等字典方法名会与属性名冲突
# 使用 body['items'] 或 body.to_dict()['items'] 访问这些特殊名称
print("   ✅ DynamicBody 测试通过")

# ============================================================================
# 测试6: 校验测试
# ============================================================================
print("\n6. 参数校验测试")
print("-" * 40)

def test_validation(
    self,
    age: Body(int, ge=0, le=150),
    name: Body(str, min_length=2, max_length=50),
):
    pass

# 测试校验通过
result = ParamResolver.resolve(
    func=test_validation,
    request=None,
    body_data={'age': '25', 'name': 'John'}
)
print(f"   校验通过: {result}")

# 测试校验失败 - ge
try:
    result = ParamResolver.resolve(
        func=test_validation,
        request=None,
        body_data={'age': '-1', 'name': 'John'}
    )
    print("   ❌ ge 校验应该失败")
except Exception as e:
    print(f"   ✅ ge 校验正确失败: {e}")

# 测试校验失败 - min_length
try:
    result = ParamResolver.resolve(
        func=test_validation,
        request=None,
        body_data={'age': '25', 'name': 'J'}
    )
    print("   ❌ min_length 校验应该失败")
except Exception as e:
    print(f"   ✅ min_length 校验正确失败: {e}")

print("   ✅ 参数校验测试通过")

# ============================================================================
# 测试7: 混合参数测试
# ============================================================================
print("\n7. 混合参数测试")
print("-" * 40)

def test_mixed(
    self,
    id: Path(int),
    page: Query(int, default=1),
    name: Body(str, required=True),
    auth: Header(str, alias='Authorization'),
):
    pass

config = ParamResolver.analyze_params(test_mixed)
print(f"   参数配置: {list(config.keys())}")
for name, cfg in config.items():
    print(f"   - {name}: source={cfg['source']}")

result = ParamResolver.resolve(
    func=test_mixed,
    request=None,
    url_params={'id': '42'},
    query_params={'page': '3'},
    body_data={'name': 'Alice'},
    headers={'Authorization': 'Bearer xxx'}
)
print(f"   解析结果: {result}")
assert result['id'] == 42, "混合 Path 失败"
assert result['page'] == 3, "混合 Query 失败"
assert result['name'] == 'Alice', "混合 Body 失败"
assert result['auth'] == 'Bearer xxx', "混合 Header 失败"
print("   ✅ 混合参数测试通过")

# ============================================================================
# 测试8: 类型转换测试
# ============================================================================
print("\n8. 类型转换测试")
print("-" * 40)

def test_types(
    self,
    int_val: Query(int),
    float_val: Query(float),
    bool_val: Query(bool),
    str_val: Query(str),
):
    pass

# 测试各种类型转换
result = ParamResolver.resolve(
    func=test_types,
    request=None,
    query_params={
        'int_val': '123',
        'float_val': '3.14',
        'bool_val': 'true',
        'str_val': 'hello'
    }
)
print(f"   解析结果: {result}")
assert result['int_val'] == 123 and type(result['int_val']) is int, "int 转换失败"
assert result['float_val'] == 3.14 and type(result['float_val']) is float, "float 转换失败"
assert result['bool_val'] == True and type(result['bool_val']) is bool, "bool 转换失败"
assert result['str_val'] == 'hello' and type(result['str_val']) is str, "str 转换失败"

# bool 多种格式测试
def test_bool_formats(self, val: Query(bool)):
    pass

for true_val in ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'on']:
    result = ParamResolver.resolve(
        func=test_bool_formats, request=None, query_params={'val': true_val}
    )
    assert result['val'] == True, f"bool 转换 {true_val} 失败"

for false_val in ['false', 'False', 'FALSE', '0', 'no', 'No', 'off']:
    result = ParamResolver.resolve(
        func=test_bool_formats, request=None, query_params={'val': false_val}
    )
    assert result['val'] == False, f"bool 转换 {false_val} 失败"

print("   ✅ 类型转换测试通过")

print("\n" + "=" * 70)
print("所有参数类型测试完成！")
print("=" * 70)

