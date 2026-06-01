# -*- coding: utf-8 -*-
"""Cullinan Pydantic Model Handler

可选的 Pydantic 模型处理器。

Pydantic 是可选依赖，此模块仅在 Pydantic 可用时才能正常工作。

Author: Plumeink
"""

from typing import Any, Dict, Type

from .base import ModelHandler, ModelHandlerError


def _is_pydantic_available() -> bool:
    """检查 Pydantic 是否可用"""
    try:
        import pydantic
        return True
    except ImportError:
        return False


def _get_pydantic_version() -> int:
    """获取 Pydantic 主版本号"""
    try:
        import pydantic
        version_str = getattr(pydantic, 'VERSION', getattr(pydantic, '__version__', '1.0'))
        return int(version_str.split('.')[0])
    except Exception:
        return 0


class PydanticHandler(ModelHandler):
    """Pydantic 模型处理器

    可选处理器，用于解析 Pydantic BaseModel。

    Features:
    - 支持 Pydantic v1 和 v2
    - 完整的 Pydantic 校验
    - 嵌套模型解析
    - 自动类型转换

    Note:
        此处理器仅在 Pydantic 已安装时可用。
    """

    priority = 50  # 高于 dataclass
    name = "pydantic"

    def __init__(self):
        if not _is_pydantic_available():
            raise ImportError("Pydantic is not installed")

        self._version = _get_pydantic_version()
        self._base_model = None
        self._load_pydantic()

    def _load_pydantic(self):
        """加载 Pydantic"""
        from pydantic import BaseModel
        self._base_model = BaseModel

    def can_handle(self, type_: Type) -> bool:
        """检查是否是 Pydantic BaseModel"""
        if type_ is None:
            return False

        try:
            return isinstance(type_, type) and issubclass(type_, self._base_model)
        except Exception:
            return False

    def resolve(self, model_class: Type, data: Dict[str, Any]) -> Any:
        """解析数据为 Pydantic 模型实例"""
        if not self.can_handle(model_class):
            raise ModelHandlerError(
                f"{model_class} is not a Pydantic BaseModel",
                model_class=model_class,
                handler_name=self.name,
            )

        if data is None:
            data = {}

        try:
            if self._version >= 2:
                return model_class.model_validate(data)
            else:
                return model_class.parse_obj(data)
        except Exception as e:
            error_type = type(e).__name__
            if 'ValidationError' in error_type:
                raise ModelHandlerError(
                    f"Validation failed for {model_class.__name__}",
                    model_class=model_class,
                    errors=self._extract_errors(e),
                    handler_name=self.name,
                )
            raise ModelHandlerError(
                f"Failed to resolve {model_class.__name__}: {e}",
                model_class=model_class,
                handler_name=self.name,
            )

    def to_dict(self, instance: Any) -> Dict[str, Any]:
        """将 Pydantic 模型实例转换为字典"""
        if self._version >= 2:
            return instance.model_dump()
        else:
            return instance.dict()

    def to_json(self, instance: Any) -> str:
        """将 Pydantic 模型实例转换为 JSON 字符串"""
        if self._version >= 2:
            return instance.model_dump_json()
        else:
            return instance.json()

    def get_schema(self, model_class: Type) -> Dict[str, Any]:
        """获取 Pydantic 模型的 JSON Schema"""
        if not self.can_handle(model_class):
            raise ModelHandlerError(
                f"{model_class} is not a Pydantic BaseModel",
                model_class=model_class,
                handler_name=self.name,
            )

        if self._version >= 2:
            return model_class.model_json_schema()
        else:
            return model_class.schema()

    def _extract_errors(self, error) -> list:
        """从 Pydantic ValidationError 提取错误信息"""
        errors = []
        try:
            for err in error.errors():
                errors.append({
                    'loc': list(err.get('loc', [])),
                    'msg': err.get('msg', ''),
                    'type': err.get('type', ''),
                })
        except Exception:
            errors.append({'msg': str(error)})
        return errors

