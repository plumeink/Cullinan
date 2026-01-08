# -*- coding: utf-8 -*-
"""Cullinan JSON Codec

JSON 请求体解码器和响应编码器实现。

Author: Plumeink
"""

import json
from typing import Any, Dict

from .base import BodyCodec, ResponseCodec
from .errors import DecodeError, EncodeError


class JsonBodyCodec(BodyCodec):
    """JSON 请求体解码器

    支持的 Content-Type:
    - application/json
    - text/json
    - application/json; charset=utf-8
    """

    content_types = ['application/json', 'text/json']
    priority = 10  # 高优先级

    def decode(self, body: bytes, charset: str = 'utf-8') -> Dict[str, Any]:
        """解码 JSON 请求体

        Args:
            body: 原始请求体字节
            charset: 字符编码

        Returns:
            解码后的字典 (空请求体返回空字典)

        Raises:
            DecodeError: JSON 解析失败
        """
        if not body:
            return {}

        try:
            decoded = body.decode(charset)
            result = json.loads(decoded)

            # 确保返回字典
            if isinstance(result, dict):
                return result
            # 非字典值包装 (如 JSON 数组或标量)
            return {'_value': result}

        except UnicodeDecodeError as e:
            raise DecodeError(
                f"Failed to decode body with charset '{charset}': {e}",
                content_type='application/json',
                body_preview=body
            )
        except json.JSONDecodeError as e:
            raise DecodeError(
                f"Invalid JSON: {e}",
                content_type='application/json',
                body_preview=body
            )

    def encode(self, data: Dict[str, Any], charset: str = 'utf-8') -> bytes:
        """编码为 JSON

        Args:
            data: 要编码的字典
            charset: 字符编码

        Returns:
            JSON 字节串
        """
        try:
            return json.dumps(data, ensure_ascii=False).encode(charset)
        except (TypeError, ValueError) as e:
            raise EncodeError(
                f"Failed to encode as JSON: {e}",
                data_type=type(data)
            )


class JsonResponseCodec(ResponseCodec):
    """JSON 响应编码器

    将响应数据编码为 JSON 格式。
    """

    content_type = 'application/json'
    accept_types = ['application/json', 'text/json', '*/*']
    priority = 10  # 高优先级

    def encode(self, data: Any, charset: str = 'utf-8') -> bytes:
        """编码响应数据为 JSON

        Args:
            data: 响应数据 (可以是任意 JSON 可序列化类型)
            charset: 字符编码

        Returns:
            JSON 字节串

        Raises:
            EncodeError: 序列化失败
        """
        try:
            # 使用 default=str 处理不可序列化的类型
            return json.dumps(
                data,
                ensure_ascii=False,
                default=str
            ).encode(charset)
        except Exception as e:
            raise EncodeError(
                f"Failed to encode response as JSON: {e}",
                data_type=type(data)
            )

