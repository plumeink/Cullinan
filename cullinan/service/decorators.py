# -*- coding: utf-8 -*-
"""Service decorators for Cullinan framework.

类似 Spring 的 @Service 装饰器，统一使用 cullinan.core 的 DI 系统。

特性：
- 单一注册系统（cullinan.core.injection）
- 自动扫描类型注解并注入依赖
- 支持 Inject() 和 InjectByName() 两种注入方式
- 兼容传统 dependencies 参数（转换为元数据）
"""

from typing import Optional, List, Type
import logging

from cullinan.core.injection import injectable
from .registry import get_service_registry
from .base import Service

logger = logging.getLogger(__name__)


def service(cls: Optional[Type[Service]] = None, *, 
            dependencies: Optional[List[str]] = None):
    """类似 Spring 的 @Service 装饰器 - 注册服务到统一 DI 容器

    注册流程（类似 Spring Boot）：
    1. 使用 @injectable 标记类为可注入（扫描并注册依赖）
    2. 注册到 ServiceRegistry（提供实例给 InjectionRegistry）
    3. ServiceRegistry 作为 provider 提供服务实例

    推荐用法 - 类型注入（类似 Spring @Autowired）:
        from cullinan.core import Inject

        @service
        class UserService(Service):
            email_service: EmailService = Inject()  # 自动注入！

            def create_user(self, name):
                self.email_service.send_email(...)

    也支持字符串注入（无需 import 依赖类）:
        from cullinan.core import InjectByName

        @service
        class UserService(Service):
            email_service = InjectByName('EmailService')
            # 或者自动推断：email_service = InjectByName()  # -> EmailService

    传统方式（向后兼容，不推荐）:
        @service(dependencies=['EmailService'])
        class UserService(Service):
            def on_init(self):
                # 通过 ServiceRegistry.get_instance 手动获取
                from cullinan.service import get_service_registry
                registry = get_service_registry()
                self.email = registry.get_instance('EmailService')

    Args:
        cls: Service class (when used without arguments)
        dependencies: List of service names this service depends on (legacy, 仅用于元数据)

    Returns:
        Decorated class (registered with unified DI system)
    """
    def decorator(service_class: Type[Service]) -> Type[Service]:
        """Inner decorator that performs the registration."""

        # 1. 【核心】标记为可注入（使用 core 的 @injectable）
        #    - 扫描类的类型注解（Inject、InjectByName）
        #    - 包装 __init__，在实例化后自动注入依赖
        #    - 注册到 InjectionRegistry._metadata
        service_class = injectable(service_class)

        # 2. 注册到 ServiceRegistry（作为依赖提供者）
        #    - ServiceRegistry 已在 __init__ 中注册为 InjectionRegistry 的 provider
        #    - InjectionRegistry._resolve_dependency() 会调用 ServiceRegistry.get_instance()
        #    - 这样形成完整的 DI 链条
        registry = get_service_registry()
        registry.register(
            service_class.__name__,
            service_class,
            dependencies=dependencies  # 仅用于元数据和依赖顺序
        )
        
        logger.debug(f"Registered service to unified DI: {service_class.__name__}")
        return service_class
    
    # Support both @service and @service(dependencies=[...])
    if cls is None:
        # Called with arguments: @service(dependencies=[...])
        return decorator
    else:
        # Called without arguments: @service
        return decorator(cls)
