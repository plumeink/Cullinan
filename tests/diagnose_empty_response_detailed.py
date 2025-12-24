# -*- coding: utf-8 -*-
"""诊断空响应问题 - 跟踪完整的调用链

Author: Plumeink
"""
import json
import asyncio
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from cullinan.controller import controller, post_api
from cullinan.handler import get_handler_registry

print("=" * 70)
print("诊断测试：跟踪 @post_api 装饰器的调用链")
print("=" * 70)

@controller(url='/api')
class DiagController:
    @post_api(url='/test', get_request_body=True)
    async def handle_test(self, request_body):
        """测试异步处理器"""
        print("🔥 handle_test 方法被调用！")
        print(f"🔥 request_body = {request_body}")

        from cullinan.controller import response_build

        result = {
            'executed': True,
            'message': 'Handler executed successfully',
            'body': request_body.decode('utf-8') if isinstance(request_body, bytes) else str(request_body)
        }

        resp = response_build()
        resp.set_status(200)
        resp.set_header('Content-Type', 'application/json')
        resp.set_body(json.dumps(result))

        print(f"🔥 返回响应: {result}")
        return resp

print("\n1. 检查handlers注册:")
registry = get_handler_registry()
handlers = registry.get_handlers()
print(f"   注册的handlers数量: {len(handlers)}")

for url, handler_class in handlers:
    print(f"\n   URL: {url}")
    print(f"   Handler类: {handler_class.__name__}")

    # 检查 post 方法
    if hasattr(handler_class, 'post'):
        post_method = getattr(handler_class, 'post')
        print(f"   - 有 post 方法")
        print(f"   - post 是协程函数: {asyncio.iscoroutinefunction(post_method)}")
        print(f"   - post 方法名: {post_method.__name__}")

        # 检查原始函数
        if hasattr(post_method, '__wrapped__'):
            print(f"   - post 有 __wrapped__: {post_method.__wrapped__}")

print("\n" + "=" * 70)
print("现在启动Tornado应用进行实际测试...")
print("=" * 70)

import tornado.web
import tornado.ioloop
import tornado.httpclient

app = tornado.web.Application(handlers=handlers)
port = 4081

from tornado.httpserver import HTTPServer
server = HTTPServer(app)
server.listen(port)

async def test_request():
    """发送测试请求"""
    await asyncio.sleep(0.5)  # 等待服务器启动

    print(f"\n发送POST请求到 http://localhost:{port}/api/test")

    client = tornado.httpclient.AsyncHTTPClient()
    try:
        response = await client.fetch(
            f'http://localhost:{port}/api/test',
            method='POST',
            body=json.dumps({'test': 'data'}),
            headers={'Content-Type': 'application/json'}
        )

        print(f"\n✅ 响应状态: {response.code}")
        print(f"✅ 响应头: {dict(response.headers)}")
        print(f"✅ 响应体: {response.body}")
        print(f"✅ 响应体长度: {len(response.body)}")

        if response.body:
            data = json.loads(response.body)
            print(f"✅ 解析的JSON: {data}")
        else:
            print("❌ 响应体为空！")

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tornado.ioloop.IOLoop.current().stop()

# 调度测试请求
tornado.ioloop.IOLoop.current().call_later(0.6, lambda: asyncio.ensure_future(test_request()))

print(f"\n服务器启动在 http://localhost:{port}")
print("执行测试...")

tornado.ioloop.IOLoop.current().start()

print("\n测试完成")

