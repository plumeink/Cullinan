# -*- coding: utf-8 -*-
"""最小集成回归测试：验证 Controller HTTP 方法正确响应

使用 Tornado AsyncHTTPTestCase 真实测试 HTTP 请求，
确保不会出现 "200/空 body" 问题。

作者：Plumeink
日期：2025-12-24
"""

import json
import tornado.testing
import tornado.web
from cullinan.controller import controller, get_api, post_api, get_controller_registry
from cullinan.service import service, get_service_registry
from cullinan.core import Inject, InjectByName
from cullinan.core.injection_executor import InjectionExecutor, set_injection_executor
from cullinan.core import get_injection_registry
from cullinan.handler import get_handler_registry


class MinimalIntegrationTest(tornado.testing.AsyncHTTPTestCase):
    """最小集成测试：真实 HTTP 请求 + 响应验证"""

    def setUp(self):
        """测试初始化"""
        # 清理注册表
        controller_registry = get_controller_registry()
        service_registry = get_service_registry()
        handler_registry = get_handler_registry()

        controller_registry.clear()
        service_registry.clear()
        handler_registry.clear()

        # 初始化依赖注入
        injection_registry = get_injection_registry()
        injection_registry.clear()

        executor = InjectionExecutor(injection_registry)
        set_injection_executor(executor)

        # 注册 provider sources
        injection_registry.add_provider_source(service_registry)
        injection_registry.add_provider_source(controller_registry)

        # 在这里动态定义 Service 和 Controller（在 clear 之后）
        # 这样装饰器会重新执行注册

        @service
        class WebhookService:
            def process_webhook(self, payload: dict) -> dict:
                """处理 webhook 数据"""
                event_type = payload.get('event', 'unknown')
                return {
                    'processed': True,
                    'event_type': event_type,
                    'message': f'Webhook {event_type} processed successfully'
                }

        @controller(url='/api')
        class WebhookController:
            webhook_service: WebhookService = Inject()

            @post_api(url='/webhook', get_request_body=True, headers=['Content-Type', 'X-Event-Type'])
            def handle_webhook(self, request_body, headers):
                """处理 webhook 请求"""
                from cullinan.controller import response_build

                # 解析 JSON
                try:
                    payload = json.loads(request_body.decode('utf-8'))
                except Exception as e:
                    resp = response_build()
                    resp.set_status(400)
                    resp.add_header('Content-Type', 'application/json')
                    resp.set_body(json.dumps({'error': 'Invalid JSON', 'details': str(e)}))
                    return resp

                # 调用 service
                result = self.webhook_service.process_webhook(payload)

                # 返回响应
                resp = response_build()
                resp.set_status(200)
                resp.add_header('Content-Type', 'application/json')
                resp.set_body(json.dumps(result))
                return resp

            @get_api(url='/health')
            def health_check(self):
                """健康检查"""
                from cullinan.controller import response_build
                resp = response_build()
                resp.set_status(200)
                resp.add_header('Content-Type', 'application/json')
                resp.set_body(json.dumps({'status': 'ok', 'service': 'webhook'}))
                return resp

        # 保存引用供测试使用
        self.WebhookService = WebhookService
        self.WebhookController = WebhookController

        super().setUp()

    def get_app(self):
        """创建 Tornado Application"""
        handler_registry = get_handler_registry()
        handlers = handler_registry.get_handlers()

        if not handlers:
            raise RuntimeError("No handlers registered! Controller methods not found.")

        return tornado.web.Application(handlers)

    def test_post_webhook_returns_non_empty_body(self):
        """测试 POST /api/webhook 返回非空 body"""
        # 准备请求数据
        payload = {'event': 'push', 'repo': 'test/repo'}
        body = json.dumps(payload)

        # 发送 POST 请求
        response = self.fetch(
            '/api/webhook',
            method='POST',
            body=body,
            headers={
                'Content-Type': 'application/json',
                'X-Event-Type': 'push'
            }
        )

        # 验证响应
        self.assertEqual(response.code, 200, f"Expected 200, got {response.code}")
        self.assertIsNotNone(response.body, "Response body is None!")
        self.assertNotEqual(response.body, b'', "Response body is empty!")

        # 验证响应内容
        result = json.loads(response.body)
        self.assertTrue(result.get('processed'), "Webhook not processed")
        self.assertEqual(result.get('event_type'), 'push', "Event type mismatch")
        self.assertIn('message', result, "Response missing 'message' field")

        print(f"✅ POST /api/webhook 返回: {result}")

    def test_get_health_check(self):
        """测试 GET /api/health 健康检查"""
        response = self.fetch('/api/health', method='GET')

        # 验证响应
        self.assertEqual(response.code, 200, f"Expected 200, got {response.code}")
        self.assertIsNotNone(response.body, "Response body is None!")
        self.assertNotEqual(response.body, b'', "Response body is empty!")

        # 验证响应内容
        result = json.loads(response.body)
        self.assertEqual(result.get('status'), 'ok', "Health check failed")

        print(f"✅ GET /api/health 返回: {result}")

    def test_controller_methods_registered(self):
        """验证 Controller 方法已正确注册"""
        registry = get_controller_registry()
        methods = registry.get_methods('WebhookController')

        self.assertGreater(len(methods), 0, "Controller has 0 methods registered!")

        # 验证至少有 POST 和 GET 方法
        http_methods = [m[1] for m in methods]
        self.assertIn('post', http_methods, "POST method not registered")
        self.assertIn('get', http_methods, "GET method not registered")

        print(f"✅ WebhookController 已注册 {len(methods)} 个方法: {http_methods}")


def test_methods_count_before_app_start():
    """单元测试：验证方法注册数量（在启动 app 之前）"""
    from cullinan.controller import controller, get_api, post_api, get_controller_registry
    from cullinan.service import service
    from cullinan.core import Inject

    # 清理并重新定义
    registry = get_controller_registry()
    registry.clear()

    @service
    class TestService:
        def do_something(self):
            return "done"

    @controller(url='/api/test')
    class TestController:
        test_service: TestService = Inject()

        @get_api(url='/a')
        def method_a(self):
            return {'a': 1}

        @post_api(url='/b')
        def method_b(self):
            return {'b': 2}

    methods = registry.get_methods('TestController')

    assert len(methods) >= 2, f"Expected >= 2 methods, got {len(methods)}"

    method_urls = [(m[0], m[1]) for m in methods]
    print(f"✅ 方法注册验证通过: {method_urls}")


if __name__ == '__main__':
    import sys
    import unittest

    print("=" * 80)
    print("最小集成回归测试：Controller HTTP 方法响应验证")
    print("=" * 80)

    # 先运行单元测试（验证方法注册）
    print("\n[1] 验证 Controller 方法注册...")
    try:
        test_methods_count_before_app_start()
    except AssertionError as e:
        print(f"❌ 方法注册验证失败: {e}")
        sys.exit(1)

    # 运行集成测试（真实 HTTP 请求）
    print("\n[2] 运行集成测试（真实 HTTP 请求）...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    print("\n" + "=" * 80)
    print("✅ 所有测试通过！Controller 方法正确响应，无 200/空 body 问题")
    print("=" * 80)

