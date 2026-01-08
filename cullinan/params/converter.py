# -*- coding: utf-8 -*-
"""Cullinan Type Converter

类型转换器，将请求参数转换为目标类型。

Author: Plumeink
"""

import json
from typing import Any, Type, Union


class ConversionError(Exception):
    """类型转换错误

    Attributes:
        message: 错误消息
        value: 原始值
        target_type: 目标类型
    """

    def __init__(
        self,
        message: str,
        value: Any = None,
        target_type: Type = None
    ):
        super().__init__(message)
        self.message = message
        self.value = value
        self.target_type = target_type

    def __repr__(self) -> str:
        return f"ConversionError({self.message!r}, value={self.value!r}, target_type={self.target_type})"


class TypeConverter:
    """类型转换器

    将请求中的原始值转换为目标类型。

    Example:
        converter = TypeConverter()

        # 基本转换
        result = converter.convert("123", int)  # -> 123
        result = converter.convert("true", bool)  # -> True
        result = converter.convert("1,2,3", list)  # -> ["1", "2", "3"]
    """

    # 布尔值真值字符串
    TRUE_VALUES = frozenset({
        'true', 'True', 'TRUE',
        '1',
        'yes', 'Yes', 'YES',
        'on', 'On', 'ON'
    })

    FALSE_VALUES = frozenset({
        'false', 'False', 'FALSE',
        '0', '',
        'no', 'No', 'NO',
        'off', 'Off', 'OFF'
    })

    @classmethod
    def convert(cls, value: Any, target_type: Type) -> Any:
        """将值转换为目标类型

        Args:
            value: 原始值
            target_type: 目标类型

        Returns:
            转换后的值

        Raises:
            ConversionError: 转换失败
        """
        if value is None:
            return None

        # 如果已经是目标类型，直接返回
        if isinstance(value, target_type):
            return value

        try:
            if target_type is str:
                return cls._to_str(value)
            elif target_type is int:
                return cls._to_int(value)
            elif target_type is float:
                return cls._to_float(value)
            elif target_type is bool:
                return cls._to_bool(value)
            elif target_type is list:
                return cls._to_list(value)
            elif target_type is dict:
                return cls._to_dict(value)
            elif target_type is bytes:
                return cls._to_bytes(value)
            else:
                # 尝试直接调用目标类型构造函数
                return target_type(value)
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(
                f"Cannot convert {type(value).__name__} to {target_type.__name__}: {e}",
                value=value,
                target_type=target_type
            )

    @classmethod
    def _to_str(cls, value: Any) -> str:
        """转换为字符串"""
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return str(value)

    @classmethod
    def _to_int(cls, value: Any) -> int:
        """转换为整数"""
        if isinstance(value, str):
            value = value.strip()
            # 处理浮点数字符串
            if '.' in value:
                return int(float(value))
            # 处理空字符串
            if not value:
                raise ConversionError(
                    "Cannot convert empty string to int",
                    value=value,
                    target_type=int
                )
            return int(value)
        if isinstance(value, float):
            return int(value)
        if isinstance(value, bool):
            return 1 if value else 0
        return int(value)

    @classmethod
    def _to_float(cls, value: Any) -> float:
        """转换为浮点数"""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ConversionError(
                    "Cannot convert empty string to float",
                    value=value,
                    target_type=float
                )
        return float(value)

    @classmethod
    def _to_bool(cls, value: Any) -> bool:
        """转换为布尔值"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value in cls.TRUE_VALUES:
                return True
            if value in cls.FALSE_VALUES:
                return False
            raise ConversionError(
                f"Cannot convert '{value}' to bool",
                value=value,
                target_type=bool
            )
        if isinstance(value, (int, float)):
            return bool(value)
        return bool(value)

    @classmethod
    def _to_list(cls, value: Any) -> list:
        """转换为列表"""
        if isinstance(value, list):
            return value
        if isinstance(value, (tuple, set, frozenset)):
            return list(value)
        if isinstance(value, str):
            # 尝试解析 JSON 数组
            value = value.strip()
            if value.startswith('[') and value.endswith(']'):
                try:
                    result = json.loads(value)
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    pass
            # 逗号分隔
            if ',' in value:
                return [v.strip() for v in value.split(',')]
            # 单值
            if value:
                return [value]
            return []
        return [value]

    @classmethod
    def _to_dict(cls, value: Any) -> dict:
        """转换为字典"""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            value = value.strip()
            if value.startswith('{') and value.endswith('}'):
                try:
                    result = json.loads(value)
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    pass
            raise ConversionError(
                f"Cannot parse '{value}' as JSON dict",
                value=value,
                target_type=dict
            )
        raise ConversionError(
            f"Cannot convert {type(value).__name__} to dict",
            value=value,
            target_type=dict
        )

    @classmethod
    def _to_bytes(cls, value: Any) -> bytes:
        """转换为字节串"""
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode('utf-8')
        if isinstance(value, (bytearray, memoryview)):
            return bytes(value)
        raise ConversionError(
            f"Cannot convert {type(value).__name__} to bytes",
            value=value,
            target_type=bytes
        )

    @classmethod
    def can_convert(cls, value: Any, target_type: Type) -> bool:
        """检查是否可以转换

        Args:
            value: 原始值
            target_type: 目标类型

        Returns:
            是否可以转换
        """
        try:
            cls.convert(value, target_type)
            return True
        except (ConversionError, Exception):
            return False

