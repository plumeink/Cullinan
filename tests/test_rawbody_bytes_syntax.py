# -*- coding: utf-8 -*-
"""测试 bytes = RawBody() 语法"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.params import ParamResolver, RawBody, Header, DynamicBody

def handle_webhook(
    self,
    sign: str = Header(alias='X-Hub-Signature-256', required=True),
    event: str = Header(alias='X-GitHub-Event', required=True),
    request_body: bytes = RawBody(),
):
    pass

def handle_body(
    self,
    name: str = Header(alias='X-Name'),
    body: dict = DynamicBody(),
):
    pass

print("=" * 60)
print("测试 bytes = RawBody() 和 dict = DynamicBody() 语法")
print("=" * 60)

print("\n1. 测试 bytes = RawBody():")
config = ParamResolver.analyze_params(handle_webhook)
for name, cfg in config.items():
    print(f"  {name}: source={cfg['source']}, type={cfg['type'].__name__}, required={cfg['required']}")

print("\n2. 测试 dict = DynamicBody():")
config2 = ParamResolver.analyze_params(handle_body)
for name, cfg in config2.items():
    print(f"  {name}: source={cfg['source']}, type={cfg['type'].__name__ if hasattr(cfg['type'], '__name__') else cfg['type']}, required={cfg['required']}")

# 验证
assert config['request_body']['source'] == 'raw_body', f"Expected raw_body, got {config['request_body']['source']}"
assert config['request_body']['type'] == bytes, f"Expected bytes, got {config['request_body']['type']}"

# 测试实际解析
print("\n3. 测试实际请求解析:")

class MockRequest:
    body = b'{"action": "push"}'

resolved = ParamResolver.resolve(
    func=handle_webhook,
    request=MockRequest(),
    url_params={},
    query_params={},
    body_data={},
    headers={'X-Hub-Signature-256': 'sha256=abc', 'X-Github-Event': 'push'},
    files={},
)

print(f"  sign = {resolved['sign']}")
print(f"  event = {resolved['event']}")
print(f"  request_body = {resolved['request_body']}")
print(f"  request_body type = {type(resolved['request_body'])}")

assert resolved['request_body'] == b'{"action": "push"}', f"Expected body bytes"
assert isinstance(resolved['request_body'], bytes), "request_body should be bytes"

print("\n" + "=" * 60)
print("所有测试通过!")
print("=" * 60)

