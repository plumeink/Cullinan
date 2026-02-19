# -*- coding: utf-8 -*-
"""Service registry for Cullinan framework.

使用 cullinan.core 的 IoC/DI 2.0 系统。

架构设计：
- ServiceRegistry 存储服务类定义
- ApplicationContext 负责依赖注入和统一生命周期管理
- 所有生命周期钩子由 ApplicationContext 统一调用

Performance optimizations:
- Fast O(1) service lookup with direct dict access
- Lazy metadata initialization
- Memory-efficient with __slots__
- Singleton instance caching
"""

from typing import Type, Optional, List, Dict, Any
import logging
import threading

from cullinan.core import Registry
from cullinan.core.exceptions import RegistryError, DependencyResolutionError
from cullinan.core.provider_source import ProviderSource
from .base import Service

logger = logging.getLogger(__name__)


class ServiceRegistry(Registry[Type[Service]], ProviderSource):
    """服务注册表

    职责：
    1. 存储服务类定义
    2. 创建和缓存服务单例实例
    3. 作为 ProviderSource 提供服务实例查询

    注意：生命周期管理已移至 ApplicationContext，本类不再负责调用
    on_post_construct/on_startup/on_shutdown/on_pre_destroy 等方法。

    Usage:
        # 通过 @service 装饰器自动注册（推荐）
        @service
        class EmailService(Service):
            pass

        # 或者手动注册
        registry = get_service_registry()
        registry.register('EmailService', EmailService)

        # 获取服务实例
        email_service = registry.get_instance('EmailService')
    """
    
    __slots__ = ('_instances', '_instance_lock', '_priority')

    def __init__(self, priority: int = 10, auto_register: bool = True):
        """初始化服务注册表

        Args:
            priority: ProviderSource 优先级（默认 10）
            auto_register: 是否自动注册（默认 True）
        """
        super().__init__()

        # 服务实例缓存 (O(1) lookup)
        self._instances: Dict[str, Service] = {}

        # 线程锁（确保单例的线程安全）
        self._instance_lock = threading.RLock()

        # ProviderSource 优先级
        self._priority = priority

        if auto_register:
            logger.debug(f"ServiceRegistry initialized (priority={self._priority})")

    def register(self, name: str, service_class: Type[Service],
                 dependencies: Optional[List[str]] = None, **metadata) -> None:
        """注册服务类（O(1) 操作）

        Args:
            name: 服务唯一标识符（通常是类名）
            service_class: 服务类（不是实例）
            dependencies: 依赖的服务名称列表（可选，仅用于元数据）
            **metadata: 其他元数据

        Raises:
            RegistryError: 如果名称已注册、无效或注册表已冻结
        """
        self._check_frozen()
        self._validate_name(name)

        if name in self._items:
            logger.warning(f"Service already registered: {name}")
            return

        self._items[name] = service_class

        if dependencies or metadata:
            if self._metadata is None:
                self._metadata = {}
            meta = metadata.copy()
            meta['dependencies'] = dependencies or []
            self._metadata[name] = meta

        logger.debug(f"Registered service class: {name}")

    def get(self, name: str) -> Optional[Type[Service]]:
        """Get the service class (not instance) by name (O(1) operation).

        Args:
            name: Service identifier

        Returns:
            Service class, or None if not found
        """
        return self._items.get(name)

    def get_instance(self, name: str) -> Optional[Service]:
        """获取或创建服务实例（O(1) 缓存查找，线程安全）

        通过 ApplicationContext 创建实例，由 ApplicationContext 管理生命周期。

        Args:
            name: 服务标识符

        Returns:
            服务实例，如果未找到则返回 None

        Raises:
            DependencyResolutionError: 如果依赖无法解析
        """
        instance = self._instances.get(name)
        if instance is not None:
            return instance

        if name not in self._items:
            logger.debug(f"Service not found: {name}")
            return None

        with self._instance_lock:
            instance = self._instances.get(name)
            if instance is not None:
                return instance

            try:
                service_class = self._items[name]

                # 通过 ApplicationContext 创建实例
                from cullinan.core import get_application_context
                ctx = get_application_context()

                if ctx is not None and ctx.is_refreshed:
                    instance = ctx._create_class_instance(service_class)
                else:
                    instance = service_class()

                self._instances[name] = instance
                logger.debug(f"Created service instance: {name}")
                return instance

            except Exception as e:
                logger.error(f"Failed to instantiate service {name}: {e}", exc_info=True)
                raise DependencyResolutionError(f"Failed to create {name}: {e}") from e

    def clear(self) -> None:
        """清空所有服务和实例"""
        super().clear()
        self._instances.clear()
        logger.debug("Cleared service registry")

    def list_instances(self) -> Dict[str, Service]:
        """Get all service instances that have been created.

        Returns:
            Dictionary mapping service names to instances
        """
        return self._instances.copy()

    def has_instance(self, name: str) -> bool:
        """Check if a service instance has been created.

        Args:
            name: Service identifier

        Returns:
            True if instance exists, False otherwise
        """
        return name in self._instances

    # ========================================================================
    # ProviderSource Interface Implementation
    # ========================================================================

    def can_provide(self, name: str) -> bool:
        """检查是否能提供指定名称的服务"""
        return self.has(name)

    def provide(self, name: str) -> Optional[Service]:
        """提供指定名称的服务实例"""
        return self.get_instance(name)

    def list_available(self) -> List[str]:
        """列出所有可用的服务名称"""
        return list(self._items.keys())

    def get_priority(self) -> int:
        """获取此 ProviderSource 的优先级"""
        return self._priority


# Global service registry instance
_global_service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return _global_service_registry


def reset_service_registry() -> None:
    """Reset the global service registry."""
    _global_service_registry.clear()
    logger.debug("Reset global service registry")
