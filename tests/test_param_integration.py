# -*- coding: utf-8 -*-
"""端到端测试：新参数系统在控制器中的集成

Author: Plumeink
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 简单测试：检查 controller core 是否能正确导入新参数系统
print("=== 测试1: 导入检查 ===")
try:
    from cullinan.controller.core import (
        Param, DynamicBody, ParamResolver, ResolveError
    )
    print("[OK] 新参数系统模块已成功导入到 controller.core")
except ImportError as e:
    print(f"[FAIL] 导入失败: {e}")
    sys.exit(1)

print()

# 测试2：检查 request_handler 函数签名
print("=== 测试2: request_handler 函数检查 ===")
try:
    from cullinan.controller.core import request_handler
    import inspect
    sig = inspect.signature(request_handler)
    print(f"[OK] request_handler 签名: {sig}")
except Exception as e:
    print(f"[FAIL] 检查失败: {e}")

print()

# 测试3：模拟控制器类和方法
print("=== 测试3: 模拟控制器分析 ===")

from cullinan.params import Path, Query, Body, DynamicBody, ParamResolver

class MockController:
    """模拟控制器"""

    def hello_dynamic(self, body: DynamicBody):
        """使用 DynamicBody"""
        name = body.get('name', 'World')
        return {"message": f"Hello, {name}!"}

    def hello_typed(self, name: Body(str, default='World')):
        """使用类型化 Body 参数"""
        return {"message": f"Hello, {name}!"}

    def get_user(self, id: Path(int), verbose: Query(bool, default=False)):
        """使用 Path 和 Query 参数"""
        return {"id": id, "verbose": verbose}

    def legacy_style(self, body_params):
        """传统方式"""
        name = body_params.get('name', 'World') if body_params else 'World'
        return {"message": f"Hello, {name}!"}

# 分析各方法
methods = [
    ('hello_dynamic', MockController.hello_dynamic),
    ('hello_typed', MockController.hello_typed),
    ('get_user', MockController.get_user),
    ('legacy_style', MockController.legacy_style),
]

for method_name, method in methods:
    config = ParamResolver.analyze_params(method)
    uses_new = any(
        cfg.get('param_spec') is not None or cfg.get('type') is DynamicBody
        for cfg in config.values()
    )
    print(f"  {method_name}: uses_new_system={uses_new}")
    for name, cfg in config.items():
        print(f"    - {name}: source={cfg['source']}, type={cfg['type'].__name__}")

print()

# 测试4：实际解析
print("=== 测试4: 实际参数解析 ===")

# 测试 DynamicBody
print("\n4.1 DynamicBody 解析:")
result = ParamResolver.resolve(
    func=MockController.hello_dynamic,
    request=None,
    body_data={'name': 'Cullinan'}
)
print(f"  解析结果: {result}")
body = result['body']
print(f"  body.name = {body.name}")
print(f"  调用方法: {MockController().hello_dynamic(body)}")

# 测试类型化参数
print("\n4.2 类型化 Body 参数解析:")
result = ParamResolver.resolve(
    func=MockController.hello_typed,
    request=None,
    body_data={'name': 'TypedUser'}
)
print(f"  解析结果: {result}")
print(f"  调用方法: {MockController().hello_typed(result['name'])}")

# 测试 Path + Query
print("\n4.3 Path + Query 参数解析:")
result = ParamResolver.resolve(
    func=MockController.get_user,
    request=None,
    url_params={'id': '42'},
    query_params={'verbose': 'true'}
)
print(f"  解析结果: {result}")
print(f"  id 类型: {type(result['id'])}, 值: {result['id']}")
print(f"  verbose 类型: {type(result['verbose'])}, 值: {result['verbose']}")

print()
print("=== 所有测试完成 ===")

