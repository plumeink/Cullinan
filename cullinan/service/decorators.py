# -*- coding: utf-8 -*-
"""Service decorators for Cullinan framework.

Provides the @service decorator for registering services with optional
dependency injection support.

支持两种依赖注入方式：
1. 传统方式：dependencies 参数 + self.dependencies 字典
2. 类型注入：使用 Inject 标记 + 类型注解（推荐）
"""

from typing import Optional, List, Type
import logging

from cullinan.core.injection import injectable  # 使用 core 的注入系统
from .registry import get_service_registry
from .base import Service

logger = logging.getLogger(__name__)


def service(cls: Optional[Type[Service]] = None, *, 
            dependencies: Optional[List[str]] = None):
    """Decorator for registering service classes.
    
    支持两种依赖注入方式：

    方式1 - 类型注入（推荐，使用 core.Inject）:
        from cullinan.core import Inject

        @service
        class UserService(Service):
            email: EmailService = Inject()  # 自动注入！

            def create_user(self, name):
                self.email.send_email(...)

    方式2 - 传统方式（向后兼容）:
        @service(dependencies=['EmailService'])
        class UserService(Service):
            def on_init(self):
                self.email = self.dependencies['EmailService']
    
    Args:
        cls: Service class (when used without arguments)
        dependencies: List of service names this service depends on (legacy)

    Returns:
        Decorated class (registered with global service registry)
    """
    def decorator(service_class: Type[Service]) -> Type[Service]:
        """Inner decorator that performs the registration."""

        # 1. 标记为可注入（使用 core 的装饰器）
        service_class = injectable(service_class)

        # 2. 注册到 ServiceRegistry
        registry = get_service_registry()
        registry.register(
            service_class.__name__,
            service_class,
            dependencies=dependencies
        )
        
        logger.debug(f"Decorated service: {service_class.__name__} (injectable)")
        return service_class
    
    # Support both @service and @service(dependencies=[...])
    if cls is None:
        # Called with arguments: @service(dependencies=[...])
        return decorator
    else:
        # Called without arguments: @service
        return decorator(cls)
