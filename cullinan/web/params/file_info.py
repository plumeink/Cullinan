# -*- coding: utf-8 -*-
"""Cullinan FileInfo

文件信息容器，用于处理上传的文件。

Author: Plumeink
"""

import os
import mimetypes
from typing import Optional, List, BinaryIO
from io import BytesIO


class FileInfo:
    """文件信息容器

    封装上传文件的元数据和内容，提供便捷的访问方法。

    Attributes:
        filename: 原始文件名
        content_type: MIME 类型
        body: 文件内容 (bytes)
        size: 文件大小 (bytes)

    Example:
        @post_api(url='/upload')
        async def upload(self, avatar: File()):
            # avatar 是 FileInfo 实例
            print(f"Filename: {avatar.filename}")
            print(f"Size: {avatar.size} bytes")
            print(f"Type: {avatar.content_type}")

            # 保存文件
            avatar.save('/path/to/uploads/')

            # 或读取内容
            content = avatar.read()
    """

    __slots__ = ('_filename', '_content_type', '_body', '_field_name')

    def __init__(
        self,
        filename: str,
        body: bytes,
        content_type: str = None,
        field_name: str = None,
    ):
        """初始化文件信息

        Args:
            filename: 原始文件名
            body: 文件内容
            content_type: MIME 类型，如果不提供则自动检测
            field_name: 表单字段名
        """
        self._filename = filename
        self._body = body if body is not None else b''
        self._content_type = content_type or self._detect_content_type(filename)
        self._field_name = field_name

    @property
    def filename(self) -> str:
        """原始文件名"""
        return self._filename

    @property
    def content_type(self) -> str:
        """MIME 类型"""
        return self._content_type

    @property
    def body(self) -> bytes:
        """文件内容 (bytes)"""
        return self._body

    @property
    def size(self) -> int:
        """文件大小 (bytes)"""
        return len(self._body)

    @property
    def field_name(self) -> Optional[str]:
        """表单字段名"""
        return self._field_name

    @property
    def extension(self) -> str:
        """文件扩展名 (不含点)"""
        _, ext = os.path.splitext(self._filename)
        return ext[1:] if ext else ''

    @property
    def basename(self) -> str:
        """文件基本名 (不含扩展名)"""
        name, _ = os.path.splitext(self._filename)
        return name

    def read(self) -> bytes:
        """读取文件内容

        Returns:
            文件内容 (bytes)
        """
        return self._body

    def read_text(self, encoding: str = 'utf-8') -> str:
        """以文本形式读取文件内容

        Args:
            encoding: 文本编码

        Returns:
            文件内容 (str)
        """
        return self._body.decode(encoding)

    def stream(self) -> BinaryIO:
        """获取文件流

        Returns:
            BytesIO 对象
        """
        return BytesIO(self._body)

    def save(self, path: str, filename: str = None) -> str:
        """保存文件到磁盘

        Args:
            path: 保存目录或完整路径
            filename: 自定义文件名，不提供则使用原始文件名

        Returns:
            保存的完整路径
        """
        if os.path.isdir(path):
            # 如果是目录，拼接文件名
            save_name = filename or self._filename
            full_path = os.path.join(path, save_name)
        else:
            # 如果是完整路径
            full_path = path

        # 确保目录存在
        dir_path = os.path.dirname(full_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(full_path, 'wb') as f:
            f.write(self._body)

        return full_path

    def is_image(self) -> bool:
        """检查是否是图片文件"""
        return self._content_type.startswith('image/')

    def is_video(self) -> bool:
        """检查是否是视频文件"""
        return self._content_type.startswith('video/')

    def is_audio(self) -> bool:
        """检查是否是音频文件"""
        return self._content_type.startswith('audio/')

    def is_text(self) -> bool:
        """检查是否是文本文件"""
        return self._content_type.startswith('text/')

    def is_pdf(self) -> bool:
        """检查是否是 PDF 文件"""
        return self._content_type == 'application/pdf'

    def match_type(self, pattern: str) -> bool:
        """检查 MIME 类型是否匹配模式

        Args:
            pattern: MIME 类型模式，支持通配符如 'image/*'

        Returns:
            是否匹配
        """
        if pattern == '*/*' or pattern == '*':
            return True

        if pattern.endswith('/*'):
            # 通配符匹配，如 image/*
            prefix = pattern[:-1]  # 'image/'
            return self._content_type.startswith(prefix)

        return self._content_type == pattern

    @staticmethod
    def _detect_content_type(filename: str) -> str:
        """根据文件名检测 MIME 类型

        Args:
            filename: 文件名

        Returns:
            MIME 类型
        """
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'

    @classmethod
    def from_tornado_file(cls, file_obj) -> 'FileInfo':
        """从 Tornado HTTPFile 对象创建 FileInfo

        Args:
            file_obj: Tornado HTTPFile 对象

        Returns:
            FileInfo 实例
        """
        return cls(
            filename=file_obj.get('filename', 'unknown'),
            body=file_obj.get('body', b''),
            content_type=file_obj.get('content_type'),
            field_name=file_obj.get('field_name'),
        )

    def __repr__(self) -> str:
        return f"FileInfo(filename={self._filename!r}, size={self.size}, type={self._content_type!r})"

    def __str__(self) -> str:
        return f"{self._filename} ({self.size} bytes, {self._content_type})"

    def __len__(self) -> int:
        return self.size

    def __bool__(self) -> bool:
        return self.size > 0


class FileList:
    """文件列表容器

    用于处理多文件上传的场景。

    Example:
        @post_api(url='/upload-multiple')
        async def upload(self, files: File(multiple=True)):
            for f in files:
                print(f.filename)
            print(f"Total: {len(files)} files")
    """

    __slots__ = ('_files',)

    def __init__(self, files: List[FileInfo] = None):
        """初始化文件列表

        Args:
            files: FileInfo 列表
        """
        self._files = files or []

    def __iter__(self):
        return iter(self._files)

    def __len__(self) -> int:
        return len(self._files)

    def __getitem__(self, index: int) -> FileInfo:
        return self._files[index]

    def __bool__(self) -> bool:
        return len(self._files) > 0

    @property
    def count(self) -> int:
        """文件数量"""
        return len(self._files)

    @property
    def total_size(self) -> int:
        """总文件大小"""
        return sum(f.size for f in self._files)

    @property
    def filenames(self) -> List[str]:
        """所有文件名"""
        return [f.filename for f in self._files]

    def first(self) -> Optional[FileInfo]:
        """获取第一个文件"""
        return self._files[0] if self._files else None

    def last(self) -> Optional[FileInfo]:
        """获取最后一个文件"""
        return self._files[-1] if self._files else None

    def filter_by_type(self, pattern: str) -> 'FileList':
        """按 MIME 类型过滤文件

        Args:
            pattern: MIME 类型模式

        Returns:
            过滤后的 FileList
        """
        return FileList([f for f in self._files if f.match_type(pattern)])

    def save_all(self, directory: str) -> List[str]:
        """保存所有文件到目录

        Args:
            directory: 保存目录

        Returns:
            保存的文件路径列表
        """
        paths = []
        for f in self._files:
            path = f.save(directory)
            paths.append(path)
        return paths

    def __repr__(self) -> str:
        return f"FileList({len(self._files)} files, total {self.total_size} bytes)"

