# -*- coding: utf-8 -*-
"""示例：统一的依赖解析接口（IoC Facade）

演示如何使用新的 IoC Facade 简化依赖解析，
无需直接与三层注册表（ProviderRegistry、InjectionRegistry、ServiceRegistry）交互。

Author: Plumeink
"""

import logging
from cullinan import configure, run
from cullinan.service import service, Service
from cullinan.controller import controller, get_api
from cullinan.core import Inject

# 新的统一接口
from cullinan.core.facade import (
    get_ioc_facade,
    resolve_dependency,
    resolve_dependency_by_name,
    has_dependency
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 定义服务层
# ============================================================================

@service
class DatabaseService(Service):
    """数据库服务"""

    def on_init(self):
        logger.info("Database service initialized")
        self.data = {
            1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
            2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
        }

    def get_user(self, user_id: int):
        return self.data.get(user_id)

    def get_all_users(self):
        return list(self.data.values())


@service
class EmailService(Service):
    """邮件服务"""

    def send_email(self, to: str, subject: str, body: str):
        logger.info(f"Sending email to {to}: {subject}")
        return f"Email sent to {to}"


@service
class UserService(Service):
    """用户服务（使用传统注入方式）"""

    # 传统方式：使用 Inject() 装饰器
    db_service: 'DatabaseService' = Inject()
    email_service: 'EmailService' = Inject()

    def get_user(self, user_id: int):
        return self.db_service.get_user(user_id)

    def notify_user(self, user_id: int, message: str):
        user = self.get_user(user_id)
        if user:
            self.email_service.send_email(
                to=user['email'],
                subject="Notification",
                body=message
            )
            return f"Notified {user['name']}"
        return "User not found"


# ============================================================================
# 控制器层 - 演示新的 Facade 用法
# ============================================================================

@controller('/api/users')
class UserController:
    """用户控制器

    演示如何在控制器中使用 IoC Facade 手动解析依赖。
    这在某些场景下很有用（条件性依赖、可选依赖等）。
    """

    # 仍然可以使用传统注入
    user_service: 'UserService' = Inject()

    @get_api('/')
    def list_users(self):
        """列出所有用户（使用传统注入）"""
        db_service = self.user_service.db_service
        users = db_service.get_all_users()

        return {
            'users': users,
            'count': len(users),
            'method': 'traditional_injection'
        }

    @get_api('/<user_id>')
    def get_user(self, user_id: int):
        """获取单个用户（使用 Facade）"""
        # 方式1：使用便捷函数
        db_service = resolve_dependency(DatabaseService)
        user = db_service.get_user(user_id)

        if not user:
            self.set_status(404)
            return {'error': 'User not found'}

        return {
            'user': user,
            'method': 'facade_convenience_function'
        }

    @get_api('/<user_id>/notify')
    def notify_user(self, user_id: int):
        """通知用户（使用 Facade 按名称解析）"""
        # 方式2：按名称解析
        user_service = resolve_dependency_by_name('UserService')

        message = self.get_argument('message', 'Hello!')
        result = user_service.notify_user(user_id, message)

        return {
            'result': result,
            'method': 'facade_by_name'
        }


@controller('/api/admin')
class AdminController:
    """管理员控制器

    演示如何使用 Facade 进行条件性依赖解析。
    """

    @get_api('/stats')
    def get_stats(self):
        """获取统计信息（演示可选依赖）"""
        facade = get_ioc_facade()

        stats = {
            'total_users': 0,
            'services': {},
            'optional_features': {}
        }

        # 必需依赖
        if has_dependency(DatabaseService):
            db_service = resolve_dependency(DatabaseService)
            stats['total_users'] = len(db_service.get_all_users())
            stats['services']['database'] = 'available'

        # 检查所有可用的服务
        dependencies = facade.list_available_dependencies()
        stats['services']['registered'] = dependencies
        stats['services']['count'] = len(dependencies)

        # 演示可选依赖（假设的缓存服务）
        class CacheService:
            pass

        if has_dependency(CacheService):
            stats['optional_features']['cache'] = 'enabled'
        else:
            stats['optional_features']['cache'] = 'disabled'

        return {
            'stats': stats,
            'method': 'facade_advanced'
        }

    @get_api('/dependency-tree')
    def get_dependency_tree(self):
        """查看依赖树"""
        facade = get_ioc_facade()

        dependencies = facade.list_available_dependencies()

        # 为每个依赖收集信息
        tree = {}
        for dep_name in dependencies:
            try:
                dep = facade.resolve_by_name(dep_name, required=False)
                if dep:
                    tree[dep_name] = {
                        'type': type(dep).__name__,
                        'available': True,
                        'is_service': hasattr(dep, 'on_init'),
                    }
            except Exception as e:
                tree[dep_name] = {
                    'available': False,
                    'error': str(e)
                }

        return {
            'dependencies': tree,
            'count': len(tree)
        }


# ============================================================================
# 主程序
# ============================================================================

def main():
    """运行示例应用"""
    print("=" * 70)
    print("IoC Facade 示例 - 统一的依赖解析接口")
    print("=" * 70)
    print("\n新功能：")
    print("  1. resolve_dependency(Type) - 按类型解析（推荐）")
    print("  2. resolve_dependency_by_name(name) - 按名称解析")
    print("  3. has_dependency(Type) - 检查依赖是否存在")
    print("  4. facade.list_available_dependencies() - 列出所有依赖")
    print("\n优势：")
    print("  • 简化的 API，无需了解三层注册表")
    print("  • 统一的错误处理")
    print("  • 性能优化（缓存）")
    print("  • 清晰的文档和类型提示")
    print("\n测试命令：")
    print("  # 传统注入方式")
    print("  curl http://localhost:8080/api/users/")
    print("\n  # 使用 Facade - 按类型解析")
    print("  curl http://localhost:8080/api/users/1")
    print("\n  # 使用 Facade - 按名称解析")
    print("  curl 'http://localhost:8080/api/users/1/notify?message=Welcome'")
    print("\n  # 高级用法 - 条件性依赖")
    print("  curl http://localhost:8080/api/admin/stats")
    print("\n  # 查看依赖树")
    print("  curl http://localhost:8080/api/admin/dependency-tree")
    print("=" * 70)
    print()

    # 演示：在应用启动后使用 Facade
    print("演示：应用启动后使用 IoC Facade\n")

    configure(
        port=8080,
        debug=True
    )

    # 在这里可以使用 Facade 解析依赖
    # 注意：需要在 run() 之前，因为 run() 会阻塞

    print("启动 Web 服务器...")
    run()


if __name__ == '__main__':
    main()

