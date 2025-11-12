# -*- coding: utf-8 -*-
"""Enhanced service module for Cullinan framework.

This module provides an enhanced service layer with:
- Base Service class with lifecycle hooks (on_init, on_destroy)
- ServiceRegistry for managing services with dependency injection
- @service decorator for easy service registration
- Full backward compatibility with simple service usage

服务层使用 core 提供的通用 IoC 能力，不与 core 耦合。

Usage:
    # 方式1: 简单服务（向后兼容）
    from cullinan.service import service, Service

    @service
    class EmailService(Service):
        def send_email(self, to, subject, body):
            print(f"Sending to {to}: {subject}")
    
    # 方式2: 使用依赖注入（推荐，无需 import）
    from cullinan.core import InjectByName

    @service
    class UserService(Service):
        email_service = InjectByName('EmailService')  # 自动注入，无需 import EmailService

        def create_user(self, name):
            user = {'name': name}
            self.email_service.send_email(name, "Welcome", "Welcome!")
            return user

    # 方式3: 传统依赖方式（向后兼容）
    @service(dependencies=['EmailService'])
    class UserService(Service):
        def on_init(self):
            self.email = self.dependencies['EmailService']
"""

from .base import Service
from .decorators import service
from .registry import (
    ServiceRegistry,
    get_service_registry,
    reset_service_registry
)

# Re-export core's injection utilities for convenience
# 为了方便使用，re-export core 的注入工具（但不产生耦合）
from cullinan.core import Inject, InjectByName, injectable

__all__ = [
    'Service',
    'service',
    'ServiceRegistry',
    'get_service_registry',
    'reset_service_registry',
    # Injection utilities from core
    'Inject',
    'InjectByName',
    'injectable',
]
