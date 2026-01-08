# -*- coding: utf-8 -*-
"""Cullinan Codec Errors

定义编解码相关的异常类。

Author: Plumeink
"""

from typing import Any, Optional


class CodecError(Exception):
    """编解码错误基类"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DecodeError(CodecError):
    """解码错误

    当请求体解码失败时抛出。

    Attributes:
        message: 错误消息
        content_type: 请求的 Content-Type
        body_preview: 请求体预览（前100字节）
    """

    def __init__(
        self,
        message: str,
        content_type: str = None,
        body_preview: bytes = None,
        details: Optional[dict] = None
    ):
        super().__init__(message, details)
        self.content_type = content_type
        self.body_preview = body_preview[:100] if body_preview else None

    def __repr__(self) -> str:
        return f"DecodeError({self.message!r}, content_type={self.content_type!r})"


class EncodeError(CodecError):
    """编码错误

    当响应体编码失败时抛出。

    Attributes:
        message: 错误消息
        data_type: 尝试编码的数据类型
    """

    def __init__(
        self,
        message: str,
        data_type: type = None,
        details: Optional[dict] = None
    ):
        super().__init__(message, details)
        self.data_type = data_type

    def __repr__(self) -> str:
        return f"EncodeError({self.message!r}, data_type={self.data_type})"

