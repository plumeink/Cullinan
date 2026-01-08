# -*- coding: utf-8 -*-
"""Cullinan Dataclass Validators

为 dataclass 提供字段级校验装饰器。

Author: Plumeink
"""

from typing import Any, Callable, Dict, List, Type, Union
from functools import wraps
import dataclasses


# 存储每个 dataclass 的字段校验器
_field_validators: Dict[Type, Dict[str, List[Callable]]] = {}


class FieldValidationError(Exception):
    """字段校验错误

    Attributes:
        field: 字段名
        value: 字段值
        message: 错误消息
    """

    def __init__(self, field: str, value: Any, message: str):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"Field '{field}' validation failed: {message}")

    def to_dict(self) -> dict:
        return {
            'field': self.field,
            'value': self.value,
            'message': self.message,
        }


def field_validator(*fields: str, mode: str = 'after'):
    """字段校验器装饰器

    用于在 dataclass 中定义字段级别的校验逻辑。

    Args:
        *fields: 要校验的字段名列表
        mode: 校验模式
            - 'after': 在类型转换后校验（默认）
            - 'before': 在类型转换前校验

    Example:
        from dataclasses import dataclass
        from cullinan.params import field_validator

        @dataclass
        class CreateUserRequest:
            name: str
            email: str
            age: int = 0

            @field_validator('email')
            @classmethod
            def validate_email(cls, v):
                if '@' not in v:
                    raise ValueError('Invalid email format')
                return v

            @field_validator('age')
            @classmethod
            def validate_age(cls, v):
                if v < 0 or v > 150:
                    raise ValueError('Age must be between 0 and 150')
                return v

            @field_validator('name', 'email')
            @classmethod
            def strip_strings(cls, v):
                if isinstance(v, str):
                    return v.strip()
                return v
    """
    def decorator(func: Callable) -> Callable:
        # 检查是否是 classmethod
        if isinstance(func, classmethod):
            # 获取实际函数
            actual_func = func.__func__
            # 标记校验器属性
            actual_func._is_field_validator = True
            actual_func._validator_fields = fields
            actual_func._validator_mode = mode
            # 返回原始 classmethod，保持其类型
            return func
        else:
            # 普通函数
            func._is_field_validator = True
            func._validator_fields = fields
            func._validator_mode = mode
            return func

    return decorator


def register_validators(cls: Type) -> None:
    """注册 dataclass 的所有字段校验器

    Args:
        cls: dataclass 类
    """
    if not dataclasses.is_dataclass(cls):
        return

    validators = {}

    # 扫描类中的校验器方法
    for name in dir(cls):
        if name.startswith('_'):
            continue

        try:
            # 使用 __dict__ 直接获取，避免描述符协议
            if name in cls.__dict__:
                method = cls.__dict__[name]
            else:
                method = getattr(cls, name, None)
        except Exception:
            continue

        if method is None:
            continue

        # 处理 classmethod 包装
        actual_method = method
        if isinstance(method, classmethod):
            actual_method = method.__func__

        # 检查是否是校验器
        if hasattr(actual_method, '_is_field_validator') and actual_method._is_field_validator:
            for field in actual_method._validator_fields:
                if field not in validators:
                    validators[field] = []
                validators[field].append({
                    'func': actual_method,
                    'mode': actual_method._validator_mode,
                })

    if validators:
        _field_validators[cls] = validators


def get_validators(cls: Type) -> Dict[str, List[dict]]:
    """获取 dataclass 的字段校验器

    Args:
        cls: dataclass 类

    Returns:
        字段名到校验器列表的映射
    """
    if cls not in _field_validators:
        register_validators(cls)
    return _field_validators.get(cls, {})


def validate_field(cls: Type, field: str, value: Any, mode: str = 'after') -> Any:
    """对字段值执行校验

    Args:
        cls: dataclass 类
        field: 字段名
        value: 字段值
        mode: 校验模式

    Returns:
        校验/转换后的值

    Raises:
        FieldValidationError: 校验失败
    """
    validators = get_validators(cls)
    field_validators = validators.get(field, [])

    for validator in field_validators:
        if validator['mode'] != mode:
            continue

        try:
            value = validator['func'](cls, value)
        except ValueError as e:
            raise FieldValidationError(field, value, str(e))
        except Exception as e:
            raise FieldValidationError(field, value, str(e))

    return value


def validate_dataclass(instance) -> None:
    """校验整个 dataclass 实例

    Args:
        instance: dataclass 实例

    Raises:
        FieldValidationError: 校验失败
    """
    cls = type(instance)

    if not dataclasses.is_dataclass(cls):
        return

    validators = get_validators(cls)

    for field in dataclasses.fields(instance):
        field_name = field.name
        value = getattr(instance, field_name)

        # 执行 after 模式的校验器
        if field_name in validators:
            for validator in validators[field_name]:
                if validator['mode'] == 'after':
                    try:
                        func = validator['func']
                        # 处理 classmethod - 需要使用类作为第一个参数
                        if isinstance(func, classmethod):
                            new_value = func.__func__(cls, value)
                        else:
                            # 普通函数/方法
                            new_value = func(cls, value)
                        setattr(instance, field_name, new_value)
                    except ValueError as e:
                        raise FieldValidationError(field_name, value, str(e))


class validated_dataclass:
    """带自动校验的 dataclass 装饰器

    包装 @dataclass，自动在实例化后执行字段校验。

    Example:
        from cullinan.params import validated_dataclass, field_validator

        @validated_dataclass
        class CreateUserRequest:
            name: str
            email: str
            age: int = 0

            @field_validator('email')
            @classmethod
            def validate_email(cls, v):
                if '@' not in v:
                    raise ValueError('Invalid email format')
                return v
    """

    def __new__(cls, wrapped_cls=None, **kwargs):
        """支持 @validated_dataclass 和 @validated_dataclass() 两种用法"""
        if wrapped_cls is not None:
            # @validated_dataclass 不带括号
            return cls._wrap_class(wrapped_cls, kwargs)
        else:
            # @validated_dataclass() 带括号
            def decorator(c):
                return cls._wrap_class(c, kwargs)
            return decorator

    @staticmethod
    def _wrap_class(cls, kwargs=None):
        """包装类"""
        if kwargs is None:
            kwargs = {}

        # 应用 @dataclass
        if not dataclasses.is_dataclass(cls):
            cls = dataclasses.dataclass(cls, **kwargs)

        # 注册校验器（在 @dataclass 之后）
        register_validators(cls)

        # 保存原始的 __init__
        original_init = cls.__init__

        def new_init(self, *args, **kw):
            # 调用原始的 __init__
            original_init(self, *args, **kw)
            # 执行校验
            validate_dataclass(self)

        cls.__init__ = new_init

        return cls


def clear_validators():
    """清除所有已注册的校验器（用于测试）"""
    _field_validators.clear()

