# -*- coding: utf-8 -*-
"""Cullinan Parameter Types

定义各种参数来源类型：Path, Query, Body, Header, File。

Author: Plumeink
"""

from typing import Any, List, Optional, Type

from .base import Param, UNSET


class Path(Param):
    """URL 路径参数

    从 URL 路径中提取的参数，如 /users/{id} 中的 id。
    路径参数始终是必填的。

    Example:
        @get_api(url="/users/{id}")
        async def get_user(self, id: Path(int)):
            # id 已经转换为 int 类型
            pass

        @get_api(url="/users/{id}/posts/{post_id}")
        async def get_post(self, id: Path(int), post_id: Path(int)):
            pass
    """
    _source = 'path'

    def __init__(
        self,
        type_: Type = str,
        *,
        name: str = None,
        description: str = '',
        alias: str = None,
        # 数值约束
        ge: Any = None,
        le: Any = None,
        gt: Any = None,
        lt: Any = None,
        # 长度约束
        min_length: int = None,
        max_length: int = None,
        # 正则约束
        regex: str = None,
    ):
        """初始化路径参数

        Note:
            路径参数始终是必填的，不支持默认值。
        """
        super().__init__(
            type_=type_,
            name=name,
            required=True,  # 路径参数始终必填
            default=UNSET,  # 不支持默认值
            description=description,
            alias=alias,
            ge=ge,
            le=le,
            gt=gt,
            lt=lt,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
        )


class Query(Param):
    """查询参数

    从 URL 查询字符串中提取的参数，如 ?page=1&size=10。

    Example:
        @get_api(url="/users")
        async def list_users(
            self,
            page: Query(int, default=1, ge=1),
            size: Query(int, default=10, ge=1, le=100),
            q: Query(str, required=False),
        ):
            pass
    """
    _source = 'query'

    # 继承 Param 的 __init__，无需重写


class Body(Param):
    """请求体参数

    从请求体中提取的参数。传输格式 (JSON/Form) 由 Codec 层处理。

    Example:
        # 单个字段
        @post_api(url="/users")
        async def create_user(
            self,
            name: Body(str, required=True),
            age: Body(int, default=0, ge=0),
        ):
            pass

        # 配合 DynamicBody 使用整个请求体
        @post_api(url="/users")
        async def create_user(self, body: DynamicBody):
            print(body.name, body.age)
    """
    _source = 'body'

    # 继承 Param 的 __init__，无需重写


class Header(Param):
    """请求头参数

    从 HTTP 请求头中提取的参数。
    通常使用 alias 指定实际的请求头名称。

    Example:
        @get_api(url="/users")
        async def list_users(
            self,
            auth: Header(str, alias='Authorization', required=True),
            request_id: Header(str, alias='X-Request-ID', required=False),
        ):
            pass
    """
    _source = 'header'

    def __init__(
        self,
        type_: Type = str,
        *,
        name: str = None,
        required: bool = True,
        default: Any = UNSET,
        description: str = '',
        alias: str = None,
        # 长度约束
        min_length: int = None,
        max_length: int = None,
        # 正则约束
        regex: str = None,
    ):
        """初始化请求头参数

        Note:
            请求头参数通常使用 alias 指定实际的头名称，
            如 Authorization, Content-Type, X-Request-ID 等。
        """
        super().__init__(
            type_=type_,
            name=name,
            required=required,
            default=default,
            description=description,
            alias=alias,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
        )


class File(Param):
    """文件参数

    从 multipart/form-data 请求中提取的文件。

    Attributes:
        max_size: 最大文件大小 (bytes)
        allowed_types: 允许的 MIME 类型列表

    Example:
        @post_api(url="/upload")
        async def upload(
            self,
            avatar: File(required=True, max_size=5*1024*1024),  # 5MB
            document: File(allowed_types=['application/pdf', 'image/*']),
        ):
            pass
    """
    _source = 'file'

    # 扩展 __slots__
    __slots__ = ('max_size', 'allowed_types')

    def __init__(
        self,
        *,
        name: str = None,
        required: bool = True,
        description: str = '',
        alias: str = None,
        max_size: Optional[int] = None,
        allowed_types: Optional[List[str]] = None,
    ):
        """初始化文件参数

        Args:
            name: 参数名称
            required: 是否必填
            description: 参数描述
            alias: 别名 (表单字段名)
            max_size: 最大文件大小 (bytes)
            allowed_types: 允许的 MIME 类型列表
        """
        super().__init__(
            type_=bytes,  # 文件内容为 bytes
            name=name,
            required=required,
            default=UNSET,
            description=description,
            alias=alias,
        )
        self.max_size = max_size
        self.allowed_types = allowed_types or []

    def __repr__(self) -> str:
        parts = [f"File("]
        if self.name:
            parts.append(f"name={self.name!r}, ")
        if not self.required:
            parts.append("required=False, ")
        if self.max_size:
            parts.append(f"max_size={self.max_size}, ")
        if self.allowed_types:
            parts.append(f"allowed_types={self.allowed_types!r}, ")
        result = "".join(parts)
        if result.endswith(", "):
            result = result[:-2]
        return result + ")"

