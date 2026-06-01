# -*- coding: utf-8 -*-
"""测试原始问题场景：同步方法被 @post_api 装饰

Author: Plumeink
"""
import json
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

from cullinan.web.controller import controller, post_api, get_api
from cullinan.web.handler import get_handler_registry

print("=" * 70)
print("测试场景：同步和异步方法混合")
print("=" * 70)

@controller(url='/api')
class MixedController:
    """测试同步和异步方法"""

    @post_api(url='/sync-method', get_request_body=True)
    def sync_webhook(self, request_body):
        """同步方法 - 原始问题场景"""
        print("🔥 SYNC METHOD EXECUTED!")
        print(f"🔥 Body: {request_body}")

        from cullinan.web.controller import response_build

        result = {'sync': True, 'executed': True}
        resp = response_build()
        resp.set_status(200)
        resp.set_header('Content-Type', 'application/json')
        resp.set_body(json.dumps(result))
        print(f"🔥 Returning: {result}")
        return resp

    @post_api(url='/async-method', get_request_body=True)
    async def async_webhook(self, request_body):
        """异步方法"""
        print("🔥 ASYNC METHOD EXECUTED!")
        await asyncio.sleep(0.001)

        from cullinan.web.controller import response_build

        result = {'async': True, 'executed': True}
        resp = response_build()
        resp.set_status(200)
        resp.set_header('Content-Type', 'application/json')
        resp.set_body(json.dumps(result))
        print(f"🔥 Returning: {result}")
        return resp

    @get_api(url='/health')
    def health_check(self):
        """同步 GET 方法"""
        print("🔥 HEALTH CHECK EXECUTED!")
        from cullinan.web.controller import response_build
        resp = response_build()
        resp.set_status(200)
        resp.set_body('{"status": "ok"}')
        return resp

print("\n启动测试...")

import tornado.web
import tornado.ioloop
import tornado.httpclient

handlers = get_handler_registry().get_handlers()
app = tornado.web.Application(handlers=handlers)
port = 4082

from tornado.httpserver import HTTPServer
server = HTTPServer(app)
server.listen(port)

async def run_tests():
    """运行所有测试"""
    await asyncio.sleep(0.5)

    client = tornado.httpclient.AsyncHTTPClient()

    tests = [
        ("同步POST", "POST", "/api/sync-method", {"test": "sync"}),
        ("异步POST", "POST", "/api/async-method", {"test": "async"}),
        ("同步GET", "GET", "/api/health", None),
    ]

    for name, method, path, body in tests:
        print(f"\n{'=' * 70}")
        print(f"测试: {name}")
        print(f"{'=' * 70}")

        try:
            url = f'http://localhost:{port}{path}'
            kwargs = {'method': method}

            if body is not None:
                kwargs['body'] = json.dumps(body)
                kwargs['headers'] = {'Content-Type': 'application/json'}

            response = await client.fetch(url, **kwargs)

            print(f"✅ 状态: {response.code}")
            print(f"✅ 响应体: {response.body}")
            print(f"✅ 响应体长度: {len(response.body)}")

            if response.body:
                try:
                    data = json.loads(response.body)
                    print(f"✅ 解析JSON: {data}")
                except:
                    print(f"✅ 原始内容: {response.body.decode('utf-8')}")
            else:
                print("❌ 响应体为空！")

        except Exception as e:
            print(f"❌ 失败: {e}")
            import traceback
            traceback.print_exc()

    tornado.ioloop.IOLoop.current().stop()

tornado.ioloop.IOLoop.current().call_later(0.6, lambda: asyncio.ensure_future(run_tests()))

print(f"\n服务器在 http://localhost:{port}")
tornado.ioloop.IOLoop.current().start()

print("\n所有测试完成！")

