# -*- coding: utf-8 -*-
"""测试新参数系统集成

Author: Plumeink
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.params import DynamicBody, Path, Query, Body, ParamResolver

# 模拟控制器方法
def test_legacy_style(self, url_params, query_params, body_params):
    """传统方式"""
    pass

def test_new_style_dynamic_body(self, body: DynamicBody):
    """新方式：DynamicBody"""
    pass

def test_new_style_typed_params(self, id: Path(int), name: Query(str, default='')):
    """新方式：类型化参数"""
    pass

def test_mixed_style(self, body_params, name: Body(str, required=True)):
    """混合方式"""
    pass

def test_no_params(self):
    """无参数"""
    pass

# 测试分析
print("=== ParamResolver 参数分析测试 ===\n")

# 测试1：传统方式
print("1. 传统方式 (url_params, query_params, body_params):")
config = ParamResolver.analyze_params(test_legacy_style)
for name, cfg in config.items():
    print(f"   - {name}: source={cfg['source']}, type={cfg['type']}")
print()

# 测试2：新方式 DynamicBody
print("2. 新方式 DynamicBody (body: DynamicBody):")
config = ParamResolver.analyze_params(test_new_style_dynamic_body)
for name, cfg in config.items():
    print(f"   - {name}: source={cfg['source']}, type={cfg['type']}")
print()

# 测试3：新方式类型化参数
print("3. 新方式类型化参数 (id: Path(int), name: Query(str)):")
config = ParamResolver.analyze_params(test_new_style_typed_params)
for name, cfg in config.items():
    print(f"   - {name}: source={cfg['source']}, type={cfg['type']}, param_spec={cfg.get('param_spec')}")
print()

# 测试4：混合方式
print("4. 混合方式 (body_params, name: Body(str)):")
config = ParamResolver.analyze_params(test_mixed_style)
for name, cfg in config.items():
    print(f"   - {name}: source={cfg['source']}, type={cfg['type']}")
print()

# 测试5：无参数
print("5. 无参数 (self):")
config = ParamResolver.analyze_params(test_no_params)
print(f"   参数数量: {len(config)}")
print()

# 测试 resolve
print("=== ParamResolver.resolve 测试 ===\n")

print("6. 解析 DynamicBody:")
try:
    result = ParamResolver.resolve(
        func=test_new_style_dynamic_body,
        request=None,
        body_data={'name': 'test', 'age': 18}
    )
    print(f"   解析结果: {result}")
    body = result.get('body')
    if body:
        print(f"   body.name = {body.name}")
        print(f"   body.age = {body.age}")
except Exception as e:
    print(f"   错误: {e}")
print()

print("7. 解析类型化参数:")
try:
    result = ParamResolver.resolve(
        func=test_new_style_typed_params,
        request=None,
        url_params={'id': '123'},
        query_params={'name': 'hello'}
    )
    print(f"   解析结果: {result}")
    print(f"   id 类型: {type(result.get('id'))}")
except Exception as e:
    print(f"   错误: {e}")
print()

print("=== 测试完成 ===")

