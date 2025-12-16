# -*- coding: utf-8 -*-
"""示例：自定义认证中间件

演示如何创建一个完整的认证中间件，包括：
- Token 验证
- 用户信息提取
- 权限检查
- 错误处理

Author: Plumeink
"""

import logging
from typing import Optional
from cullinan.middleware import middleware, Middleware

logger = logging.getLogger(__name__)


# ============================================================================
# 示例 1：简单的 Token 认证中间件
# ============================================================================

@middleware(priority=50)
class TokenAuthMiddleware(Middleware):
    """Token 认证中间件

    验证请求头中的 Authorization Token，并将用户信息附加到 handler。
    """

    def __init__(self):
        super().__init__()
        # 模拟用户数据库
        self.users = {
            'token123': {'id': 1, 'name': 'Alice', 'role': 'admin'},
            'token456': {'id': 2, 'name': 'Bob', 'role': 'user'},
        }

    def on_init(self):
        """初始化时执行"""
        logger.info("TokenAuthMiddleware initialized")

    def process_request(self, handler):
        """处理请求 - 验证 Token"""
        # 获取 Authorization 头
        auth_header = handler.request.headers.get('Authorization', '')

        # 提取 Token
        token = self._extract_token(auth_header)

        if token:
            # 验证 Token 并获取用户信息
            user = self.users.get(token)
            if user:
                # 将用户信息附加到 handler
                handler.current_user = user
                logger.info(f"User authenticated: {user['name']}")
                return handler  # 继续处理
            else:
                logger.warning(f"Invalid token: {token}")

        # Token 无效或缺失
        # 如果是 /api/ 路径，返回 401
        if handler.request.path.startswith('/api/'):
            handler.set_status(401)
            handler.set_header('Content-Type', 'application/json')
            handler.finish({'error': 'Unauthorized', 'message': 'Invalid or missing token'})
            return None  # 短路，不继续处理

        # 其他路径允许通过（如公开页面）
        return handler

    def process_response(self, handler, response):
        """处理响应 - 添加安全头"""
        handler.set_header('X-Auth-Method', 'Token')
        return response

    def _extract_token(self, auth_header: str) -> Optional[str]:
        """从 Authorization 头提取 Token

        支持格式：
        - Authorization: Bearer <token>
        - Authorization: Token <token>
        - Authorization: <token>
        """
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() in ('bearer', 'token'):
            return parts[1]
        elif len(parts) == 1:
            return parts[0]

        return None


# ============================================================================
# 示例 2：基于角色的权限检查中间件
# ============================================================================

@middleware(priority=60)
class RoleAuthMiddleware(Middleware):
    """角色权限检查中间件

    检查用户是否有权限访问特定路径。
    必须在 TokenAuthMiddleware 之后执行（priority > 50）。
    """

    def __init__(self):
        super().__init__()
        # 定义路径权限规则
        self.rules = {
            '/api/admin/': ['admin'],           # 仅管理员
            '/api/users/': ['admin', 'user'],   # 管理员和普通用户
        }

    def process_request(self, handler):
        """检查用户权限"""
        path = handler.request.path

        # 检查路径是否需要权限
        required_roles = self._get_required_roles(path)
        if not required_roles:
            return handler  # 不需要权限检查

        # 获取当前用户（由 TokenAuthMiddleware 设置）
        current_user = getattr(handler, 'current_user', None)
        if not current_user:
            # 没有用户信息，禁止访问
            handler.set_status(403)
            handler.set_header('Content-Type', 'application/json')
            handler.finish({'error': 'Forbidden', 'message': 'Access denied'})
            return None

        # 检查用户角色
        user_role = current_user.get('role')
        if user_role not in required_roles:
            logger.warning(
                f"User {current_user['name']} (role: {user_role}) "
                f"attempted to access {path} (requires: {required_roles})"
            )
            handler.set_status(403)
            handler.set_header('Content-Type', 'application/json')
            handler.finish({
                'error': 'Forbidden',
                'message': f'Requires role: {", ".join(required_roles)}'
            })
            return None

        # 权限验证通过
        logger.info(f"User {current_user['name']} authorized for {path}")
        return handler

    def _get_required_roles(self, path: str) -> Optional[list]:
        """获取路径所需的角色列表"""
        for rule_path, roles in self.rules.items():
            if path.startswith(rule_path):
                return roles
        return None


# ============================================================================
# 示例 3：请求速率限制中间件
# ============================================================================

@middleware(priority=40)
class RateLimitMiddleware(Middleware):
    """请求速率限制中间件

    限制每个 IP 的请求频率。
    在认证之前执行（priority < 50），节省资源。
    """

    def __init__(self):
        super().__init__()
        import time
        from collections import defaultdict

        self.requests = defaultdict(list)  # {ip: [timestamp1, timestamp2, ...]}
        self.max_requests = 10  # 最大请求数
        self.time_window = 60   # 时间窗口（秒）
        self.time = time

    def process_request(self, handler):
        """检查请求速率"""
        # 获取客户端 IP
        ip = handler.request.remote_ip

        # 清理过期记录
        self._cleanup_old_requests(ip)

        # 检查请求数量
        if len(self.requests[ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            handler.set_status(429)  # Too Many Requests
            handler.set_header('Content-Type', 'application/json')
            handler.set_header('Retry-After', str(self.time_window))
            handler.finish({
                'error': 'Too Many Requests',
                'message': f'Rate limit: {self.max_requests} requests per {self.time_window} seconds'
            })
            return None

        # 记录请求
        self.requests[ip].append(self.time.time())
        return handler

    def process_response(self, handler, response):
        """添加速率限制响应头"""
        ip = handler.request.remote_ip
        remaining = self.max_requests - len(self.requests.get(ip, []))
        handler.set_header('X-RateLimit-Limit', str(self.max_requests))
        handler.set_header('X-RateLimit-Remaining', str(max(0, remaining)))
        return response

    def _cleanup_old_requests(self, ip: str):
        """清理超过时间窗口的请求记录"""
        if ip not in self.requests:
            return

        cutoff_time = self.time.time() - self.time_window
        self.requests[ip] = [
            timestamp for timestamp in self.requests[ip]
            if timestamp > cutoff_time
        ]

        # 如果列表为空，删除该 IP 记录
        if not self.requests[ip]:
            del self.requests[ip]


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == '__main__':
    """
    完整的应用示例，演示认证中间件的使用
    """
    from cullinan import configure, run
    from cullinan.controller import controller, get_api
    from cullinan.service import service, Service
    from cullinan.core import Inject

    # 定义服务
    @service
    class UserService(Service):
        def get_all_users(self):
            return [
                {'id': 1, 'name': 'Alice'},
                {'id': 2, 'name': 'Bob'},
            ]

        def get_user(self, user_id: int):
            users = self.get_all_users()
            for user in users:
                if user['id'] == user_id:
                    return user
            return None

    # 定义控制器
    @controller('/api/users')
    class UserController:
        user_service: 'UserService' = Inject()

        @get_api('/')
        def list_users(self):
            """获取用户列表 - 需要认证"""
            current_user = getattr(self, 'current_user', None)
            return {
                'users': self.user_service.get_all_users(),
                'requested_by': current_user['name'] if current_user else 'Anonymous'
            }

        @get_api('/<user_id>')
        def get_user(self, user_id: int):
            """获取单个用户 - 需要认证"""
            user = self.user_service.get_user(user_id)
            if user:
                return user
            else:
                self.set_status(404)
                return {'error': 'User not found'}

    @controller('/api/admin')
    class AdminController:
        user_service: 'UserService' = Inject()

        @get_api('/stats')
        def get_stats(self):
            """获取统计信息 - 仅管理员"""
            return {
                'total_users': len(self.user_service.get_all_users()),
                'message': 'Admin only endpoint'
            }

    @controller('/')
    class HomeController:
        @get_api('/')
        def index(self):
            """首页 - 公开访问"""
            return {'message': 'Welcome to the API'}

    # 启动应用
    print("=" * 70)
    print("自定义认证中间件示例")
    print("=" * 70)
    print("\n中间件执行顺序（按 priority）：")
    print("  1. RateLimitMiddleware (priority=40) - 速率限制")
    print("  2. TokenAuthMiddleware (priority=50) - Token 认证")
    print("  3. RoleAuthMiddleware (priority=60) - 角色权限检查")
    print("\n测试命令：")
    print("  # 公开访问")
    print("  curl http://localhost:8080/")
    print("\n  # 未认证访问 API（401）")
    print("  curl http://localhost:8080/api/users/")
    print("\n  # 使用有效 Token（普通用户）")
    print("  curl -H 'Authorization: Bearer token456' http://localhost:8080/api/users/")
    print("\n  # 访问管理员端点（403 - 权限不足）")
    print("  curl -H 'Authorization: Bearer token456' http://localhost:8080/api/admin/stats")
    print("\n  # 使用管理员 Token")
    print("  curl -H 'Authorization: Bearer token123' http://localhost:8080/api/admin/stats")
    print("\n  # 超过速率限制（连续请求 11 次）")
    print("  for i in {1..11}; do curl http://localhost:8080/; done")
    print("=" * 70)
    print()

    configure(
        port=8080,
        debug=True
    )

    run()

