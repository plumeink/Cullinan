# -*- coding: utf-8 -*-
"""端到端测试：新参数系统在实际 HTTP 请求中的工作情况

Author: Plumeink
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.controller import controller, get_api, post_api
from cullinan.params import Path, Query, Body, Header, DynamicBody
from cullinan import application

@controller(url='/api')
class TestController:
    """测试控制器"""

    @post_api(url='/hello')
    def hello_dynamic(self, body: DynamicBody):
        """使用 DynamicBody"""
        name = body.get('name', 'World')
        return self.response_factory(
            status=200,
            body={"message": f"Hello, {name}!", "received": body.to_dict()}
        )

    @get_api(url='/users/{id}')
    async def get_user(self, id: Path(int), verbose: Query(bool, default=False)):
        """使用 Path 和 Query 参数"""
        return self.response_factory(
            status=200,
            body={"id": id, "verbose": verbose, "id_type": str(type(id).__name__)}
        )

    @post_api(url='/typed')
    async def typed_create(self, name: Body(str, required=True), age: Body(int, default=0)):
        """使用类型化 Body 参数"""
        return self.response_factory(
            status=200,
            body={"name": name, "age": age, "name_type": str(type(name).__name__), "age_type": str(type(age).__name__)}
        )

    @get_api(url='/search')
    async def search(
        self,
        q: Query(str, required=True),
        page: Query(int, default=1, ge=1),
        size: Query(int, default=10, ge=1, le=100),
        active: Query(bool, default=True),
    ):
        """使用多个 Query 参数带校验"""
        return self.response_factory(
            status=200,
            body={
                "q": q,
                "page": page,
                "size": size,
                "active": active,
                "types": {
                    "q": type(q).__name__,
                    "page": type(page).__name__,
                    "size": type(size).__name__,
                    "active": type(active).__name__,
                }
            }
        )

    @get_api(url='/headers')
    async def check_headers(
        self,
        auth: Header(str, alias='Authorization', required=False),
        request_id: Header(str, alias='X-Request-ID', required=False),
    ):
        """使用 Header 参数"""
        return self.response_factory(
            status=200,
            body={
                "auth": auth,
                "request_id": request_id,
            }
        )

    @post_api(url='/users/{id}')
    async def update_user(
        self,
        id: Path(int),
        name: Body(str, required=True),
        age: Body(int, default=0),
    ):
        """混合使用 Path + Body"""
        return self.response_factory(
            status=200,
            body={
                "id": id,
                "name": name,
                "age": age,
                "id_type": type(id).__name__,
            }
        )

if __name__ == '__main__':
    print("Starting test server on port 4080...")
    print("Test endpoints:")
    print("  POST /api/hello              - DynamicBody test")
    print("  GET  /api/users/{id}         - Path + Query test")
    print("  POST /api/typed              - Typed Body test")
    print("  GET  /api/search             - Multiple Query with validation")
    print("  GET  /api/headers            - Header test")
    print("  POST /api/users/{id}         - Mixed Path + Body test")
    print()
    print("Example curl commands:")
    print('  curl -X POST http://localhost:4080/api/hello -H "Content-Type: application/json" -d \'{"name":"Cullinan"}\'')
    print('  curl http://localhost:4080/api/users/42?verbose=true')
    print('  curl -X POST http://localhost:4080/api/typed -H "Content-Type: application/json" -d \'{"name":"Test","age":25}\'')
    print('  curl "http://localhost:4080/api/search?q=hello&page=2&size=20&active=false"')
    print('  curl http://localhost:4080/api/headers -H "Authorization: Bearer token" -H "X-Request-ID: req-123"')
    print('  curl -X POST http://localhost:4080/api/users/42 -H "Content-Type: application/json" -d \'{"name":"Updated","age":30}\'')
    print()
    application.run()

