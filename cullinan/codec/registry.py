# -*- coding: utf-8 -*-
"""Cullinan Codec Registry

Codec 注册表，管理所有 BodyCodec 和 ResponseCodec。

Author: Plumeink
"""

from typing import Any, Dict, List, Optional, Tuple, Type

from .base import BodyCodec, ResponseCodec
from .errors import DecodeError, EncodeError


class CodecRegistry:
    """Codec 注册表

    管理所有 BodyCodec 和 ResponseCodec 的注册和选择。

    Example:
        registry = get_codec_registry()

        # 解码请求体
        data = registry.decode_body(body, 'application/json')

        # 编码响应
        encoded, content_type = registry.encode_response(data, 'application/json')

        # 注册自定义 Codec
        registry.register_body_codec(XmlBodyCodec)
    """

    def __init__(self):
        self._body_codecs: List[Type[BodyCodec]] = []
        self._response_codecs: List[Type[ResponseCodec]] = []

    def register_body_codec(self, codec_class: Type[BodyCodec]) -> None:
        """注册请求体 Codec

        Args:
            codec_class: BodyCodec 子类
        """
        if codec_class not in self._body_codecs:
            self._body_codecs.append(codec_class)
            # 按优先级排序 (数字越小越优先)
            self._body_codecs.sort(key=lambda c: c.priority)

    def register_response_codec(self, codec_class: Type[ResponseCodec]) -> None:
        """注册响应 Codec

        Args:
            codec_class: ResponseCodec 子类
        """
        if codec_class not in self._response_codecs:
            self._response_codecs.append(codec_class)
            self._response_codecs.sort(key=lambda c: c.priority)

    def unregister_body_codec(self, codec_class: Type[BodyCodec]) -> None:
        """取消注册请求体 Codec"""
        if codec_class in self._body_codecs:
            self._body_codecs.remove(codec_class)

    def unregister_response_codec(self, codec_class: Type[ResponseCodec]) -> None:
        """取消注册响应 Codec"""
        if codec_class in self._response_codecs:
            self._response_codecs.remove(codec_class)

    def get_body_codec(self, content_type: str) -> Optional[BodyCodec]:
        """根据 Content-Type 获取请求体 Codec 实例

        Args:
            content_type: HTTP Content-Type 头

        Returns:
            Codec 实例，无匹配返回 None
        """
        for codec_class in self._body_codecs:
            if codec_class.supports(content_type):
                return codec_class()
        return None

    def get_response_codec(self, accept: str = '*/*') -> Optional[ResponseCodec]:
        """根据 Accept 获取响应 Codec 实例

        Args:
            accept: HTTP Accept 头

        Returns:
            Codec 实例，无匹配返回 None
        """
        for codec_class in self._response_codecs:
            if codec_class.supports_accept(accept):
                return codec_class()
        return None

    def decode_body(
        self,
        body: bytes,
        content_type: str,
        charset: str = 'utf-8'
    ) -> Dict[str, Any]:
        """解码请求体

        Args:
            body: 原始请求体字节
            content_type: Content-Type 头
            charset: 字符编码

        Returns:
            解码后的字典

        Raises:
            DecodeError: 解码失败
        """
        codec = self.get_body_codec(content_type)
        if codec:
            return codec.decode(body, charset)

        # 默认尝试 JSON
        from .json_codec import JsonBodyCodec
        return JsonBodyCodec().decode(body, charset)

    def encode_response(
        self,
        data: Any,
        accept: str = '*/*',
        charset: str = 'utf-8'
    ) -> Tuple[bytes, str]:
        """编码响应

        Args:
            data: 响应数据
            accept: Accept 头
            charset: 字符编码

        Returns:
            (编码后的字节, Content-Type)

        Raises:
            EncodeError: 编码失败
        """
        codec = self.get_response_codec(accept)
        if codec:
            return codec.encode(data, charset), codec.get_content_type(charset)

        # 默认 JSON
        from .json_codec import JsonResponseCodec
        default_codec = JsonResponseCodec()
        return default_codec.encode(data, charset), default_codec.get_content_type(charset)

    def list_body_codecs(self) -> List[Type[BodyCodec]]:
        """列出所有注册的请求体 Codec"""
        return list(self._body_codecs)

    def list_response_codecs(self) -> List[Type[ResponseCodec]]:
        """列出所有注册的响应 Codec"""
        return list(self._response_codecs)


# 全局注册表实例
_codec_registry: Optional[CodecRegistry] = None


def get_codec_registry() -> CodecRegistry:
    """获取全局 Codec 注册表

    Returns:
        CodecRegistry 单例
    """
    global _codec_registry
    if _codec_registry is None:
        _codec_registry = CodecRegistry()
        # 注册默认 Codec
        from .json_codec import JsonBodyCodec, JsonResponseCodec
        from .form_codec import FormBodyCodec
        _codec_registry.register_body_codec(JsonBodyCodec)
        _codec_registry.register_body_codec(FormBodyCodec)
        _codec_registry.register_response_codec(JsonResponseCodec)
    return _codec_registry


def reset_codec_registry() -> None:
    """重置全局注册表 (测试用)"""
    global _codec_registry
    _codec_registry = None

