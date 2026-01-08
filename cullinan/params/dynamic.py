# -*- coding: utf-8 -*-
"""Cullinan DynamicBody

动态请求体类，支持属性访问方式。

Author: Plumeink
"""

from typing import Any, Dict, Iterator, KeysView, ValuesView, ItemsView, Optional, List, Union


class _Empty:
    """空值哨兵类，用于区分 None 和真正的空"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return '<EMPTY>'

    def __bool__(self):
        return False


# 空值哨兵
EMPTY = _Empty()


class DynamicBody:
    """动态请求体类

    提供类似 JavaScript 对象的属性访问方式，避免频繁使用 .get()。

    Features:
    - 属性访问: body.name
    - 安全访问: body.get('name', default)
    - 嵌套安全访问: body.get_nested('user.address.city', 'Unknown')
    - 快捷判空: body.has('name'), body.is_empty(), body.is_not_empty()
    - 字典兼容: body['name'], 'name' in body
    - 迭代支持: for key in body
    - 可变性: body.new_field = value
    - 嵌套访问: body.user.name (嵌套字典自动转换)
    - 链式安全访问: body.safe.user.address.city (不抛异常)

    Example:
        body = DynamicBody({'name': 'test', 'age': 18, 'user': {'id': 1}})

        # 属性访问
        print(body.name)  # 'test'
        print(body.age)   # 18

        # 嵌套访问
        print(body.user.id)  # 1

        # 安全访问
        print(body.get('email', 'default@example.com'))

        # 嵌套安全访问
        print(body.get_nested('user.address.city', 'Unknown'))

        # 快捷判空
        if body.has('name'):
            print('has name')
        if body.is_not_empty():
            print('body has data')

        # 链式安全访问 (不抛异常)
        city = body.safe.user.address.city.value_or('Unknown')

        # 检查存在性
        if 'name' in body:
            print('has name')

        # 设置新字段
        body.email = 'test@example.com'

        # 转换为字典
        data = body.to_dict()
    """

    __slots__ = ('_data',)

    def __init__(self, data: Dict[str, Any] = None):
        """初始化动态请求体

        Args:
            data: 原始数据字典
        """
        object.__setattr__(self, '_data', data if data is not None else {})

    def __getattr__(self, name: str) -> Any:
        """属性访问

        Args:
            name: 属性名

        Returns:
            属性值 (嵌套字典自动转换为 DynamicBody)

        Raises:
            AttributeError: 属性不存在
        """
        data = object.__getattribute__(self, '_data')
        if name in data:
            value = data[name]
            # 嵌套字典自动转换为 DynamicBody
            if isinstance(value, dict):
                return DynamicBody(value)
            return value
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """设置属性

        Args:
            name: 属性名
            value: 属性值
        """
        if name == '_data':
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value

    def __delattr__(self, name: str) -> None:
        """删除属性

        Args:
            name: 属性名
        """
        data = object.__getattribute__(self, '_data')
        if name in data:
            del data[name]
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __getitem__(self, key: str) -> Any:
        """字典式访问

        Args:
            key: 键名

        Returns:
            对应的值
        """
        value = self._data[key]
        if isinstance(value, dict):
            return DynamicBody(value)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """字典式设置

        Args:
            key: 键名
            value: 值
        """
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        """字典式删除

        Args:
            key: 键名
        """
        del self._data[key]

    def __contains__(self, name: str) -> bool:
        """检查键是否存在

        Args:
            name: 键名

        Returns:
            是否存在
        """
        return name in self._data

    def __iter__(self) -> Iterator[str]:
        """迭代键名"""
        return iter(self._data)

    def __len__(self) -> int:
        """返回字段数量"""
        return len(self._data)

    def __bool__(self) -> bool:
        """布尔值判断 (非空为 True)"""
        return bool(self._data)

    def __repr__(self) -> str:
        return f"DynamicBody({self._data!r})"

    def __str__(self) -> str:
        return str(self._data)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, DynamicBody):
            return self._data == other._data
        if isinstance(other, dict):
            return self._data == other
        return False

    # =========================================================================
    # 字典兼容方法
    # =========================================================================

    def get(self, name: str, default: Any = None) -> Any:
        """安全获取属性值

        Args:
            name: 属性名
            default: 默认值

        Returns:
            属性值或默认值

        Example:
            email = body.get('email', 'default@example.com')
        """
        value = self._data.get(name, default)
        if isinstance(value, dict):
            return DynamicBody(value)
        return value

    def keys(self) -> KeysView[str]:
        """返回所有键"""
        return self._data.keys()

    def values(self) -> ValuesView[Any]:
        """返回所有值"""
        return self._data.values()

    def items(self) -> ItemsView[str, Any]:
        """返回所有键值对"""
        return self._data.items()

    def to_dict(self) -> Dict[str, Any]:
        """转换为普通字典

        Returns:
            字典副本
        """
        return dict(self._data)

    def update(self, data: Dict[str, Any] = None, **kwargs) -> None:
        """更新数据

        Args:
            data: 要合并的字典
            **kwargs: 要设置的键值对
        """
        if data:
            self._data.update(data)
        if kwargs:
            self._data.update(kwargs)

    def pop(self, name: str, *default) -> Any:
        """弹出并返回值

        Args:
            name: 键名
            *default: 默认值 (可选)

        Returns:
            被弹出的值
        """
        return self._data.pop(name, *default)

    def setdefault(self, name: str, default: Any = None) -> Any:
        """设置默认值并返回

        Args:
            name: 键名
            default: 默认值

        Returns:
            现有值或设置的默认值
        """
        return self._data.setdefault(name, default)

    def clear(self) -> None:
        """清空所有数据"""
        self._data.clear()

    # =========================================================================
    # 快捷判空方法
    # =========================================================================

    def has(self, name: str) -> bool:
        """检查属性是否存在

        比 'name' in body 更语义化的方法。

        Args:
            name: 属性名

        Returns:
            属性是否存在

        Example:
            if body.has('email'):
                send_email(body.email)
        """
        return name in self._data

    def has_value(self, name: str) -> bool:
        """检查属性是否存在且值非空（不为 None、空字符串、空列表等）

        Args:
            name: 属性名

        Returns:
            属性是否存在且有值

        Example:
            if body.has_value('email'):
                send_email(body.email)  # 确保 email 不是 None 或 ''
        """
        if name not in self._data:
            return False
        value = self._data[name]
        # None, '', [], {}, 0, False 等都返回 False
        return bool(value)

    def is_empty(self) -> bool:
        """检查是否为空

        Returns:
            如果没有任何数据返回 True

        Example:
            if body.is_empty():
                return {'error': 'No data provided'}
        """
        return len(self._data) == 0

    def is_not_empty(self) -> bool:
        """检查是否非空

        Returns:
            如果有数据返回 True

        Example:
            if body.is_not_empty():
                process(body)
        """
        return len(self._data) > 0

    def is_null(self, name: str) -> bool:
        """检查属性值是否为 None

        Args:
            name: 属性名

        Returns:
            如果属性不存在或值为 None 返回 True

        Example:
            if body.is_null('optional_field'):
                body.optional_field = default_value
        """
        return self._data.get(name) is None

    def is_not_null(self, name: str) -> bool:
        """检查属性值是否不为 None

        Args:
            name: 属性名

        Returns:
            如果属性存在且值不为 None 返回 True

        Example:
            if body.is_not_null('callback_url'):
                notify(body.callback_url)
        """
        return name in self._data and self._data[name] is not None

    # =========================================================================
    # 嵌套安全访问方法
    # =========================================================================

    def get_nested(self, path: str, default: Any = None, separator: str = '.') -> Any:
        """嵌套路径安全访问

        通过点分隔路径安全访问嵌套属性，任意层级不存在都返回默认值。

        Args:
            path: 点分隔的路径，如 'user.address.city'
            default: 默认值
            separator: 路径分隔符，默认 '.'

        Returns:
            嵌套属性值或默认值

        Example:
            city = body.get_nested('user.address.city', 'Unknown')
            # 等价于：
            # city = body.get('user', {}).get('address', {}).get('city', 'Unknown')
            # 但更简洁且安全
        """
        keys = path.split(separator)
        current = self._data

        for key in keys:
            if isinstance(current, dict):
                if key not in current:
                    return default
                current = current[key]
            elif isinstance(current, DynamicBody):
                if key not in current._data:
                    return default
                current = current._data[key]
            else:
                return default

        if isinstance(current, dict):
            return DynamicBody(current)
        return current

    def get_list(self, name: str, default: List = None) -> List:
        """安全获取列表属性

        Args:
            name: 属性名
            default: 默认值，默认为空列表

        Returns:
            列表值或默认值

        Example:
            tags = body.get_list('tags')  # 返回 [] 如果 tags 不存在
            for tag in tags:
                process(tag)
        """
        if default is None:
            default = []
        value = self._data.get(name)
        if value is None:
            return default
        if isinstance(value, list):
            return value
        return default

    def get_str(self, name: str, default: str = '') -> str:
        """安全获取字符串属性

        Args:
            name: 属性名
            default: 默认值，默认为空字符串

        Returns:
            字符串值或默认值

        Example:
            name = body.get_str('name')  # 返回 '' 如果 name 不存在
        """
        value = self._data.get(name)
        if value is None:
            return default
        return str(value)

    def get_int(self, name: str, default: int = 0) -> int:
        """安全获取整数属性

        Args:
            name: 属性名
            default: 默认值，默认为 0

        Returns:
            整数值或默认值

        Example:
            age = body.get_int('age')  # 返回 0 如果 age 不存在或无法转换
        """
        value = self._data.get(name)
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, name: str, default: float = 0.0) -> float:
        """安全获取浮点数属性

        Args:
            name: 属性名
            default: 默认值，默认为 0.0

        Returns:
            浮点数值或默认值

        Example:
            price = body.get_float('price')  # 返回 0.0 如果 price 不存在
        """
        value = self._data.get(name)
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, name: str, default: bool = False) -> bool:
        """安全获取布尔属性

        支持多种布尔值表示：True/False, 'true'/'false', 1/0, 'yes'/'no'

        Args:
            name: 属性名
            default: 默认值，默认为 False

        Returns:
            布尔值或默认值

        Example:
            active = body.get_bool('active')  # 返回 False 如果 active 不存在
        """
        value = self._data.get(name)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    # =========================================================================
    # 链式安全访问器
    # =========================================================================

    @property
    def safe(self) -> 'SafeAccessor':
        """返回安全访问器，支持链式访问而不抛异常

        Returns:
            SafeAccessor 实例

        Example:
            # 传统方式可能抛异常
            # city = body.user.address.city  # AttributeError if any level is missing

            # 使用安全访问器
            city = body.safe.user.address.city.value_or('Unknown')

            # 或者检查是否存在
            if body.safe.user.address.city.exists:
                print(body.safe.user.address.city.value)
        """
        return SafeAccessor(self._data)

    def copy(self) -> 'DynamicBody':
        """返回浅拷贝

        Returns:
            新的 DynamicBody 实例
        """
        return DynamicBody(self._data.copy())


class SafeAccessor:
    """安全访问器

    支持链式访问而不抛出 AttributeError，任意层级不存在都安全处理。

    Example:
        body = DynamicBody({'user': {'name': 'John'}})

        # 安全访问存在的属性
        name = body.safe.user.name.value  # 'John'

        # 安全访问不存在的属性
        city = body.safe.user.address.city.value_or('Unknown')  # 'Unknown'

        # 检查是否存在
        if body.safe.user.email.exists:
            send_email(body.safe.user.email.value)
    """

    __slots__ = ('_data', '_exists')

    def __init__(self, data: Any, exists: bool = True):
        """初始化安全访问器

        Args:
            data: 当前数据
            exists: 数据是否存在
        """
        object.__setattr__(self, '_data', data)
        object.__setattr__(self, '_exists', exists)

    def __getattr__(self, name: str) -> 'SafeAccessor':
        """安全获取属性，不抛异常

        Args:
            name: 属性名

        Returns:
            新的 SafeAccessor 实例
        """
        data = object.__getattribute__(self, '_data')
        exists = object.__getattribute__(self, '_exists')

        if not exists:
            return SafeAccessor(None, False)

        if isinstance(data, dict):
            if name in data:
                return SafeAccessor(data[name], True)
            return SafeAccessor(None, False)

        if isinstance(data, DynamicBody):
            if name in data._data:
                return SafeAccessor(data._data[name], True)
            return SafeAccessor(None, False)

        return SafeAccessor(None, False)

    @property
    def value(self) -> Any:
        """获取当前值

        Returns:
            当前值，如果不存在返回 None
        """
        if not self._exists:
            return None
        if isinstance(self._data, dict):
            return DynamicBody(self._data)
        return self._data

    def value_or(self, default: Any) -> Any:
        """获取值或默认值

        Args:
            default: 默认值

        Returns:
            当前值或默认值
        """
        if not self._exists or self._data is None:
            return default
        if isinstance(self._data, dict):
            return DynamicBody(self._data)
        return self._data

    @property
    def exists(self) -> bool:
        """检查值是否存在

        Returns:
            是否存在
        """
        return self._exists

    @property
    def is_null(self) -> bool:
        """检查值是否为 None

        Returns:
            是否为 None
        """
        return not self._exists or self._data is None

    @property
    def is_not_null(self) -> bool:
        """检查值是否不为 None

        Returns:
            是否不为 None
        """
        return self._exists and self._data is not None

    def __bool__(self) -> bool:
        """布尔值判断"""
        return self._exists and bool(self._data)

    def __repr__(self) -> str:
        if self._exists:
            return f"SafeAccessor({self._data!r})"
        return "SafeAccessor(<missing>)"
