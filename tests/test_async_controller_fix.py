# -*- coding: utf-8 -*-
"""Test async controller support after critical fix.

验证 controller 中的 async def 方法能正确执行。
"""

import asyncio
import pytest
import tornado.web
import tornado.testing
from cullinan.controller.core import controller, get_api, post_api, response
from cullinan.core import injectable, get_injection_registry
from cullinan.service.base import Service
from cullinan.service.registry import get_service_registry
from cullinan.handler import create_handler


class AsyncTestService(Service):
    """测试用异步服务"""

    def on_init(self):
        self.data = {"initialized": True}

    async def fetch_data_async(self):
        """模拟异步数据获取"""
        await asyncio.sleep(0.01)  # 模拟 I/O 延迟
        return {"async": True, "message": "Data fetched asynchronously"}

    def fetch_data_sync(self):
        """同步数据获取"""
        return {"async": False, "message": "Data fetched synchronously"}


@controller(url='/test-async')
class AsyncTestController:
    """测试异步控制器"""

    from cullinan.core import InjectByName
    test_service = InjectByName('AsyncTestService')

    @get_api('/sync')
    def sync_method(self):
        """同步方法 - 应该继续正常工作"""
        data = self.test_service.fetch_data_sync()
        resp = response.get()
        resp.set_body({"type": "sync", "data": data})
        resp.set_status(200)
        return resp

    @get_api('/async')
    async def async_method(self):
        """异步方法 - 这是修复的关键测试点"""
        # 这个 await 在修复前永远不会执行
        data = await self.test_service.fetch_data_async()
        resp = response.get()
        resp.set_body({"type": "async", "data": data})
        resp.set_status(200)
        return resp

    @post_api('/async-with-params')
    async def async_with_params(self, body_params):
        """异步方法带参数"""
        await asyncio.sleep(0.01)
        input_data = body_params.get('input') if body_params else None
        data = await self.test_service.fetch_data_async()
        resp = response.get()
        resp.set_body({
            "type": "async_with_params",
            "input": input_data,
            "data": data
        })
        resp.set_status(200)
        return resp


class TestAsyncControllerFix(tornado.testing.AsyncHTTPTestCase):
    """测试 async controller 修复"""

    def setUp(self):
        """设置测试环境"""
        # 清理注册表
        service_registry = get_service_registry()
        service_registry.clear()
        service_registry._instances.clear()
        service_registry._initialized.clear()

        injection_registry = get_injection_registry()
        injection_registry.clear()

        # 注册服务
        from cullinan.service.decorators import service
        service_cls = service(AsyncTestService)

        # 初始化服务
        service_registry.initialize_all()

        super().setUp()

    def get_app(self):
        """创建测试应用"""
        from cullinan.handler import get_handler_registry
        handler_registry = get_handler_registry()

        # 获取注册的 handlers
        handlers = []
        for handler_data in handler_registry.list_handlers():
            handlers.append((handler_data['pattern'], handler_data['handler']))

        return tornado.web.Application(handlers)

    def test_sync_controller_method(self):
        """测试同步 controller 方法依然正常工作"""
        response = self.fetch('/test-async/sync')
        self.assertEqual(response.code, 200)

        import json
        body = json.loads(response.body)
        self.assertEqual(body['type'], 'sync')
        self.assertFalse(body['data']['async'])
        self.assertIn('message', body['data'])

    def test_async_controller_method(self):
        """测试异步 controller 方法能正确执行（关键测试）"""
        response = self.fetch('/test-async/async')
        self.assertEqual(response.code, 200)

        import json
        body = json.loads(response.body)
        self.assertEqual(body['type'], 'async')
        # 如果修复成功，这个值应该是 True（async 方法被 await 了）
        self.assertTrue(body['data']['async'])
        self.assertEqual(body['data']['message'], 'Data fetched asynchronously')

    def test_async_controller_with_params(self):
        """测试带参数的异步 controller 方法"""
        import json
        post_data = json.dumps({"input": "test_value"})
        response = self.fetch(
            '/test-async/async-with-params',
            method='POST',
            body=post_data,
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.code, 200)

        body = json.loads(response.body)
        self.assertEqual(body['type'], 'async_with_params')
        self.assertEqual(body['input'], 'test_value')
        self.assertTrue(body['data']['async'])


@pytest.mark.asyncio
async def test_async_controller_integration():
    """集成测试：验证异步调用链"""
    # 设置
    service_registry = get_service_registry()
    service_registry.clear()

    from cullinan.service.decorators import service
    service_cls = service(AsyncTestService)
    service_registry.initialize_all()

    # 获取服务实例并测试
    svc = service_registry.get_instance('AsyncTestService')
    assert svc is not None

    # 测试服务的异步方法
    result = await svc.fetch_data_async()
    assert result['async'] is True
    assert 'message' in result


if __name__ == '__main__':
    import unittest

    # 运行 Tornado 测试
    tornado.testing.unittest.main()

