# -*- coding: utf-8 -*-
"""演示修复后的依赖注入功能

这个示例展示了如何在 Controller 中使用依赖注入来注入 Service。

作者：Plumeink
"""

from cullinan.service import Service, service
from cullinan.controller.core import controller, get_api, post_api
from cullinan.core import InjectByName
from cullinan.application import run
import json


# 定义一个 Service
@service
class GreetingService(Service):
    """问候服务"""

    def __init__(self):
        super().__init__()
        self.greeting_count = 0

    def on_init(self):
        """Service 初始化时调用"""
        print("GreetingService 已初始化")

    def get_greeting(self, name: str) -> str:
        """生成问候语"""
        self.greeting_count += 1
        return f"Hello, {name}! (#{self.greeting_count})"

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_greetings": self.greeting_count
        }


# 定义一个 Controller，使用依赖注入
@controller(url='/api')
class GreetingController:
    """问候控制器

    使用 InjectByName 注入 GreetingService，无需手动创建实例。
    """

    # 使用依赖注入 - 框架会自动注入 GreetingService 实例
    greeting_service = InjectByName('GreetingService')

    @get_api('/greet')
    def greet(self, query_params):
        """GET /api/greet?name=World

        返回问候语
        """
        name = query_params.get('name', ['Guest'])[0]

        # 直接使用注入的 service
        greeting = self.greeting_service.get_greeting(name)

        return {
            "message": greeting,
            "success": True
        }

    @get_api('/stats')
    def get_stats(self):
        """GET /api/stats

        返回统计信息
        """
        stats = self.greeting_service.get_stats()

        return {
            "stats": stats,
            "success": True
        }

    @post_api('/greet', get_request_body=True)
    def greet_post(self, request_body):
        """POST /api/greet

        Body: {"name": "World"}
        """
        try:
            data = json.loads(request_body)
            name = data.get('name', 'Guest')

            greeting = self.greeting_service.get_greeting(name)

            return {
                "message": greeting,
                "success": True
            }
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON",
                "success": False
            }


if __name__ == "__main__":
    print("=" * 80)
    print("演示：修复后的依赖注入功能")
    print("=" * 80)
    print()
    print("启动服务器后，可以测试以下接口：")
    print()
    print("1. GET  http://localhost:4080/api/greet?name=Alice")
    print("   返回: {\"message\": \"Hello, Alice! (#1)\", \"success\": true}")
    print()
    print("2. GET  http://localhost:4080/api/stats")
    print("   返回: {\"stats\": {\"total_greetings\": 1}, \"success\": true}")
    print()
    print("3. POST http://localhost:4080/api/greet")
    print("   Body: {\"name\": \"Bob\"}")
    print("   返回: {\"message\": \"Hello, Bob! (#2)\", \"success\": true}")
    print()
    print("=" * 80)
    print()

    # 使用修复后的 run() 函数启动应用
    run()

