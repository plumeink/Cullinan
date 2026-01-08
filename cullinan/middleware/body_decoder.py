# -*- coding: utf-8 -*-
"""Cullinan Body Decoder Middleware

请求体解码中间件，在请求进入 Handler 之前自动解码请求体。

Author: Plumeink
"""

import logging
from typing import Any, Optional

from .base import Middleware

logger = logging.getLogger(__name__)


class BodyDecoderMiddleware(Middleware):
    """请求体解码中间件

    在请求进入 Handler 之前，自动解码请求体并存储到 request 对象。

    特点:
    - 一次解码，全局可用
    - 支持多种 Content-Type (通过 CodecRegistry)
    - 可配置是否启用
    - 解码失败可配置处理策略

    Example:
        from cullinan.middleware import get_middleware_registry
        from cullinan.middleware.body_decoder import BodyDecoderMiddleware

        # 注册中间件
        registry = get_middleware_registry()
        registry.register(BodyDecoderMiddleware())

        # 在控制器中获取已解码的请求体
        decoded_body = get_decoded_body(self.request)
    """

    def __init__(
        self,
        enabled: bool = True,
        fail_silently: bool = True,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """初始化中间件

        Args:
            enabled: 是否启用解码
            fail_silently: 解码失败是否静默 (False 则返回 400 错误)
            max_body_size: 最大请求体大小 (bytes)
        """
        super().__init__()
        self.enabled = enabled
        self.fail_silently = fail_silently
        self.max_body_size = max_body_size

    def process_request(self, handler: Any) -> Any:
        """请求预处理: 解码请求体

        Args:
            handler: Tornado RequestHandler 实例

        Returns:
            handler 或 None (短路请求处理)
        """
        if not self.enabled:
            return handler

        request = handler.request

        # 检查请求体大小
        body = request.body
        if body and len(body) > self.max_body_size:
            logger.warning(
                f"Request body too large: {len(body)} bytes > {self.max_body_size} bytes"
            )
            if not self.fail_silently:
                handler.set_status(413)
                handler.write({"error": "Request body too large"})
                handler.finish()
                return None
            # 静默模式：设置空字典
            setattr(request, '_decoded_body', {})
            return handler

        # 获取 Content-Type
        content_type = request.headers.get('Content-Type', '')

        # 检测字符编码
        charset = self._detect_charset(content_type)

        # 解码
        try:
            from cullinan.codec import get_codec_registry, DecodeError

            registry = get_codec_registry()
            decoded = registry.decode_body(body or b'', content_type, charset)

            # 存储到 request 对象
            setattr(request, '_decoded_body', decoded)

            logger.debug(
                f"Decoded request body: content_type={content_type}, "
                f"charset={charset}, keys={list(decoded.keys())}"
            )

        except Exception as e:
            logger.warning(f"Failed to decode request body: {e}")
            if not self.fail_silently:
                handler.set_status(400)
                handler.write({"error": f"Request body decode failed: {e}"})
                handler.finish()
                return None
            setattr(request, '_decoded_body', {})

        return handler

    def _detect_charset(self, content_type: str) -> str:
        """从 Content-Type 检测字符编码

        Args:
            content_type: Content-Type 头

        Returns:
            字符编码 (默认 utf-8)
        """
        if 'charset=' in content_type:
            try:
                parts = content_type.split('charset=')
                if len(parts) > 1:
                    charset = parts[1].strip().split(';')[0].strip()
                    return charset.strip('"\'')
            except Exception:
                pass
        return 'utf-8'

    def on_init(self):
        """中间件初始化"""
        logger.debug(
            f"BodyDecoderMiddleware initialized: enabled={self.enabled}, "
            f"fail_silently={self.fail_silently}, max_body_size={self.max_body_size}"
        )


def get_decoded_body(request: Any) -> dict:
    """获取已解码的请求体

    Args:
        request: Tornado request 对象 (或 handler.request)

    Returns:
        解码后的字典 (如果未解码或解码失败，返回空字典)

    Example:
        class MyController:
            @post_api(url="/users")
            async def create_user(self):
                body = get_decoded_body(self.request)
                name = body.get('name')
    """
    return getattr(request, '_decoded_body', {})


def set_decoded_body(request: Any, data: dict) -> None:
    """手动设置已解码的请求体 (测试用)

    Args:
        request: Tornado request 对象
        data: 要设置的数据
    """
    setattr(request, '_decoded_body', data)

