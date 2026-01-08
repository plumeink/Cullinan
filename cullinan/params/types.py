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
        multiple: 是否支持多文件上传
        max_count: 多文件上传时的最大文件数量

    Example:
        # 单文件上传
        @post_api(url="/upload")
        async def upload(
            self,
            avatar: File(required=True, max_size=5*1024*1024),  # 5MB
        ):
            print(avatar.filename)
            print(avatar.size)
            avatar.save('/uploads/')

        # 带类型校验
        @post_api(url="/upload-image")
        async def upload_image(
            self,
            image: File(allowed_types=['image/png', 'image/jpeg', 'image/*']),
        ):
            pass

        # 多文件上传
        @post_api(url="/upload-multiple")
        async def upload_multiple(
            self,
            files: File(multiple=True, max_count=10),
        ):
            for f in files:
                print(f.filename)
    """
    _source = 'file'

    # 扩展 __slots__
    __slots__ = ('max_size', 'allowed_types', 'multiple', 'max_count', 'min_size')

    def __init__(
        self,
        *,
        name: str = None,
        required: bool = True,
        description: str = '',
        alias: str = None,
        max_size: Optional[int] = None,
        min_size: Optional[int] = None,
        allowed_types: Optional[List[str]] = None,
        multiple: bool = False,
        max_count: Optional[int] = None,
    ):
        """初始化文件参数

        Args:
            name: 参数名称
            required: 是否必填
            description: 参数描述
            alias: 别名 (表单字段名)
            max_size: 最大文件大小 (bytes)
            min_size: 最小文件大小 (bytes)
            allowed_types: 允许的 MIME 类型列表，支持通配符如 'image/*'
            multiple: 是否支持多文件上传
            max_count: 多文件上传时的最大文件数量
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
        self.min_size = min_size
        self.allowed_types = allowed_types or []
        self.multiple = multiple
        self.max_count = max_count

    def validate_file(self, file_info) -> None:
        """校验文件

        Args:
            file_info: FileInfo 实例

        Raises:
            ValueError: 校验失败
        """
        # 校验文件大小
        if self.max_size is not None and file_info.size > self.max_size:
            raise ValueError(
                f"File '{file_info.filename}' size ({file_info.size} bytes) "
                f"exceeds maximum allowed size ({self.max_size} bytes)"
            )

        if self.min_size is not None and file_info.size < self.min_size:
            raise ValueError(
                f"File '{file_info.filename}' size ({file_info.size} bytes) "
                f"is below minimum required size ({self.min_size} bytes)"
            )

        # 校验 MIME 类型
        if self.allowed_types:
            if not self._match_content_type(file_info.content_type):
                raise ValueError(
                    f"File '{file_info.filename}' type '{file_info.content_type}' "
                    f"is not allowed. Allowed types: {self.allowed_types}"
                )

    def validate_file_list(self, file_list) -> None:
        """校验文件列表

        Args:
            file_list: FileList 实例

        Raises:
            ValueError: 校验失败
        """
        # 校验文件数量
        if self.max_count is not None and len(file_list) > self.max_count:
            raise ValueError(
                f"Number of files ({len(file_list)}) exceeds maximum allowed ({self.max_count})"
            )

        # 校验每个文件
        for file_info in file_list:
            self.validate_file(file_info)

    def _match_content_type(self, content_type: str) -> bool:
        """检查 MIME 类型是否匹配允许列表

        Args:
            content_type: 文件的 MIME 类型

        Returns:
            是否匹配
        """
        for pattern in self.allowed_types:
            if pattern == '*/*' or pattern == '*':
                return True
            if pattern.endswith('/*'):
                # 通配符匹配
                prefix = pattern[:-1]  # 'image/'
                if content_type.startswith(prefix):
                    return True
            elif content_type == pattern:
                return True
        return False

    def __repr__(self) -> str:
        parts = ["File("]
        if self.name:
            parts.append(f"name={self.name!r}, ")
        if not self.required:
            parts.append("required=False, ")
        if self.max_size:
            parts.append(f"max_size={self.max_size}, ")
        if self.min_size:
            parts.append(f"min_size={self.min_size}, ")
        if self.allowed_types:
            parts.append(f"allowed_types={self.allowed_types!r}, ")
        if self.multiple:
            parts.append("multiple=True, ")
        if self.max_count:
            parts.append(f"max_count={self.max_count}, ")
        result = "".join(parts)
        if result.endswith(", "):
            result = result[:-2]
        return result + ")"

