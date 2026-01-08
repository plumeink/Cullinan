# -*- coding: utf-8 -*-
"""Cullinan Params Module

提供参数标记类和类型转换工具。

支持的参数类型:
- Path: URL 路径参数
- Query: 查询参数
- Body: 请求体参数
- Header: 请求头参数
- File: 文件参数

类型转换:
- TypeConverter: 类型转换器
- Auto: 自动类型推断
- DynamicBody: 动态请求体

校验:
- ParamValidator: 参数校验器

模型:
- ModelResolver: dataclass 模型解析

编排:
- ParamResolver: 参数解析编排器

Author: Plumeink
"""

from .base import Param, UNSET
from .types import Path, Query, Body, Header, File
from .converter import TypeConverter, ConversionError
from .auto import Auto, AutoType
from .dynamic import DynamicBody
from .validator import ParamValidator, ValidationError
from .model import ModelResolver, ModelError
from .resolver import ParamResolver, ResolveError

__all__ = [
    # 基类
    'Param',
    'UNSET',

    # 参数类型
    'Path',
    'Query',
    'Body',
    'Header',
    'File',

    # 类型转换
    'TypeConverter',
    'ConversionError',

    # 自动类型
    'Auto',
    'AutoType',

    # 动态请求体
    'DynamicBody',

    # 校验
    'ParamValidator',
    'ValidationError',

    # 模型
    'ModelResolver',
    'ModelError',

    # 编排
    'ParamResolver',
    'ResolveError',
]

