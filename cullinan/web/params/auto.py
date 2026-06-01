# -*- coding: utf-8 -*-
"""Cullinan Auto Type Inference

自动类型推断，根据值内容自动确定类型。

Author: Plumeink
"""

import json
import re
from typing import Any, Type


class Auto:
    """自动类型推断

    根据传入值的内容自动推断并转换为合适的类型。

    类型推断优先级:
    1. None / null -> None
    2. 布尔值字符串 -> bool
    3. 整数字符串 -> int
    4. 浮点数字符串 -> float
    5. JSON 对象/数组 -> dict/list
    6. 其他 -> 保持原类型 (通常是 str)

    Example:
        Auto.infer("123")      # -> 123 (int)
        Auto.infer("12.5")     # -> 12.5 (float)
        Auto.infer("true")     # -> True (bool)
        Auto.infer('{"a":1}')  # -> {"a": 1} (dict)
        Auto.infer("hello")    # -> "hello" (str)
    """

    # 布尔值映射
    BOOL_MAP = {
        'true': True, 'True': True, 'TRUE': True,
        'false': False, 'False': False, 'FALSE': False,
        'yes': True, 'Yes': True, 'YES': True,
        'no': False, 'No': False, 'NO': False,
        'on': True, 'On': True, 'ON': True,
        'off': False, 'Off': False, 'OFF': False,
    }

    # 数字模式
    INT_PATTERN = re.compile(r'^-?\d+$')
    FLOAT_PATTERN = re.compile(r'^-?\d+\.\d+$')
    SCIENTIFIC_PATTERN = re.compile(r'^-?\d+\.?\d*[eE][+-]?\d+$')

    @classmethod
    def infer(cls, value: Any) -> Any:
        """根据值内容推断并转换类型

        Args:
            value: 原始值

        Returns:
            转换后的值
        """
        if value is None:
            return None

        # 如果已经是非字符串类型，直接返回
        if not isinstance(value, str):
            return value

        # 空字符串
        if value == '':
            return ''

        # 去除首尾空白后推断
        stripped = value.strip()

        # null / None
        if stripped.lower() in ('null', 'none'):
            return None

        # 布尔值
        if stripped in cls.BOOL_MAP:
            return cls.BOOL_MAP[stripped]

        # 整数
        if cls.INT_PATTERN.match(stripped):
            try:
                return int(stripped)
            except ValueError:
                pass

        # 浮点数
        if cls.FLOAT_PATTERN.match(stripped) or cls.SCIENTIFIC_PATTERN.match(stripped):
            try:
                return float(stripped)
            except ValueError:
                pass

        # JSON 对象
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                pass

        # JSON 数组
        if stripped.startswith('[') and stripped.endswith(']'):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                pass

        # 保持原字符串
        return value

    @classmethod
    def infer_type(cls, value: Any) -> Type:
        """推断值的目标类型 (不进行转换)

        Args:
            value: 原始值

        Returns:
            推断的类型
        """
        if value is None:
            return type(None)

        if not isinstance(value, str):
            return type(value)

        stripped = value.strip()

        # null / None
        if stripped.lower() in ('null', 'none'):
            return type(None)

        # 布尔值
        if stripped in cls.BOOL_MAP:
            return bool

        # 整数
        if cls.INT_PATTERN.match(stripped):
            return int

        # 浮点数
        if cls.FLOAT_PATTERN.match(stripped) or cls.SCIENTIFIC_PATTERN.match(stripped):
            return float

        # JSON 对象
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                result = json.loads(stripped)
                if isinstance(result, dict):
                    return dict
            except json.JSONDecodeError:
                pass

        # JSON 数组
        if stripped.startswith('[') and stripped.endswith(']'):
            try:
                result = json.loads(stripped)
                if isinstance(result, list):
                    return list
            except json.JSONDecodeError:
                pass

        return str


class AutoType:
    """Auto 类型标记

    用于参数声明时表示自动类型推断。

    Example:
        @get_api(url="/search")
        async def search(self, limit: Query(AutoType, default=10)):
            # limit 会自动推断类型
            pass
    """
    pass

