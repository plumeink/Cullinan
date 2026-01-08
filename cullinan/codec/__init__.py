# -*- coding: utf-8 -*-
"""Cullinan Codec Module

提供请求体和响应体的编解码功能。

支持的格式:
- JSON (application/json)
- Form (application/x-www-form-urlencoded)
- 可扩展自定义格式

Author: Plumeink
"""

from .base import BodyCodec, ResponseCodec
from .errors import CodecError, DecodeError, EncodeError
from .json_codec import JsonBodyCodec, JsonResponseCodec
from .form_codec import FormBodyCodec
from .registry import (
    CodecRegistry,
    get_codec_registry,
    reset_codec_registry,
)

__all__ = [
    # 抽象基类
    'BodyCodec',
    'ResponseCodec',

    # 错误类型
    'CodecError',
    'DecodeError',
    'EncodeError',

    # 内置 Codec
    'JsonBodyCodec',
    'JsonResponseCodec',
    'FormBodyCodec',

    # 注册表
    'CodecRegistry',
    'get_codec_registry',
    'reset_codec_registry',
]

