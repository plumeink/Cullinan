# -*- coding: utf-8 -*-
"""Cullinan Parameter Validator

参数校验器，验证参数值是否满足约束条件。

Author: Plumeink
"""

import re
from typing import Any, List, Optional, Tuple


class ValidationError(Exception):
    """参数校验错误

    Attributes:
        message: 错误消息
        param_name: 参数名
        value: 原始值
        constraint: 约束条件
    """

    def __init__(
        self,
        message: str,
        param_name: str = None,
        value: Any = None,
        constraint: str = None
    ):
        super().__init__(message)
        self.message = message
        self.param_name = param_name
        self.value = value
        self.constraint = constraint

    def __repr__(self) -> str:
        return f"ValidationError({self.message!r}, param={self.param_name!r})"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'message': self.message,
            'param': self.param_name,
            'value': self.value,
            'constraint': self.constraint,
        }


class ParamValidator:
    """参数校验器

    根据验证规则校验参数值。

    支持的校验规则:
    - required: 必填
    - ge: 大于等于
    - le: 小于等于
    - gt: 大于
    - lt: 小于
    - min_length: 最小长度
    - max_length: 最大长度
    - regex: 正则表达式

    Example:
        validator = ParamValidator()

        # 单个校验
        validator.validate_ge(10, 5, 'age')  # OK
        validator.validate_ge(3, 5, 'age')   # raises ValidationError

        # 批量校验
        validators = [('ge', 0), ('le', 100)]
        validator.validate(50, validators, 'score')  # OK
    """

    @classmethod
    def validate(
        cls,
        value: Any,
        validators: List[Tuple[str, Any]],
        param_name: str = None
    ) -> None:
        """批量校验参数值

        Args:
            value: 参数值
            validators: 校验规则列表，每项为 (rule_name, rule_value)
            param_name: 参数名 (用于错误消息)

        Raises:
            ValidationError: 校验失败
        """
        for rule_name, rule_value in validators:
            method = getattr(cls, f'validate_{rule_name}', None)
            if method:
                method(value, rule_value, param_name)
            else:
                raise ValueError(f"Unknown validation rule: {rule_name}")

    @classmethod
    def validate_required(
        cls,
        value: Any,
        required: bool,
        param_name: str = None
    ) -> None:
        """校验必填

        Args:
            value: 参数值
            required: 是否必填
            param_name: 参数名

        Raises:
            ValidationError: 值为 None 但必填
        """
        if required and value is None:
            raise ValidationError(
                f"Parameter '{param_name}' is required",
                param_name=param_name,
                value=value,
                constraint='required'
            )

    @classmethod
    def validate_ge(
        cls,
        value: Any,
        min_value: float,
        param_name: str = None
    ) -> None:
        """校验大于等于

        Args:
            value: 参数值
            min_value: 最小值
            param_name: 参数名
        """
        if value is None:
            return
        if value < min_value:
            raise ValidationError(
                f"Parameter '{param_name}' must be >= {min_value}, got {value}",
                param_name=param_name,
                value=value,
                constraint=f'ge:{min_value}'
            )

    @classmethod
    def validate_le(
        cls,
        value: Any,
        max_value: float,
        param_name: str = None
    ) -> None:
        """校验小于等于

        Args:
            value: 参数值
            max_value: 最大值
            param_name: 参数名
        """
        if value is None:
            return
        if value > max_value:
            raise ValidationError(
                f"Parameter '{param_name}' must be <= {max_value}, got {value}",
                param_name=param_name,
                value=value,
                constraint=f'le:{max_value}'
            )

    @classmethod
    def validate_gt(
        cls,
        value: Any,
        min_value: float,
        param_name: str = None
    ) -> None:
        """校验大于

        Args:
            value: 参数值
            min_value: 最小值 (不含)
            param_name: 参数名
        """
        if value is None:
            return
        if value <= min_value:
            raise ValidationError(
                f"Parameter '{param_name}' must be > {min_value}, got {value}",
                param_name=param_name,
                value=value,
                constraint=f'gt:{min_value}'
            )

    @classmethod
    def validate_lt(
        cls,
        value: Any,
        max_value: float,
        param_name: str = None
    ) -> None:
        """校验小于

        Args:
            value: 参数值
            max_value: 最大值 (不含)
            param_name: 参数名
        """
        if value is None:
            return
        if value >= max_value:
            raise ValidationError(
                f"Parameter '{param_name}' must be < {max_value}, got {value}",
                param_name=param_name,
                value=value,
                constraint=f'lt:{max_value}'
            )

    @classmethod
    def validate_min_length(
        cls,
        value: Any,
        min_length: int,
        param_name: str = None
    ) -> None:
        """校验最小长度

        Args:
            value: 参数值 (字符串或列表)
            min_length: 最小长度
            param_name: 参数名
        """
        if value is None:
            return
        if len(value) < min_length:
            raise ValidationError(
                f"Parameter '{param_name}' length must be >= {min_length}, got {len(value)}",
                param_name=param_name,
                value=value,
                constraint=f'min_length:{min_length}'
            )

    @classmethod
    def validate_max_length(
        cls,
        value: Any,
        max_length: int,
        param_name: str = None
    ) -> None:
        """校验最大长度

        Args:
            value: 参数值 (字符串或列表)
            max_length: 最大长度
            param_name: 参数名
        """
        if value is None:
            return
        if len(value) > max_length:
            raise ValidationError(
                f"Parameter '{param_name}' length must be <= {max_length}, got {len(value)}",
                param_name=param_name,
                value=value,
                constraint=f'max_length:{max_length}'
            )

    @classmethod
    def validate_regex(
        cls,
        value: Any,
        pattern: str,
        param_name: str = None
    ) -> None:
        """校验正则表达式

        Args:
            value: 参数值
            pattern: 正则表达式
            param_name: 参数名
        """
        if value is None:
            return
        if not isinstance(value, str):
            value = str(value)
        if not re.match(pattern, value):
            raise ValidationError(
                f"Parameter '{param_name}' does not match pattern '{pattern}'",
                param_name=param_name,
                value=value,
                constraint=f'regex:{pattern}'
            )

    @classmethod
    def validate_param(cls, param, value: Any, name: str = None) -> None:
        """根据 Param 对象校验值

        Args:
            param: Param 实例
            value: 参数值
            name: 参数名 (覆盖 param.name)

        Raises:
            ValidationError: 校验失败
        """
        param_name = name or param.name

        # 必填校验
        if param.required and value is None:
            raise ValidationError(
                f"Parameter '{param_name}' is required",
                param_name=param_name,
                value=value,
                constraint='required'
            )

        # 获取并执行所有验证器
        validators = param.get_validators()
        if validators:
            cls.validate(value, validators, param_name)

