# -*- coding: utf-8 -*-
"""测试 Header 和 RawBody 语法"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.params import Header, ParamResolver, RawBody

# 测试1: RawBody 不带括号（推荐，与 DynamicBody 一致）
def handle_webhook_v1(
    self,
    sign: Header(str, alias="X-Hub-Signature-256"),
    event: Header(str, alias="X-GitHub-Event"),
    raw_body: RawBody,  # 不带括号
):
    pass

# 测试2: RawBody 带括号（也支持）
def handle_webhook_v2(
    self,
    sign: Header(str, alias="X-Hub-Signature-256"),
    event: Header(str, alias="X-GitHub-Event"),
    raw_body: RawBody(),  # 带括号
):
    pass

print("=" * 60)
print("测试 Header 和 RawBody 语法")
print("=" * 60)

# Test 1: RawBody 不带括号
print("\n1. 测试 RawBody 不带括号（推荐）:")
config = ParamResolver.analyze_params(handle_webhook_v1)
assert config['raw_body']['source'] == 'raw_body', f"source 错误: {config['raw_body']['source']}"
assert config['raw_body']['type'] == bytes, f"type 错误: {config['raw_body']['type']}"
print("   raw_body: source=raw_body, type=bytes ✓")

# Test 2: RawBody 带括号
print("\n2. 测试 RawBody 带括号（也支持）:")
config = ParamResolver.analyze_params(handle_webhook_v2)
assert config['raw_body']['source'] == 'raw_body', f"source 错误: {config['raw_body']['source']}"
assert config['raw_body']['type'] == bytes, f"type 错误: {config['raw_body']['type']}"
print("   raw_body: source=raw_body, type=bytes ✓")

# Test 3: 实际解析
print("\n3. 测试实际解析:")

class MockRequest:
    body = b'{"action": "push", "ref": "refs/heads/main"}'

headers_dict = {
    'X-Hub-Signature-256': 'sha256=abc123',
    'X-Github-Event': 'push',
}

resolved = ParamResolver.resolve(
    func=handle_webhook_v1,
    request=MockRequest(),
    url_params={},
    query_params={},
    body_data={'action': 'push'},
    headers=headers_dict,
    files={},
)

print(f"   sign = {resolved.get('sign')}")
print(f"   event = {resolved.get('event')}")
print(f"   raw_body = {resolved.get('raw_body')[:30]}...")
print(f"   raw_body type = {type(resolved.get('raw_body'))}")

assert resolved.get('sign') == 'sha256=abc123'
assert resolved.get('event') == 'push'
assert resolved.get('raw_body') == b'{"action": "push", "ref": "refs/heads/main"}'
assert isinstance(resolved.get('raw_body'), bytes)

print("\n" + "=" * 60)
print("所有测试通过!")
print("=" * 60)

