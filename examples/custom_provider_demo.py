# -*- coding: utf-8 -*-
"""示例：自定义依赖注入 Provider

演示如何创建自定义的依赖注入 Provider，包括：
- 自定义 Scope（作用域）
- 工厂模式 Provider
- 配置驱动的 Provider
- 条件性依赖注入

Author: Plumeink
"""

import logging
from typing import Any, Optional, Callable
from cullinan.service import service, Service
from cullinan.controller import controller, get_api
from cullinan.core import Inject
from cullinan.core.provider import Provider, ScopedProvider
from cullinan.core.scope import Scope, get_request_scope
from cullinan.core.injection import get_injection_registry

logger = logging.getLogger(__name__)


# ============================================================================
# 示例 1：自定义 Scope - Session Scope
# ============================================================================

class SessionScope(Scope):
    """会话级作用域

    在同一个会话中，依赖只创建一次。
    适用于：用户会话数据、购物车等。
    """

    def __init__(self):
        super().__init__('session')
        self._instances = {}  # {session_id: {key: instance}}

    def get(self, key: str) -> Optional[Any]:
        """获取会话级实例"""
        session_id = self._get_current_session_id()
        if session_id and session_id in self._instances:
            return self._instances[session_id].get(key)
        return None

    def set(self, key: str, value: Any) -> None:
        """设置会话级实例"""
        session_id = self._get_current_session_id()
        if session_id:
            if session_id not in self._instances:
                self._instances[session_id] = {}
            self._instances[session_id][key] = value

    def clear(self) -> None:
        """清理当前会话"""
        session_id = self._get_current_session_id()
        if session_id and session_id in self._instances:
            del self._instances[session_id]

    def _get_current_session_id(self) -> Optional[str]:
        """获取当前会话 ID（从请求上下文）"""
        from cullinan.core.context import get_current_context
        try:
            context = get_current_context()
            return context.get('session_id')
        except:
            return None


# 创建全局的 Session Scope 实例
_session_scope = SessionScope()

def get_session_scope() -> SessionScope:
    """获取 Session Scope 单例"""
    return _session_scope


# ============================================================================
# 示例 2：工厂模式 Provider
# ============================================================================

class FactoryProvider(Provider):
    """工厂模式 Provider

    每次都调用工厂函数创建新实例。
    适用于：需要频繁创建的对象、带参数的构造等。
    """

    def __init__(self, factory: Callable[[], Any], name: str):
        """
        Args:
            factory: 工厂函数，返回实例
            name: Provider 名称
        """
        self.factory = factory
        self.name = name

    def get(self, key: str) -> Optional[Any]:
        """每次调用工厂函数创建新实例"""
        try:
            instance = self.factory()
            logger.debug(f"FactoryProvider created instance for: {key}")
            return instance
        except Exception as e:
            logger.error(f"Factory failed for {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """工厂模式不支持 set"""
        pass


# ============================================================================
# 示例 3：配置驱动的 Provider
# ============================================================================

class ConfigProvider(Provider):
    """配置驱动的 Provider

    根据配置动态选择实例。
    适用于：环境相关的服务（开发/生产）、特性开关等。
    """

    def __init__(self, config: dict, name: str):
        """
        Args:
            config: 配置字典，格式：{key: instance}
            name: Provider 名称
        """
        self.config = config
        self.name = name
        self.current_env = self._detect_environment()

    def get(self, key: str) -> Optional[Any]:
        """根据配置返回实例"""
        env_key = f"{key}_{self.current_env}"
        if env_key in self.config:
            return self.config[env_key]
        return self.config.get(key)

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config[key] = value

    def _detect_environment(self) -> str:
        """检测当前环境"""
        import os
        return os.getenv('APP_ENV', 'development')


# ============================================================================
# 示例 4：延迟初始化 Provider
# ============================================================================

class LazyProvider(Provider):
    """延迟初始化 Provider

    只在第一次访问时创建实例，然后缓存。
    适用于：初始化开销大的服务、数据库连接等。
    """

    def __init__(self, factory: Callable[[], Any], name: str):
        """
        Args:
            factory: 工厂函数，返回实例
            name: Provider 名称
        """
        self.factory = factory
        self.name = name
        self._instance = None
        self._initialized = False

    def get(self, key: str) -> Optional[Any]:
        """延迟创建实例"""
        if not self._initialized:
            try:
                self._instance = self.factory()
                self._initialized = True
                logger.info(f"LazyProvider initialized instance for: {key}")
            except Exception as e:
                logger.error(f"Lazy initialization failed for {key}: {e}")
                return None
        return self._instance

    def set(self, key: str, value: Any) -> None:
        """重置实例"""
        self._instance = value
        self._initialized = True


# ============================================================================
# 使用示例
# ============================================================================

# 示例 1：使用 Session Scope
class ShoppingCart:
    """购物车（会话级）"""
    def __init__(self):
        self.items = []
        logger.info("ShoppingCart created")

    def add_item(self, item: str):
        self.items.append(item)

    def get_items(self):
        return self.items


# 示例 2：使用 Factory Provider
class RequestLogger:
    """请求日志记录器（每次新建）"""
    def __init__(self):
        import uuid
        self.request_id = uuid.uuid4().hex[:8]
        logger.info(f"RequestLogger created: {self.request_id}")

    def log(self, message: str):
        logger.info(f"[{self.request_id}] {message}")


# 示例 3：使用 Config Provider
class DatabaseConnection:
    """数据库连接（环境相关）"""
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        logger.info(f"Database connection: {host}:{port}")

    def query(self, sql: str):
        return f"[{self.host}] Executing: {sql}"


# 示例 4：使用 Lazy Provider
class HeavyService:
    """重型服务（延迟初始化）"""
    def __init__(self):
        import time
        logger.info("HeavyService initializing... (simulating 2s delay)")
        time.sleep(2)
        logger.info("HeavyService initialized")
        self.data = "Heavy data loaded"

    def process(self):
        return f"Processing: {self.data}"


# ============================================================================
# 集成到应用
# ============================================================================

@service
class CustomProviderDemoService(Service):
    """演示自定义 Provider 的服务"""

    def on_init(self):
        """注册自定义 Providers"""
        logger.info("Registering custom providers...")

        registry = get_injection_registry()

        # 1. 注册 Session Scope Provider
        session_provider = ScopedProvider(
            factory=lambda: ShoppingCart(),
            scope=get_session_scope(),
            name='ShoppingCartProvider'
        )
        registry.register_provider('ShoppingCart', session_provider)

        # 2. 注册 Factory Provider
        factory_provider = FactoryProvider(
            factory=lambda: RequestLogger(),
            name='RequestLoggerFactory'
        )
        registry.register_provider('RequestLogger', factory_provider)

        # 3. 注册 Config Provider（环境相关）
        dev_db = DatabaseConnection('localhost', 5432)
        prod_db = DatabaseConnection('prod-server.com', 5432)

        config_provider = ConfigProvider(
            config={
                'DatabaseConnection': dev_db,
                'DatabaseConnection_development': dev_db,
                'DatabaseConnection_production': prod_db,
            },
            name='DatabaseConfigProvider'
        )
        registry.register_provider('DatabaseConnection', config_provider)

        # 4. 注册 Lazy Provider
        lazy_provider = LazyProvider(
            factory=lambda: HeavyService(),
            name='HeavyServiceLazyProvider'
        )
        registry.register_provider('HeavyService', lazy_provider)

        logger.info("Custom providers registered successfully")


@controller('/demo/providers')
class ProviderDemoController:
    """演示自定义 Provider 的控制器"""

    # 注入自定义 Provider 提供的依赖
    shopping_cart: 'ShoppingCart' = Inject()
    request_logger: 'RequestLogger' = Inject()
    db_connection: 'DatabaseConnection' = Inject()
    heavy_service: 'HeavyService' = Inject()

    @get_api('/cart')
    def test_session_scope(self):
        """测试 Session Scope"""
        # 设置会话 ID（实际应用中从 Cookie/Header 获取）
        from cullinan.core.context import get_current_context
        context = get_current_context()
        session_id = self.get_argument('session_id', '12345')
        context.set('session_id', session_id)

        # 添加商品到购物车
        item = self.get_argument('item', 'Apple')
        self.shopping_cart.add_item(item)

        return {
            'session_id': session_id,
            'cart': self.shopping_cart.get_items(),
            'message': 'Item added to cart (session scope)'
        }

    @get_api('/log')
    def test_factory_provider(self):
        """测试 Factory Provider"""
        # 每次请求创建新的 RequestLogger
        self.request_logger.log("This is a test message")

        return {
            'request_id': self.request_logger.request_id,
            'message': 'New logger instance created per request'
        }

    @get_api('/db')
    def test_config_provider(self):
        """测试 Config Provider"""
        result = self.db_connection.query("SELECT * FROM users")

        return {
            'host': self.db_connection.host,
            'port': self.db_connection.port,
            'query_result': result,
            'message': 'Database connection from config'
        }

    @get_api('/heavy')
    def test_lazy_provider(self):
        """测试 Lazy Provider"""
        # 第一次访问时才初始化（会有 2 秒延迟）
        # 后续访问直接使用缓存实例
        result = self.heavy_service.process()

        return {
            'result': result,
            'message': 'Heavy service (lazy initialized)'
        }


if __name__ == '__main__':
    """运行示例应用"""
    from cullinan import configure, run

    print("=" * 70)
    print("自定义依赖注入 Provider 示例")
    print("=" * 70)
    print("\n自定义 Providers：")
    print("  1. SessionScope - 会话级作用域")
    print("  2. FactoryProvider - 工厂模式（每次新建）")
    print("  3. ConfigProvider - 配置驱动（环境相关）")
    print("  4. LazyProvider - 延迟初始化（首次访问时创建）")
    print("\n测试命令：")
    print("  # 测试 Session Scope（相同 session_id 共享购物车）")
    print("  curl 'http://localhost:8080/demo/providers/cart?session_id=user1&item=Apple'")
    print("  curl 'http://localhost:8080/demo/providers/cart?session_id=user1&item=Banana'")
    print("  curl 'http://localhost:8080/demo/providers/cart?session_id=user2&item=Orange'")
    print("\n  # 测试 Factory Provider（每次新建 RequestLogger）")
    print("  curl http://localhost:8080/demo/providers/log")
    print("  curl http://localhost:8080/demo/providers/log")
    print("\n  # 测试 Config Provider（环境相关数据库）")
    print("  curl http://localhost:8080/demo/providers/db")
    print("\n  # 测试 Lazy Provider（首次访问有延迟）")
    print("  curl http://localhost:8080/demo/providers/heavy")
    print("  curl http://localhost:8080/demo/providers/heavy  # 第二次无延迟")
    print("=" * 70)
    print()

    configure(
        port=8080,
        debug=True
    )

    run()

