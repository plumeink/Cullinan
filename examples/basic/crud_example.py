# -*- coding: utf-8 -*-
"""
完整的 CRUD API 示例

演示如何使用 Cullinan 构建一个完整的 RESTful API。
包括：Controller、Service、内存数据存储。

安装 Cullinan:
    # 从源码安装（开发版）
    pip install -e /path/to/Cullinan

    # 或等待 PyPI 发布后
    pip install cullinan

运行方法:
    python crud_example.py

API端点:
    GET    /api/users          - 获取所有用户
    GET    /api/users?id=1     - 获取单个用户
    POST   /api/users          - 创建用户
    PUT    /api/users?id=1     - 更新用户
    DELETE /api/users?id=1     - 删除用户
"""

from cullinan import configure, application
from cullinan.controller import controller, get_api, post_api, put_api, delete_api
from cullinan import Service, service

# 配置
configure(user_packages=['__main__'])


# =============================================================================
# 数据层（简单的内存存储）
# =============================================================================

class InMemoryUserStore:
    """内存用户存储"""

    def __init__(self):
        self.users = {
            1: {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
            2: {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'},
        }
        self.next_id = 3

    def get_all(self):
        return list(self.users.values())

    def get_by_id(self, user_id):
        return self.users.get(int(user_id))

    def create(self, name, email):
        user = {
            'id': self.next_id,
            'name': name,
            'email': email
        }
        self.users[self.next_id] = user
        self.next_id += 1
        return user

    def update(self, user_id, name=None, email=None):
        user = self.users.get(int(user_id))
        if not user:
            return None

        if name:
            user['name'] = name
        if email:
            user['email'] = email

        return user

    def delete(self, user_id):
        return self.users.pop(int(user_id), None)


# 全局存储实例
user_store = InMemoryUserStore()


# =============================================================================
# Service 层（业务逻辑）
# =============================================================================

@service
class UserService(Service):
    """用户服务"""

    def get_all_users(self):
        """获取所有用户"""
        users = user_store.get_all()
        self.response.set_body(users)
        return self.response

    def get_user(self, user_id):
        """获取单个用户"""
        user = user_store.get_by_id(user_id)

        if user:
            self.response.set_body(user)
        else:
            self.response.set_status(404)
            self.response.set_body({'error': 'User not found'})

        return self.response

    def create_user(self, name, email):
        """创建用户"""
        # 简单验证
        if not name or not email:
            self.response.set_status(400)
            self.response.set_body({'error': 'Name and email are required'})
            return self.response

        user = user_store.create(name, email)
        self.response.set_status(201)
        self.response.set_body(user)
        return self.response

    def update_user(self, user_id, name=None, email=None):
        """更新用户"""
        user = user_store.update(user_id, name, email)

        if user:
            self.response.set_body(user)
        else:
            self.response.set_status(404)
            self.response.set_body({'error': 'User not found'})

        return self.response

    def delete_user(self, user_id):
        """删除用户"""
        user = user_store.delete(user_id)

        if user:
            self.response.set_body({'message': 'User deleted', 'user': user})
        else:
            self.response.set_status(404)
            self.response.set_body({'error': 'User not found'})

        return self.response


# =============================================================================
# Controller 层（API端点）
# =============================================================================

@controller(url='/api')
class UserController:
    """用户 API 控制器"""

    @get_api(url='/users', query_params=['id'])
    def get_users(self, query_params):
        """
        获取用户
        - 无参数: 返回所有用户
        - id参数: 返回指定用户
        """
        user_id = query_params.get('id')

        if user_id:
            return self.service['UserService'].get_user(user_id)
        else:
            return self.service['UserService'].get_all_users()

    @post_api(url='/users', body_params=['name', 'email'])
    def create_user(self, body_params):
        """创建新用户"""
        return self.service['UserService'].create_user(
            body_params['name'],
            body_params['email']
        )

    @put_api(url='/users', query_params=['id'], body_params=['name', 'email'])
    def update_user(self, query_params, body_params):
        """更新用户"""
        user_id = query_params.get('id')
        if not user_id:
            return {
                'error': 'User ID is required',
                'status': 400
            }

        return self.service['UserService'].update_user(
            user_id,
            body_params.get('name'),
            body_params.get('email')
        )

    @delete_api(url='/users', query_params=['id'])
    def delete_user(self, query_params):
        """删除用户"""
        user_id = query_params.get('id')
        if not user_id:
            return {
                'error': 'User ID is required',
                'status': 400
            }

        return self.service['UserService'].delete_user(user_id)


# =============================================================================
# 应用入口
# =============================================================================

def main():
    """启动应用"""
    print("="*70)
    print("Cullinan CRUD API Example")
    print("="*70)
    print()
    print("Server starting on http://localhost:8080")
    print()
    print("Available Endpoints:")
    print("  GET    /api/users          - Get all users")
    print("  GET    /api/users?id=1     - Get user by ID")
    print("  POST   /api/users          - Create new user")
    print("  PUT    /api/users?id=1     - Update user")
    print("  DELETE /api/users?id=1     - Delete user")
    print()
    print("Example curl commands:")
    print()
    print("  # Get all users")
    print("  curl http://localhost:8080/api/users")
    print()
    print("  # Get user by ID")
    print("  curl http://localhost:8080/api/users?id=1")
    print()
    print("  # Create user")
    print("  curl -X POST http://localhost:8080/api/users \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"name\":\"Charlie\",\"email\":\"charlie@example.com\"}'")
    print()
    print("  # Update user")
    print("  curl -X PUT http://localhost:8080/api/users?id=1 \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"name\":\"Alice Updated\"}'")
    print()
    print("  # Delete user")
    print("  curl -X DELETE http://localhost:8080/api/users?id=1")
    print()
    print("="*70)
    print()

    application.run()


if __name__ == '__main__':
    main()

