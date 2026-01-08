# -*- coding: utf-8 -*-
"""Cullinan Form Codec

Form 表单请求体解码器实现。

Author: Plumeink
"""

from urllib.parse import parse_qs, urlencode
from typing import Any, Dict

from .base import BodyCodec
from .errors import DecodeError, EncodeError


class FormBodyCodec(BodyCodec):
    """Form 表单解码器

    支持的 Content-Type:
    - application/x-www-form-urlencoded
    """

    content_types = ['application/x-www-form-urlencoded']
    priority = 20

    def decode(self, body: bytes, charset: str = 'utf-8') -> Dict[str, Any]:
        """解码 Form 请求体

        Args:
            body: 原始请求体字节
            charset: 字符编码

        Returns:
            解码后的字典 (单值字段展开为标量)

        Raises:
            DecodeError: 解析失败
        """
        if not body:
            return {}

        try:
            decoded = body.decode(charset)
            parsed = parse_qs(decoded, keep_blank_values=True)

            # 单值字段展开为标量，多值保持列表
            result = {}
            for key, values in parsed.items():
                if len(values) == 1:
                    result[key] = values[0]
                else:
                    result[key] = values

            return result

        except UnicodeDecodeError as e:
            raise DecodeError(
                f"Failed to decode form body with charset '{charset}': {e}",
                content_type='application/x-www-form-urlencoded',
                body_preview=body
            )
        except Exception as e:
            raise DecodeError(
                f"Failed to parse form body: {e}",
                content_type='application/x-www-form-urlencoded',
                body_preview=body
            )

    def encode(self, data: Dict[str, Any], charset: str = 'utf-8') -> bytes:
        """编码为 Form 格式

        Args:
            data: 要编码的字典
            charset: 字符编码

        Returns:
            URL 编码的字节串

        Raises:
            EncodeError: 编码失败
        """
        try:
            # 处理列表值
            encoded_data = {}
            for key, value in data.items():
                if isinstance(value, list):
                    encoded_data[key] = value
                else:
                    encoded_data[key] = str(value)

            return urlencode(encoded_data, doseq=True).encode(charset)

        except Exception as e:
            raise EncodeError(
                f"Failed to encode as form data: {e}",
                data_type=type(data)
            )

