# -*- coding: utf-8 -*-
"""Cullinan Model Handlers

可插拔的模型处理器模块。

提供统一的模型解析接口，支持 dataclass、Pydantic 等多种模型库。

Author: Plumeink
"""

from typing import Any, Dict, List, Optional, Type

from .base import ModelHandler, ModelHandlerError
from .dataclass_handler import DataclassHandler


class ModelHandlerRegistry:
    """模型处理器注册表

    管理所有已注册的模型处理器，根据类型自动选择合适的处理器。

    Features:
    - 自动发现可用处理器
    - 按优先级排序
    - 支持手动注册/注销
    - 线程安全的单例模式

    Example:
        # 获取注册表
        registry = get_model_handler_registry()

        # 获取能处理某类型的处理器
        handler = registry.get_handler(MyDataclass)
        if handler:
            instance = handler.resolve(MyDataclass, data)

        # 注册自定义处理器
        registry.register(MyCustomHandler())
    """

    def __init__(self):
        self._handlers: List[ModelHandler] = []
        self._initialized = False

    def register(self, handler: ModelHandler) -> None:
        """注册处理器

        Args:
            handler: 模型处理器实例
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
            # 按优先级降序排序
            self._handlers.sort(key=lambda h: h.priority, reverse=True)

    def unregister(self, handler: ModelHandler) -> bool:
        """注销处理器

        Args:
            handler: 模型处理器实例

        Returns:
            True 如果成功注销
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
            return True
        return False

    def unregister_by_name(self, name: str) -> bool:
        """按名称注销处理器

        Args:
            name: 处理器名称

        Returns:
            True 如果成功注销
        """
        for handler in self._handlers[:]:
            if handler.name == name:
                self._handlers.remove(handler)
                return True
        return False

    def get_handler(self, type_: Type) -> Optional[ModelHandler]:
        """获取能处理指定类型的处理器

        按优先级顺序查找，返回第一个能处理的处理器。

        Args:
            type_: 类型

        Returns:
            处理器实例，如果没有找到返回 None
        """
        self._ensure_initialized()

        for handler in self._handlers:
            try:
                if handler.can_handle(type_):
                    return handler
            except Exception:
                continue
        return None

    def can_handle(self, type_: Type) -> bool:
        """检查是否有处理器能处理指定类型

        Args:
            type_: 类型

        Returns:
            True 如果有处理器能处理
        """
        return self.get_handler(type_) is not None

    def resolve(self, model_class: Type, data: Dict[str, Any]) -> Any:
        """使用合适的处理器解析数据

        Args:
            model_class: 模型类
            data: 数据字典

        Returns:
            模型实例

        Raises:
            ModelHandlerError: 没有处理器或解析失败
        """
        handler = self.get_handler(model_class)
        if handler is None:
            raise ModelHandlerError(
                f"No handler found for {model_class}",
                model_class=model_class,
            )
        return handler.resolve(model_class, data)

    @property
    def handlers(self) -> List[ModelHandler]:
        """获取所有已注册的处理器"""
        self._ensure_initialized()
        return self._handlers.copy()

    def get_handler_names(self) -> List[str]:
        """获取所有处理器名称"""
        self._ensure_initialized()
        return [h.name for h in self._handlers]

    def _ensure_initialized(self) -> None:
        """确保已初始化"""
        if not self._initialized:
            self._auto_discover()
            self._initialized = True

    def _auto_discover(self) -> None:
        """自动发现并注册可用的处理器"""
        # 1. 注册内置的 dataclass 处理器
        self.register(DataclassHandler())

        # 2. 尝试加载 Pydantic 处理器
        try:
            from .pydantic_handler import PydanticHandler
            self.register(PydanticHandler())
        except ImportError:
            pass  # Pydantic 未安装，跳过

    def reset(self) -> None:
        """重置注册表（用于测试）"""
        self._handlers.clear()
        self._initialized = False


# 全局注册表实例
_registry: Optional[ModelHandlerRegistry] = None


def get_model_handler_registry() -> ModelHandlerRegistry:
    """获取全局模型处理器注册表

    Returns:
        ModelHandlerRegistry 实例
    """
    global _registry
    if _registry is None:
        _registry = ModelHandlerRegistry()
    return _registry


def reset_model_handler_registry() -> None:
    """重置全局注册表（用于测试）"""
    global _registry
    if _registry is not None:
        _registry.reset()
    _registry = None


# 导出
__all__ = [
    'ModelHandler',
    'ModelHandlerError',
    'ModelHandlerRegistry',
    'DataclassHandler',
    'get_model_handler_registry',
    'reset_model_handler_registry',
]

# 尝试导出 PydanticHandler（如果可用）
try:
    from .pydantic_handler import PydanticHandler
    __all__.append('PydanticHandler')
except ImportError:
    pass

