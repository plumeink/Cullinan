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
- field_validator: dataclass 字段校验器

模型:
- ModelResolver: dataclass 模型解析

文件:
- FileInfo: 文件信息容器
- FileList: 多文件容器

响应:
- Response: 响应模型装饰器
- ResponseSerializer: 响应序列化器

编排:
- ParamResolver: 参数解析编排器

Author: Plumeink
"""

from .base import Param, UNSET
from .types import Path, Query, Body, Header, File
from .converter import TypeConverter, ConversionError
from .auto import Auto, AutoType
from .dynamic import DynamicBody, SafeAccessor, EMPTY
from .validator import ParamValidator, ValidationError
from .model import ModelResolver, ModelError
from .resolver import ParamResolver, ResolveError
from .file_info import FileInfo, FileList
from .dataclass_validators import (
    field_validator,
    FieldValidationError,
    validated_dataclass,
    validate_field,
    validate_dataclass,
)
from .response import (
    Response,
    ResponseModel,
    ResponseSerializer,
    serialize_response,
    get_response_models,
)
from .model_handlers import (
    ModelHandler,
    ModelHandlerError,
    ModelHandlerRegistry,
    DataclassHandler,
    get_model_handler_registry,
    reset_model_handler_registry,
)

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
    'SafeAccessor',
    'EMPTY',

    # 校验
    'ParamValidator',
    'ValidationError',

    # 模型
    'ModelResolver',
    'ModelError',

    # 文件
    'FileInfo',
    'FileList',

    # Dataclass 校验
    'field_validator',
    'FieldValidationError',
    'validated_dataclass',
    'validate_field',
    'validate_dataclass',

    # 响应
    'Response',
    'ResponseModel',
    'ResponseSerializer',
    'serialize_response',
    'get_response_models',

    # 模型处理器（可插拔）
    'ModelHandler',
    'ModelHandlerError',
    'ModelHandlerRegistry',
    'DataclassHandler',
    'get_model_handler_registry',
    'reset_model_handler_registry',

    # 编排
    'ParamResolver',
    'ResolveError',
]

