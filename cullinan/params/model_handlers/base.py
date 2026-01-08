# -*- coding: utf-8 -*-
"""Cullinan Model Handler Base

模型处理器基类，定义可插拔的模型解析接口。

Author: Plumeink
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type


class ModelHandler(ABC):
    """模型处理器基类

    所有模型处理器（如 dataclass、Pydantic、attrs 等）都需要继承此类。

    处理器通过注册表管理，核心代码不直接依赖具体实现。

    Attributes:
        priority: 优先级，数值越大越先匹配（默认 0）
        name: 处理器名称
    """

    priority: int = 0
    name: str = "base"

    @abstractmethod
    def can_handle(self, type_: Type) -> bool:
        """检查是否能处理该类型

        Args:
            type_: 类型

        Returns:
            True 如果能处理
        """
        pass

    @abstractmethod
    def resolve(self, model_class: Type, data: Dict[str, Any]) -> Any:
        """解析数据为模型实例

        Args:
            model_class: 模型类
            data: 请求数据字典

        Returns:
            模型实例

        Raises:
            ModelHandlerError: 解析失败
        """
        pass

    @abstractmethod
    def to_dict(self, instance: Any) -> Dict[str, Any]:
        """将模型实例转换为字典

        Args:
            instance: 模型实例

        Returns:
            字典
        """
        pass

    def get_source(self) -> str:
        """获取参数来源

        默认返回 'body'，子类可覆盖。

        Returns:
            参数来源字符串
        """
        return 'body'

    def is_required_by_default(self) -> bool:
        """默认是否必填

        Returns:
            True 如果默认必填
        """
        return True


class ModelHandlerError(Exception):
    """模型处理器错误

    Attributes:
        message: 错误消息
        model_class: 模型类
        errors: 错误详情列表
        handler_name: 处理器名称
    """

    def __init__(
        self,
        message: str,
        model_class: Type = None,
        errors: list = None,
        handler_name: str = None,
    ):
        super().__init__(message)
        self.message = message
        self.model_class = model_class
        self.errors = errors or []
        self.handler_name = handler_name

    def __repr__(self) -> str:
        return f"ModelHandlerError({self.message!r}, handler={self.handler_name})"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'message': self.message,
            'model': self.model_class.__name__ if self.model_class else None,
            'errors': self.errors,
            'handler': self.handler_name,
        }

