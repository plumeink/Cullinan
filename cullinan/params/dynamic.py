# -*- coding: utf-8 -*-
"""Cullinan DynamicBody

动态请求体类，支持属性访问方式。

Author: Plumeink
"""

from typing import Any, Dict, Iterator, KeysView, ValuesView, ItemsView


class DynamicBody:
    """动态请求体类

    提供类似 JavaScript 对象的属性访问方式，避免频繁使用 .get()。

    Features:
    - 属性访问: body.name
    - 安全访问: body.get('name', default)
    - 字典兼容: body['name'], 'name' in body
    - 迭代支持: for key in body
    - 可变性: body.new_field = value
    - 嵌套访问: body.user.name (嵌套字典自动转换)

    Example:
        body = DynamicBody({'name': 'test', 'age': 18, 'user': {'id': 1}})

        # 属性访问
        print(body.name)  # 'test'
        print(body.age)   # 18

        # 嵌套访问
        print(body.user.id)  # 1

        # 安全访问
        print(body.get('email', 'default@example.com'))

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

    # 字典兼容方法

    def get(self, name: str, default: Any = None) -> Any:
        """安全获取属性值

        Args:
            name: 属性名
            default: 默认值

        Returns:
            属性值或默认值
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

    def copy(self) -> 'DynamicBody':
        """返回浅拷贝

        Returns:
            新的 DynamicBody 实例
        """
        return DynamicBody(self._data.copy())

