# -*- coding: utf-8 -*-
"""统一的注入执行器（Task-3.3）

集中处理所有依赖注入逻辑，简化执行路径。

作者：Plumeink
"""

from typing import Any, Optional, Dict, List, Tuple, Type
import logging
import threading

from .injection_model import InjectionPoint, UnifiedInjectionMetadata
from .exceptions import RegistryError

logger = logging.getLogger(__name__)


class InjectionExecutor:
    """统一的注入执行器

    职责：
    1. 从 InjectionPoint 解析依赖
    2. 执行注入（设置属性值）
    3. 处理错误和缓存
    4. 提供统一的注入入口

    这是所有注入方式的统一执行层，替代分散的注入逻辑。

    Example:
        executor = InjectionExecutor(injection_registry)

        # 注入单个实例
        executor.inject_instance(user_controller, metadata)

        # 解析单个注入点
        value = executor.resolve_injection_point(instance, point)
    """

    __slots__ = ('_registry', '_instance_cache', '_lock')

    def __init__(self, registry):
        """初始化注入执行器

        Args:
            registry: InjectionRegistry 实例
        """
        self._registry = registry
        # 实例级缓存：{(instance_id, attr_name): value}
        self._instance_cache: Dict[Tuple[int, str], Any] = {}
        self._lock = threading.RLock()

    def inject_instance(self, instance: Any, metadata: UnifiedInjectionMetadata) -> None:
        """向实例注入所有依赖

        Args:
            instance: 要注入的实例
            metadata: 注入元数据

        Raises:
            RegistryError: 当必需的依赖找不到时
        """
        if not metadata.has_injections():
            return

        cls_name = instance.__class__.__name__
        logger.debug(f"Injecting dependencies into {cls_name} ({len(metadata)} points)")

        for point in metadata.injection_points:
            try:
                value = self.resolve_injection_point(instance, point)

                if value is None and point.required:
                    raise RegistryError(
                        f"Required dependency '{point.dependency_name}' not found "
                        f"for {cls_name}.{point.attr_name}"
                    )

                # 只在有值时设置属性（可选依赖如果不存在，不设置属性）
                if value is not None:
                    setattr(instance, point.attr_name, value)
                    logger.debug(
                        f"Injected {point.dependency_name} -> "
                        f"{cls_name}.{point.attr_name}"
                    )
            except Exception as e:
                if point.required:
                    logger.error(
                        f"Injection failed for {cls_name}.{point.attr_name}: {e}"
                    )
                    raise
                else:
                    logger.debug(
                        f"Optional dependency {point.dependency_name} injection failed, "
                        f"skipping {cls_name}.{point.attr_name}"
                    )

    def resolve_injection_point(self, instance: Any, point: InjectionPoint) -> Optional[Any]:
        """解析单个注入点

        Args:
            instance: 实例（用于缓存）
            point: 注入点

        Returns:
            依赖实例，如果无法解析则返回 None
        """
        # 检查实例已有的值（用户手动设置或之前注入的）
        # 直接检查 __dict__ 避免触发描述符导致无限递归
        if hasattr(instance, '__dict__'):
            existing_value = instance.__dict__.get(point.attr_name)
            if existing_value is not None:
                return existing_value

        # 检查缓存（实例级别）
        if point._cache_enabled:
            cache_key = (id(instance), point.attr_name)
            if cache_key in self._instance_cache:
                logger.debug(
                    f"Cache hit for {instance.__class__.__name__}.{point.attr_name}"
                )
                return self._instance_cache[cache_key]

        # 解析依赖
        value = self._resolve_dependency(point.dependency_name)

        # 缓存结果
        if value is not None and point._cache_enabled:
            cache_key = (id(instance), point.attr_name)
            with self._lock:
                self._instance_cache[cache_key] = value

        return value

    def _resolve_dependency(self, name: str) -> Optional[Any]:
        """从注册表解析依赖

        这是一个简单的委托方法，实际解析由 InjectionRegistry 完成。

        Args:
            name: 依赖名称

        Returns:
            依赖实例，如果无法解析则返回 None
        """
        return self._registry._resolve_dependency(name)

    def clear_cache(self, instance: Optional[Any] = None) -> None:
        """清空缓存

        Args:
            instance: 如果指定，只清空该实例的缓存；否则清空全部
        """
        with self._lock:
            if instance is None:
                # 清空全部
                self._instance_cache.clear()
                logger.debug("Cleared all injection cache")
            else:
                # 清空指定实例的缓存
                instance_id = id(instance)
                keys_to_remove = [
                    key for key in self._instance_cache.keys()
                    if key[0] == instance_id
                ]
                for key in keys_to_remove:
                    del self._instance_cache[key]
                logger.debug(
                    f"Cleared injection cache for {instance.__class__.__name__} "
                    f"({len(keys_to_remove)} entries)"
                )

    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            return {
                'total_cached': len(self._instance_cache),
                'instances': len(set(key[0] for key in self._instance_cache.keys()))
            }

    def __repr__(self):
        stats = self.get_cache_stats()
        return (
            f"InjectionExecutor("
            f"cached={stats['total_cached']}, "
            f"instances={stats['instances']})"
        )


# ============================================================================
# 全局单例
# ============================================================================

_executor_instance: Optional[InjectionExecutor] = None
_executor_lock = threading.RLock()


def get_injection_executor() -> InjectionExecutor:
    """获取全局注入执行器单例

    注意：必须先调用 set_injection_executor() 设置执行器。

    Returns:
        全局注入执行器实例

    Raises:
        RuntimeError: 如果执行器未初始化
    """
    global _executor_instance
    if _executor_instance is None:
        raise RuntimeError(
            "InjectionExecutor not initialized. "
            "Call set_injection_executor() first."
        )
    return _executor_instance


def set_injection_executor(executor: InjectionExecutor) -> None:
    """设置全局注入执行器单例

    Args:
        executor: 注入执行器实例
    """
    global _executor_instance
    with _executor_lock:
        _executor_instance = executor
        logger.debug("Set global InjectionExecutor instance")


def reset_injection_executor() -> None:
    """重置全局注入执行器（用于测试）"""
    global _executor_instance
    with _executor_lock:
        if _executor_instance is not None:
            _executor_instance.clear_cache()
        _executor_instance = None
        logger.debug("Reset global InjectionExecutor instance")


def has_injection_executor() -> bool:
    """检查是否已初始化执行器

    Returns:
        True 如果已初始化
    """
    return _executor_instance is not None


__all__ = [
    'InjectionExecutor',
    'get_injection_executor',
    'set_injection_executor',
    'reset_injection_executor',
    'has_injection_executor',
]

