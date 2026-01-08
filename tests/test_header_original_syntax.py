# -*- coding: utf-8 -*-
"""测试 Header 和 RawBody 语法"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.params import Header, ParamResolver, RawBody

def handle_webhook(
    self,
    sign: Header(str, alias="X-Hub-Signature-256"),
    event: Header(str, alias="X-GitHub-Event"),
    raw_body: RawBody(),
):
    pass

print("=" * 60)
print("测试 Header 和 RawBody 语法")
print("=" * 60)

# Test 1: 分析参数
print("\n1. 参数分析测试:")
config = ParamResolver.analyze_params(handle_webhook)
for name, cfg in config.items():
    print(f'  {name}:')
    print(f'    source={cfg["source"]}')
    print(f'    type={cfg["type"]}')
    print(f'    required={cfg["required"]}')
    if cfg.get("param_spec"):
        print(f'    alias={cfg["param_spec"].alias}')

# Test 2: 大小写不敏感匹配
print("\n2. Header 大小写不敏感匹配测试:")

# 模拟 Tornado 存储的 headers（格式化后的 key）
headers_dict = {
    'X-Hub-Signature-256': 'sha256=abc123',
    'X-Github-Event': 'push',
}

# 模拟 request 对象
class MockRequest:
    body = b'{"action": "push", "ref": "refs/heads/main"}'

resolved = ParamResolver.resolve(
    func=handle_webhook,
    request=MockRequest(),
    url_params={},
    query_params={},
    body_data={'action': 'push'},
    headers=headers_dict,
    files={},
)

print(f"  sign = {resolved.get('sign')}")
print(f"  event = {resolved.get('event')}")
print(f"  raw_body = {resolved.get('raw_body')}")
print(f"  raw_body type = {type(resolved.get('raw_body'))}")

# Verify
assert resolved.get('sign') == 'sha256=abc123', f"sign mismatch: {resolved.get('sign')}"
assert resolved.get('event') == 'push', f"event mismatch: {resolved.get('event')}"
assert resolved.get('raw_body') == b'{"action": "push", "ref": "refs/heads/main"}', f"raw_body mismatch"
assert isinstance(resolved.get('raw_body'), bytes), "raw_body should be bytes"

print("\n" + "=" * 60)
print("所有测试通过!")
print("=" * 60)

