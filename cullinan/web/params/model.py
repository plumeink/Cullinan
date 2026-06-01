# -*- coding: utf-8 -*-
"""Cullinan Model Resolver

dataclass 模型解析器，将请求数据映射到 dataclass 实例。

Author: Plumeink
"""

import dataclasses
from typing import Any, Dict, Type, get_type_hints, Union
import inspect

from .converter import TypeConverter, ConversionError
from .validator import ParamValidator, ValidationError


class ModelError(Exception):
    """模型解析错误

    Attributes:
        message: 错误消息
        model_class: 模型类
        field_errors: 字段错误列表
    """

    def __init__(
        self,
        message: str,
        model_class: Type = None,
        field_errors: list = None
    ):
        super().__init__(message)
        self.message = message
        self.model_class = model_class
        self.field_errors = field_errors or []

    def __repr__(self) -> str:
        return f"ModelError({self.message!r}, model={self.model_class})"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'message': self.message,
            'model': self.model_class.__name__ if self.model_class else None,
            'field_errors': self.field_errors,
        }


class ModelResolver:
    """模型解析器

    将请求数据 (dict) 映射到 dataclass 实例。

    Features:
    - 自动类型转换
    - 支持嵌套 dataclass
    - 支持默认值
    - 支持可选字段 (Optional)

    Example:
        from dataclasses import dataclass

        @dataclass
        class CreateUserRequest:
            name: str
            age: int = 0

        resolver = ModelResolver()
        data = {'name': 'test', 'age': '25'}
        user = resolver.resolve(CreateUserRequest, data)
        # user.name = 'test', user.age = 25
    """

    @classmethod
    def is_dataclass(cls, obj: Any) -> bool:
        """检查是否是 dataclass 类型

        Args:
            obj: 要检查的对象

        Returns:
            是否是 dataclass
        """
        return dataclasses.is_dataclass(obj) and isinstance(obj, type)

    @classmethod
    def resolve(cls, model_class: Type, data: Dict[str, Any]) -> Any:
        """将字典数据解析为模型实例

        Args:
            model_class: dataclass 类
            data: 请求数据字典

        Returns:
            dataclass 实例

        Raises:
            ModelError: 解析失败
        """
        if not cls.is_dataclass(model_class):
            raise ModelError(
                f"{model_class} is not a dataclass",
                model_class=model_class
            )

        if data is None:
            data = {}

        # 获取字段信息
        fields = dataclasses.fields(model_class)
        type_hints = get_type_hints(model_class)

        # 构建参数
        kwargs = {}
        field_errors = []

        for field in fields:
            field_name = field.name
            field_type = type_hints.get(field_name, field.type)

            # 检查是否有值
            if field_name in data:
                raw_value = data[field_name]

                try:
                    # 解析嵌套 dataclass
                    if cls.is_dataclass(field_type):
                        if isinstance(raw_value, dict):
                            kwargs[field_name] = cls.resolve(field_type, raw_value)
                        elif isinstance(raw_value, field_type):
                            kwargs[field_name] = raw_value
                        else:
                            raise ModelError(
                                f"Cannot convert {type(raw_value).__name__} to {field_type.__name__}"
                            )
                    else:
                        # 处理 Optional 类型
                        actual_type = cls._unwrap_optional(field_type)
                        if raw_value is None:
                            kwargs[field_name] = None
                        elif actual_type is not None:
                            kwargs[field_name] = TypeConverter.convert(raw_value, actual_type)
                        else:
                            kwargs[field_name] = raw_value

                except (ConversionError, ModelError) as e:
                    field_errors.append({
                        'field': field_name,
                        'error': str(e),
                        'value': raw_value
                    })
            else:
                # 没有提供值
                if field.default is not dataclasses.MISSING:
                    # 有默认值，使用默认值
                    kwargs[field_name] = field.default
                elif field.default_factory is not dataclasses.MISSING:
                    # 有默认工厂，调用工厂
                    kwargs[field_name] = field.default_factory()
                elif cls._is_optional(field_type):
                    # Optional 类型，设为 None
                    kwargs[field_name] = None
                else:
                    # 必填字段缺失
                    field_errors.append({
                        'field': field_name,
                        'error': f"Field '{field_name}' is required",
                        'value': None
                    })

        if field_errors:
            raise ModelError(
                f"Failed to resolve model {model_class.__name__}",
                model_class=model_class,
                field_errors=field_errors
            )

        try:
            return model_class(**kwargs)
        except Exception as e:
            raise ModelError(
                f"Failed to create {model_class.__name__}: {e}",
                model_class=model_class
            )

    @classmethod
    def _is_optional(cls, type_hint) -> bool:
        """检查类型是否是 Optional

        Args:
            type_hint: 类型提示

        Returns:
            是否是 Optional
        """
        # Optional[X] 等价于 Union[X, None]
        origin = getattr(type_hint, '__origin__', None)
        if origin is Union:
            args = getattr(type_hint, '__args__', ())
            return type(None) in args
        return False

    @classmethod
    def _unwrap_optional(cls, type_hint) -> Type:
        """从 Optional[X] 中提取 X

        Args:
            type_hint: 类型提示

        Returns:
            内部类型，如果不是 Optional 返回原类型
        """
        origin = getattr(type_hint, '__origin__', None)
        if origin is Union:
            args = getattr(type_hint, '__args__', ())
            # 过滤掉 NoneType
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return non_none[0]
        # 不是 Optional，返回原类型（如果是基本类型）
        if isinstance(type_hint, type):
            return type_hint
        return None

    @classmethod
    def to_dict(cls, instance: Any) -> Dict[str, Any]:
        """将 dataclass 实例转换为字典

        Args:
            instance: dataclass 实例

        Returns:
            字典
        """
        if not dataclasses.is_dataclass(instance):
            raise ModelError(f"{type(instance)} is not a dataclass instance")

        result = {}
        for field in dataclasses.fields(instance):
            value = getattr(instance, field.name)
            if dataclasses.is_dataclass(value):
                result[field.name] = cls.to_dict(value)
            else:
                result[field.name] = value
        return result

