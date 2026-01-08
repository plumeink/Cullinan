# -*- coding: utf-8 -*-
"""Cullinan Parameter Resolver

参数解析编排器，协调各层完成参数解析。

Author: Plumeink
"""

import inspect
import dataclasses
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, get_type_hints

from .base import Param, UNSET
from .types import Path, Query, Body, Header, File
from .converter import TypeConverter, ConversionError
from .auto import Auto, AutoType
from .dynamic import DynamicBody
from .validator import ParamValidator, ValidationError
from .model import ModelResolver, ModelError
from .file_info import FileInfo, FileList
from .model_handlers import get_model_handler_registry, ModelHandlerError


class ResolveError(Exception):
    """参数解析错误

    Attributes:
        message: 错误消息
        errors: 错误详情列表
    """

    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'message': self.message,
            'errors': self.errors,
        }


class ParamResolver:
    """参数解析编排器

    协调传输层、转换层、数据层完成参数解析。

    Features:
    - 从函数签名推导参数配置
    - 支持传统装饰器配置
    - 自动类型转换
    - 参数校验
    - dataclass / DynamicBody 支持

    Example:
        @post_api(url="/users")
        async def create_user(
            self,
            name: Body(str, required=True),
            age: Body(int, default=0, ge=0),
        ):
            pass

        # ParamResolver 会自动解析 name 和 age 参数
    """

    # 签名缓存
    _signature_cache: Dict[Callable, inspect.Signature] = {}

    @classmethod
    def get_signature(cls, func: Callable) -> inspect.Signature:
        """获取函数签名 (带缓存)

        Args:
            func: 函数

        Returns:
            函数签名
        """
        if func not in cls._signature_cache:
            cls._signature_cache[func] = inspect.signature(func)
        return cls._signature_cache[func]

    @classmethod
    def analyze_params(cls, func: Callable) -> Dict[str, dict]:
        """分析函数参数配置

        Args:
            func: 控制器方法

        Returns:
            参数配置字典 {param_name: {source, type, param_spec, ...}}
        """
        sig = cls.get_signature(func)
        type_hints = {}
        try:
            type_hints = get_type_hints(func)
        except Exception:
            pass

        params_config = {}

        for name, param in sig.parameters.items():
            # 跳过 self 参数
            if name == 'self':
                continue

            config = {
                'name': name,
                'source': 'unknown',
                'type': str,
                'required': True,
                'default': UNSET,
                'param_spec': None,
            }

            # 检查类型注解
            annotation = type_hints.get(name, param.annotation)

            if annotation is inspect.Parameter.empty:
                annotation = None

            # 检查是否是 Param 实例
            if isinstance(annotation, Param):
                param_spec = annotation
                config['source'] = param_spec.source
                config['type'] = param_spec.type_
                config['required'] = param_spec.required
                config['default'] = param_spec.default
                config['param_spec'] = param_spec
                # 使用参数名作为 name（如果未指定）
                if param_spec.name is None:
                    param_spec.name = name

            # 检查是否是 DynamicBody
            elif annotation is DynamicBody:
                config['source'] = 'body'
                config['type'] = DynamicBody
                config['required'] = False

            # 检查是否是可处理的模型类型（通过注册表）
            elif get_model_handler_registry().can_handle(annotation):
                handler = get_model_handler_registry().get_handler(annotation)
                config['source'] = handler.get_source()
                config['type'] = annotation
                config['required'] = handler.is_required_by_default()
                config['model_handler'] = handler

            # 检查是否是 AutoType
            elif annotation is AutoType:
                config['source'] = 'auto'
                config['type'] = AutoType

            # 普通类型注解
            elif annotation is not None:
                config['type'] = annotation

            # 检查默认值
            if param.default is not inspect.Parameter.empty:
                config['default'] = param.default
                config['required'] = False

            params_config[name] = config

        return params_config

    @classmethod
    def resolve(
        cls,
        func: Callable,
        request: Any,
        url_params: Dict[str, Any] = None,
        query_params: Dict[str, Any] = None,
        body_data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        files: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """解析请求参数

        Args:
            func: 控制器方法
            request: Tornado request 对象
            url_params: URL 路径参数
            query_params: 查询参数
            body_data: 请求体数据 (已解码)
            headers: 请求头
            files: 上传的文件

        Returns:
            解析后的参数字典 {param_name: value}

        Raises:
            ResolveError: 解析失败
        """
        url_params = url_params or {}
        query_params = query_params or {}
        body_data = body_data or {}
        headers = headers or {}
        files = files or {}

        # 分析参数配置
        params_config = cls.analyze_params(func)

        result = {}
        errors = []

        for name, config in params_config.items():
            try:
                value = cls._resolve_param(
                    name, config,
                    url_params, query_params, body_data, headers, files
                )
                result[name] = value
            except (ConversionError, ValidationError, ModelError) as e:
                errors.append({
                    'param': name,
                    'error': str(e),
                    'type': type(e).__name__,
                })

        if errors:
            raise ResolveError(
                f"Failed to resolve {len(errors)} parameter(s)",
                errors=errors
            )

        return result

    @classmethod
    def _resolve_param(
        cls,
        name: str,
        config: dict,
        url_params: Dict[str, Any],
        query_params: Dict[str, Any],
        body_data: Dict[str, Any],
        headers: Dict[str, str],
        files: Dict[str, Any],
    ) -> Any:
        """解析单个参数

        Args:
            name: 参数名
            config: 参数配置
            各种来源数据...

        Returns:
            解析后的值
        """
        source = config['source']
        target_type = config['type']
        required = config['required']
        default = config['default']
        param_spec = config.get('param_spec')

        # 获取别名
        alias = name
        if param_spec and param_spec.alias:
            alias = param_spec.alias

        # 根据来源获取原始值
        raw_value = None

        if source == 'path':
            raw_value = url_params.get(alias) or url_params.get(name)
        elif source == 'query':
            raw_value = query_params.get(alias) or query_params.get(name)
        elif source == 'body':
            # 特殊处理 DynamicBody 和模型类型
            if target_type is DynamicBody:
                return DynamicBody(body_data)
            elif config.get('model_handler'):
                # 使用注册的模型处理器
                return config['model_handler'].resolve(target_type, body_data)
            else:
                raw_value = body_data.get(alias) or body_data.get(name)
        elif source == 'header':
            raw_value = headers.get(alias) or headers.get(name)
        elif source == 'file':
            raw_value = files.get(alias) or files.get(name)
            # 处理文件参数
            if raw_value is not None:
                return cls._resolve_file_param(raw_value, param_spec, name)
        elif source == 'auto':
            # Auto 类型：依次查找各来源
            raw_value = (
                url_params.get(name) or
                query_params.get(name) or
                body_data.get(name)
            )
        else:
            # 未知来源：尝试从多处获取
            raw_value = (
                url_params.get(name) or
                query_params.get(name) or
                body_data.get(name)
            )

        # 处理 None 值
        if raw_value is None:
            if default is not UNSET:
                return default
            if required:
                raise ValidationError(
                    f"Parameter '{name}' is required",
                    param_name=name,
                    constraint='required'
                )
            return None

        # 类型转换
        if target_type is AutoType:
            converted = Auto.infer(raw_value)
        elif target_type is DynamicBody:
            if isinstance(raw_value, dict):
                converted = DynamicBody(raw_value)
            else:
                converted = raw_value
        elif config.get('model_handler'):
            # 使用注册的模型处理器
            if isinstance(raw_value, dict):
                converted = config['model_handler'].resolve(target_type, raw_value)
            else:
                converted = raw_value
        else:
            converted = TypeConverter.convert(raw_value, target_type)

        # 参数校验
        if param_spec:
            ParamValidator.validate_param(param_spec, converted, name)

        return converted

    @classmethod
    def clear_cache(cls) -> None:
        """清空签名缓存"""
        cls._signature_cache.clear()

    @classmethod
    def _resolve_file_param(
        cls,
        raw_value: Any,
        param_spec: File,
        name: str,
    ) -> Any:
        """解析文件参数

        Args:
            raw_value: 原始文件数据 (来自 Tornado)
            param_spec: File 参数规格
            name: 参数名

        Returns:
            FileInfo 或 FileList
        """
        # 处理列表格式 (Tornado 的 request.files 返回列表)
        if isinstance(raw_value, list):
            file_list = []
            for item in raw_value:
                if isinstance(item, dict):
                    file_info = FileInfo.from_tornado_file(item)
                elif isinstance(item, FileInfo):
                    file_info = item
                else:
                    # 尝试作为字典处理
                    file_info = FileInfo(
                        filename=getattr(item, 'filename', 'unknown'),
                        body=getattr(item, 'body', b''),
                        content_type=getattr(item, 'content_type', None),
                    )
                file_list.append(file_info)

            if param_spec and param_spec.multiple:
                # 多文件模式
                result = FileList(file_list)
                if param_spec:
                    param_spec.validate_file_list(result)
                return result
            elif file_list:
                # 单文件模式，取第一个
                result = file_list[0]
                if param_spec:
                    param_spec.validate_file(result)
                return result
            else:
                return None

        # 处理单个文件
        if isinstance(raw_value, dict):
            file_info = FileInfo.from_tornado_file(raw_value)
        elif isinstance(raw_value, FileInfo):
            file_info = raw_value
        else:
            file_info = FileInfo(
                filename=getattr(raw_value, 'filename', 'unknown'),
                body=getattr(raw_value, 'body', b''),
                content_type=getattr(raw_value, 'content_type', None),
            )

        if param_spec:
            param_spec.validate_file(file_info)

        return file_info

