# -*- coding: utf-8 -*-
"""Cullinan Parameter Base Classes

定义参数标记类的基础设施。

Author: Plumeink
"""

from typing import Any, Callable, List, Optional, Type, Union


class _UNSET:
    """哨兵类，表示未设置的值

    用于区分"未设置"和"设置为 None"的情况。
    使用单例模式确保全局唯一。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return '<UNSET>'

    def __bool__(self) -> bool:
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


# 全局 UNSET 单例
UNSET = _UNSET()


class Param:
    """参数标记基类

    所有参数类型 (Path, Query, Body, Header, File) 的基类。
    用于在函数签名中标记参数的来源和约束。

    Attributes:
        name: 参数名称 (默认使用函数参数名)
        type_: 目标类型
        required: 是否必填
        default: 默认值
        description: 参数描述
        alias: 别名 (从请求中读取时使用的键名)

    Validator Attributes:
        ge: 大于等于 (数值类型)
        le: 小于等于 (数值类型)
        gt: 大于 (数值类型)
        lt: 小于 (数值类型)
        min_length: 最小长度 (字符串/列表)
        max_length: 最大长度 (字符串/列表)
        regex: 正则表达式 (字符串)

    Example:
        # 作为类型注解使用
        @get_api(url="/users/{id}")
        async def get_user(self, id: Path(int), verbose: Query(bool, default=False)):
            pass

        # 直接实例化
        param = Param(int, name='age', required=True, ge=0, le=150)
    """

    __slots__ = (
        'name', 'type_', 'required', 'default', 'description', 'alias',
        'ge', 'le', 'gt', 'lt', 'min_length', 'max_length', 'regex',
        '_validators'
    )

    # 参数来源标识 (子类重写)
    _source: str = 'unknown'

    def __init__(
        self,
        type_: Type = str,
        *,
        name: str = None,
        required: bool = True,
        default: Any = UNSET,
        description: str = '',
        alias: str = None,
        # 数值约束
        ge: Union[int, float, None] = None,
        le: Union[int, float, None] = None,
        gt: Union[int, float, None] = None,
        lt: Union[int, float, None] = None,
        # 长度约束
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        # 正则约束
        regex: Optional[str] = None,
    ):
        """初始化参数标记

        Args:
            type_: 目标类型 (默认 str)
            name: 参数名称 (默认使用函数参数名)
            required: 是否必填 (有默认值时自动为 False)
            default: 默认值
            description: 参数描述 (用于文档生成)
            alias: 别名 (从请求中读取时使用的键名)
            ge: 大于等于约束
            le: 小于等于约束
            gt: 大于约束
            lt: 小于约束
            min_length: 最小长度约束
            max_length: 最大长度约束
            regex: 正则表达式约束
        """
        self.name = name
        self.type_ = type_
        self.default = default
        self.description = description
        self.alias = alias

        # 如果有默认值，则不是必填
        if default is not UNSET:
            self.required = False
        else:
            self.required = required

        # 存储约束条件
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex

        # 延迟构建验证器
        self._validators = None

    @property
    def source(self) -> str:
        """返回参数来源标识"""
        return self._source

    def get_validators(self) -> List[tuple]:
        """获取验证器列表 (延迟构建)

        Returns:
            验证器列表，每项为 (validator_name, value) 元组
        """
        if self._validators is None:
            self._validators = self._build_validators()
        return self._validators

    def _build_validators(self) -> List[tuple]:
        """构建验证器列表"""
        validators = []

        if self.ge is not None:
            validators.append(('ge', self.ge))
        if self.le is not None:
            validators.append(('le', self.le))
        if self.gt is not None:
            validators.append(('gt', self.gt))
        if self.lt is not None:
            validators.append(('lt', self.lt))
        if self.min_length is not None:
            validators.append(('min_length', self.min_length))
        if self.max_length is not None:
            validators.append(('max_length', self.max_length))
        if self.regex is not None:
            validators.append(('regex', self.regex))

        return validators

    def has_default(self) -> bool:
        """检查是否有默认值"""
        return self.default is not UNSET

    def get_default(self) -> Any:
        """获取默认值

        Returns:
            默认值，如果未设置则返回 None
        """
        if self.default is UNSET:
            return None
        return self.default

    def __repr__(self) -> str:
        parts = [f"{self.__class__.__name__}({self.type_.__name__}"]
        if self.name:
            parts.append(f", name={self.name!r}")
        if not self.required:
            parts.append(", required=False")
        if self.default is not UNSET:
            parts.append(f", default={self.default!r}")
        if self.alias:
            parts.append(f", alias={self.alias!r}")
        parts.append(")")
        return "".join(parts)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Param):
            return False
        return (
            self.name == other.name and
            self.type_ == other.type_ and
            self.required == other.required and
            self.default == other.default
        )

    def __hash__(self) -> int:
        return hash((self.name, self.type_, self.required))

