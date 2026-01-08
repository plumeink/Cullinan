# -*- coding: utf-8 -*-
"""Cullinan Response Decorators

响应模型装饰器，用于定义 API 响应模式。

Author: Plumeink
"""

from typing import Any, Type, List, Dict, Callable, Optional, Union
from functools import wraps
import dataclasses
import json


class ResponseModel:
    """响应模型定义

    Attributes:
        model: 响应模型类 (dataclass 或普通类)
        status_code: HTTP 状态码
        description: 响应描述
        content_type: 响应内容类型
    """

    __slots__ = ('model', 'status_code', 'description', 'content_type', 'headers')

    def __init__(
        self,
        model: Type = None,
        status_code: int = 200,
        description: str = '',
        content_type: str = 'application/json',
        headers: Dict[str, str] = None,
    ):
        self.model = model
        self.status_code = status_code
        self.description = description
        self.content_type = content_type
        self.headers = headers or {}

    def __repr__(self) -> str:
        return (
            f"ResponseModel(model={self.model.__name__ if self.model else None}, "
            f"status_code={self.status_code})"
        )


def Response(
    model: Type = None,
    status_code: int = 200,
    description: str = '',
    content_type: str = 'application/json',
    headers: Dict[str, str] = None,
):
    """响应模型装饰器

    用于定义 API 端点的响应模式，支持多个响应状态。

    Args:
        model: 响应模型类
        status_code: HTTP 状态码
        description: 响应描述
        content_type: 响应内容类型
        headers: 响应头

    Example:
        from dataclasses import dataclass
        from cullinan.params import Response

        @dataclass
        class UserResponse:
            id: int
            name: str
            email: str

        @dataclass
        class ErrorResponse:
            message: str
            code: int = 0

        @controller(url='/api/users')
        class UserController:
            @get_api(url='/{id}')
            @Response(model=UserResponse, status_code=200, description="User found")
            @Response(model=ErrorResponse, status_code=404, description="User not found")
            async def get_user(self, id: Path(int)):
                user = self.user_service.get(id)
                if not user:
                    return ErrorResponse(message="User not found"), 404
                return UserResponse(id=user.id, name=user.name, email=user.email)
    """
    response_model = ResponseModel(
        model=model,
        status_code=status_code,
        description=description,
        content_type=content_type,
        headers=headers,
    )

    def decorator(func: Callable) -> Callable:
        # 获取或创建响应模型列表
        if not hasattr(func, '_response_models'):
            func._response_models = []

        func._response_models.append(response_model)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # 保持响应模型列表
        wrapper._response_models = func._response_models

        return wrapper

    return decorator


def get_response_models(func: Callable) -> List[ResponseModel]:
    """获取函数的响应模型列表

    Args:
        func: 被装饰的函数

    Returns:
        ResponseModel 列表
    """
    return getattr(func, '_response_models', [])


class ResponseSerializer:
    """响应序列化器

    将响应数据序列化为 JSON 格式。
    支持 dataclass、dict、list 和基本类型。
    """

    @classmethod
    def serialize(cls, data: Any) -> Any:
        """序列化响应数据

        Args:
            data: 响应数据

        Returns:
            可 JSON 序列化的数据
        """
        if data is None:
            return None

        # dataclass
        if dataclasses.is_dataclass(data) and not isinstance(data, type):
            return cls._serialize_dataclass(data)

        # 字典
        if isinstance(data, dict):
            return {k: cls.serialize(v) for k, v in data.items()}

        # 列表/元组
        if isinstance(data, (list, tuple)):
            return [cls.serialize(item) for item in data]

        # 基本类型
        if isinstance(data, (str, int, float, bool)):
            return data

        # bytes
        if isinstance(data, bytes):
            return data.decode('utf-8', errors='replace')

        # 有 to_dict 方法
        if hasattr(data, 'to_dict') and callable(data.to_dict):
            return cls.serialize(data.to_dict())

        # 有 __dict__ 属性
        if hasattr(data, '__dict__'):
            return {k: cls.serialize(v) for k, v in data.__dict__.items()
                    if not k.startswith('_')}

        # 其他情况转字符串
        return str(data)

    @classmethod
    def _serialize_dataclass(cls, instance) -> dict:
        """序列化 dataclass 实例

        Args:
            instance: dataclass 实例

        Returns:
            字典
        """
        result = {}
        for field in dataclasses.fields(instance):
            value = getattr(instance, field.name)
            result[field.name] = cls.serialize(value)
        return result

    @classmethod
    def to_json(cls, data: Any, **kwargs) -> str:
        """序列化为 JSON 字符串

        Args:
            data: 响应数据
            **kwargs: json.dumps 的参数

        Returns:
            JSON 字符串
        """
        serialized = cls.serialize(data)
        return json.dumps(serialized, ensure_ascii=False, **kwargs)


def serialize_response(data: Any) -> Any:
    """序列化响应数据的便捷函数

    Args:
        data: 响应数据

    Returns:
        可 JSON 序列化的数据
    """
    return ResponseSerializer.serialize(data)

