# -*- coding: utf-8 -*-
"""Tests for OpenAPI 3.0 auto-generation."""
import asyncio
import inspect
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.gateway import Router, CullinanRequest, CullinanResponse, Dispatcher
from cullinan.gateway.openapi import OpenAPIGenerator

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")


async def main():
    print("=" * 60)
    print("OpenAPI Generator Tests")
    print("=" * 60)

    # ====================================================================
    # 1. Basic spec generation
    # ====================================================================
    print("\n--- 1. Basic spec ---")
    router = Router()

    async def list_users(request):
        """List all users.

        Returns a paginated list of user objects.
        """
        return CullinanResponse.json({"users": []})

    async def get_user(request):
        """Get a single user by ID."""
        return CullinanResponse.json({})

    async def create_user(request):
        """Create a new user."""
        return CullinanResponse.json({}, status_code=201)

    router.add_route('GET', '/api/users', handler=list_users)
    router.add_route('GET', '/api/users/{id}', handler=get_user)
    router.add_route('POST', '/api/users', handler=create_user)

    gen = OpenAPIGenerator(router=router, title='Test API', version='1.0.0',
                           description='Test description')
    spec = gen.to_dict()

    check("OpenAPI version", spec['openapi'] == '3.0.3')
    check("Info title", spec['info']['title'] == 'Test API')
    check("Info version", spec['info']['version'] == '1.0.0')
    check("Info description", spec['info']['description'] == 'Test description')
    check("Paths count", len(spec['paths']) == 2)  # /api/users + /api/users/{id}
    check("GET /api/users exists", 'get' in spec['paths'].get('/api/users', {}))
    check("POST /api/users exists", 'post' in spec['paths'].get('/api/users', {}))
    check("GET /api/users/{id} exists", 'get' in spec['paths'].get('/api/users/{id}', {}))

    # ====================================================================
    # 2. Docstring extraction
    # ====================================================================
    print("\n--- 2. Docstring extraction ---")
    op = spec['paths']['/api/users']['get']
    check("Summary from docstring", op.get('summary') == 'List all users.')
    check("Description from docstring", 'paginated' in op.get('description', ''))

    op_get_user = spec['paths']['/api/users/{id}']['get']
    check("Single-line docstring summary", op_get_user.get('summary') == 'Get a single user by ID.')

    # ====================================================================
    # 3. Path parameter detection
    # ====================================================================
    print("\n--- 3. Path params ---")
    params = op_get_user.get('parameters', [])
    check("Path param count", len(params) == 1)
    check("Path param name", params[0]['name'] == 'id')
    check("Path param in=path", params[0]['in'] == 'path')
    check("Path param required", params[0]['required'] is True)

    # ====================================================================
    # 4. Param annotation introspection
    # ====================================================================
    print("\n--- 4. Param annotations ---")
    try:
        from cullinan.params import Path, Query, Body, Header

        async def annotated_handler(
            self,
            user_id: int = Path(int, description='The user ID'),
            page: int = Query(int, default=1, ge=1, description='Page number'),
            size: int = Query(int, default=10, ge=1, le=100),
        ):
            """Get users with pagination."""
            pass

        router2 = Router()
        router2.add_route('GET', '/v2/users/{user_id}', handler=annotated_handler)

        gen2 = OpenAPIGenerator(router=router2)
        spec2 = gen2.to_dict()
        op2 = spec2['paths']['/v2/users/{user_id}']['get']
        params2 = op2.get('parameters', [])

        path_params = [p for p in params2 if p['in'] == 'path']
        query_params = [p for p in params2 if p['in'] == 'query']

        check("Annotated path param", len(path_params) >= 1)
        if path_params:
            check("Path param type int", path_params[0]['schema'].get('type') == 'integer')
            check("Path param description", path_params[0].get('description') == 'The user ID')

        check("Annotated query params", len(query_params) >= 2)
        if query_params:
            page_param = next((p for p in query_params if p['name'] == 'page'), None)
            if page_param:
                check("Query default value", page_param['schema'].get('default') == 1)
                check("Query ge constraint", page_param['schema'].get('minimum') == 1)
                check("Query description", page_param.get('description') == 'Page number')

            size_param = next((p for p in query_params if p['name'] == 'size'), None)
            if size_param:
                check("Query le constraint", size_param['schema'].get('maximum') == 100)

    except ImportError:
        print("  [SKIP] cullinan.params not available")

    # ====================================================================
    # 5. JSON serialization
    # ====================================================================
    print("\n--- 5. Serialization ---")
    json_str = gen.to_json()
    check("JSON output is valid", json.loads(json_str) is not None)
    check("JSON contains openapi", '"openapi"' in json_str)

    # ====================================================================
    # 6. Spec endpoint registration
    # ====================================================================
    print("\n--- 6. Spec endpoints ---")
    gen.register_spec_routes()
    route_count_after = router.route_count()
    check("Spec routes registered", route_count_after >= 5)  # 3 original + 2 spec

    # Dispatch to /openapi.json
    dispatcher = Dispatcher(router=router)
    req = CullinanRequest(method='GET', path='/openapi.json')
    resp = await dispatcher.dispatch(req)
    check("GET /openapi.json status 200", resp.status_code == 200)
    body = resp.render_body()
    parsed = json.loads(body)
    check("Spec JSON parsable", parsed.get('openapi') == '3.0.3')
    check("Spec has paths", len(parsed.get('paths', {})) > 0)

    # ====================================================================
    # 7. Metadata overrides
    # ====================================================================
    print("\n--- 7. Metadata ---")
    router3 = Router()
    router3.add_route('GET', '/tagged', handler=list_users,
                       metadata={'tags': ['admin'], 'summary': 'Custom summary',
                                 'deprecated': True})
    gen3 = OpenAPIGenerator(router=router3)
    spec3 = gen3.to_dict()
    op3 = spec3['paths']['/tagged']['get']
    check("Metadata tags", op3.get('tags') == ['admin'])
    check("Metadata summary override", op3.get('summary') == 'Custom summary')
    check("Metadata deprecated", op3.get('deprecated') is True)

    # ====================================================================
    # 8. Controller tag inference
    # ====================================================================
    print("\n--- 8. Controller tag ---")
    class UserController:
        pass
    router4 = Router()
    router4.add_route('GET', '/ctrl', handler=list_users, controller_cls=UserController)
    gen4 = OpenAPIGenerator(router=router4)
    spec4 = gen4.to_dict()
    op4 = spec4['paths']['/ctrl']['get']
    check("Controller tag inferred", op4.get('tags') == ['User'])

    # ====================================================================
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")
    return failed == 0


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

