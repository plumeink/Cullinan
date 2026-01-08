# -*- coding: utf-8 -*-
"""Cullinan Codec Base Classes

定义 BodyCodec 和 ResponseCodec 抽象基类。

Author: Plumeink
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BodyCodec(ABC):
    """请求体编解码器抽象基类

    职责:
    - decode: bytes → dict (请求解码)
    - encode: dict → bytes (可选，用于某些场景)

    特点:
    - 纯粹的编解码，不涉及业务逻辑
    - 可在 Middleware 中统一调用

    Example:
        class JsonBodyCodec(BodyCodec):
            content_types = ['application/json']

            def decode(self, body, charset='utf-8'):
                return json.loads(body.decode(charset))
    """

    # 支持的 Content-Type 列表 (子类必须重写)
    content_types: List[str] = []

    # 优先级 (数字越小优先级越高)
    priority: int = 100

    @abstractmethod
    def decode(self, body: bytes, charset: str = 'utf-8') -> Dict[str, Any]:
        """解码请求体

        Args:
            body: 原始请求体字节
            charset: 字符编码

        Returns:
            解码后的字典

        Raises:
            DecodeError: 解码失败
        """
        pass

    def encode(self, data: Dict[str, Any], charset: str = 'utf-8') -> bytes:
        """编码数据 (可选实现)

        Args:
            data: 要编码的字典
            charset: 字符编码

        Returns:
            编码后的字节

        Raises:
            EncodeError: 编码失败
        """
        raise NotImplementedError("This codec does not support encoding")

    @classmethod
    def supports(cls, content_type: str) -> bool:
        """检查是否支持该 Content-Type

        Args:
            content_type: HTTP Content-Type 头

        Returns:
            是否支持
        """
        if not content_type:
            return False
        ct_lower = content_type.lower()
        for ct in cls.content_types:
            if ct in ct_lower:
                return True
        return False


class ResponseCodec(ABC):
    """响应体编解码器抽象基类

    职责:
    - encode: Any → bytes (响应编码)
    - 设置正确的 Content-Type

    使用场景:
    - 统一响应格式 (JSON/XML/MessagePack)
    - 内容协商 (Accept header)

    Example:
        class JsonResponseCodec(ResponseCodec):
            content_type = 'application/json'
            accept_types = ['application/json', '*/*']

            def encode(self, data, charset='utf-8'):
                return json.dumps(data).encode(charset)
    """

    # 输出的 Content-Type
    content_type: str = 'application/octet-stream'

    # 支持的 Accept 类型
    accept_types: List[str] = []

    # 优先级
    priority: int = 100

    @abstractmethod
    def encode(self, data: Any, charset: str = 'utf-8') -> bytes:
        """编码响应数据

        Args:
            data: 响应数据 (可以是任意类型)
            charset: 字符编码

        Returns:
            编码后的字节

        Raises:
            EncodeError: 编码失败
        """
        pass

    def get_content_type(self, charset: str = 'utf-8') -> str:
        """获取完整的 Content-Type 头

        Args:
            charset: 字符编码

        Returns:
            完整的 Content-Type 字符串
        """
        if 'charset' not in self.content_type.lower():
            return f"{self.content_type}; charset={charset}"
        return self.content_type

    @classmethod
    def supports_accept(cls, accept: str) -> bool:
        """检查是否支持该 Accept 类型

        Args:
            accept: HTTP Accept 头

        Returns:
            是否支持
        """
        if not accept or accept == '*/*':
            return True
        accept_lower = accept.lower()
        for at in cls.accept_types:
            if at in accept_lower:
                return True
        return False

