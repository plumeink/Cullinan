# -*- coding: utf-8 -*-
"""Cullinan ModelResolver Tests

测试 dataclass 模型解析。

Author: Plumeink
"""

import unittest
from dataclasses import dataclass
from typing import Optional, List

from cullinan.params import (
    ModelResolver,
    ModelError,
)


@dataclass
class SimpleUser:
    name: str
    age: int


@dataclass
class UserWithDefaults:
    name: str
    age: int = 0
    email: str = ""


@dataclass
class UserWithOptional:
    name: str
    nickname: Optional[str] = None


@dataclass
class Address:
    city: str
    street: str


@dataclass
class UserWithAddress:
    name: str
    address: Address


class TestModelResolverBasic(unittest.TestCase):
    """测试基本模型解析"""

    def test_is_dataclass(self):
        """检测 dataclass"""
        self.assertTrue(ModelResolver.is_dataclass(SimpleUser))
        self.assertFalse(ModelResolver.is_dataclass(str))
        self.assertFalse(ModelResolver.is_dataclass(dict))

    def test_resolve_simple(self):
        """解析简单模型"""
        data = {'name': 'test', 'age': 25}
        user = ModelResolver.resolve(SimpleUser, data)
        self.assertEqual(user.name, 'test')
        self.assertEqual(user.age, 25)

    def test_resolve_with_type_conversion(self):
        """解析时类型转换"""
        data = {'name': 'test', 'age': '30'}  # age 是字符串
        user = ModelResolver.resolve(SimpleUser, data)
        self.assertEqual(user.age, 30)

    def test_resolve_missing_required(self):
        """缺少必填字段"""
        data = {'name': 'test'}  # 缺少 age
        with self.assertRaises(ModelError) as ctx:
            ModelResolver.resolve(SimpleUser, data)
        self.assertTrue(len(ctx.exception.field_errors) > 0)

    def test_resolve_with_defaults(self):
        """使用默认值"""
        data = {'name': 'test'}
        user = ModelResolver.resolve(UserWithDefaults, data)
        self.assertEqual(user.name, 'test')
        self.assertEqual(user.age, 0)
        self.assertEqual(user.email, '')

    def test_resolve_override_defaults(self):
        """覆盖默认值"""
        data = {'name': 'test', 'age': 18, 'email': 'test@example.com'}
        user = ModelResolver.resolve(UserWithDefaults, data)
        self.assertEqual(user.age, 18)
        self.assertEqual(user.email, 'test@example.com')


class TestModelResolverOptional(unittest.TestCase):
    """测试 Optional 类型"""

    def test_optional_with_value(self):
        """Optional 有值"""
        data = {'name': 'test', 'nickname': 'nick'}
        user = ModelResolver.resolve(UserWithOptional, data)
        self.assertEqual(user.nickname, 'nick')

    def test_optional_without_value(self):
        """Optional 无值"""
        data = {'name': 'test'}
        user = ModelResolver.resolve(UserWithOptional, data)
        self.assertIsNone(user.nickname)

    def test_optional_with_none(self):
        """Optional 显式 None"""
        data = {'name': 'test', 'nickname': None}
        user = ModelResolver.resolve(UserWithOptional, data)
        self.assertIsNone(user.nickname)


class TestModelResolverNested(unittest.TestCase):
    """测试嵌套 dataclass"""

    def test_nested_resolve(self):
        """解析嵌套模型"""
        data = {
            'name': 'test',
            'address': {
                'city': 'Beijing',
                'street': 'Main Street'
            }
        }
        user = ModelResolver.resolve(UserWithAddress, data)
        self.assertEqual(user.name, 'test')
        self.assertEqual(user.address.city, 'Beijing')
        self.assertEqual(user.address.street, 'Main Street')

    def test_nested_missing_required(self):
        """嵌套模型缺少字段"""
        data = {
            'name': 'test',
            'address': {'city': 'Beijing'}  # 缺少 street
        }
        with self.assertRaises(ModelError):
            ModelResolver.resolve(UserWithAddress, data)


class TestModelResolverToDict(unittest.TestCase):
    """测试 to_dict"""

    def test_simple_to_dict(self):
        """简单模型转字典"""
        user = SimpleUser(name='test', age=25)
        data = ModelResolver.to_dict(user)
        self.assertEqual(data, {'name': 'test', 'age': 25})

    def test_nested_to_dict(self):
        """嵌套模型转字典"""
        address = Address(city='Beijing', street='Main Street')
        user = UserWithAddress(name='test', address=address)
        data = ModelResolver.to_dict(user)
        self.assertEqual(data['name'], 'test')
        self.assertEqual(data['address']['city'], 'Beijing')


class TestModelResolverErrors(unittest.TestCase):
    """测试错误处理"""

    def test_not_dataclass(self):
        """非 dataclass 类型"""
        with self.assertRaises(ModelError):
            ModelResolver.resolve(dict, {})

    def test_error_to_dict(self):
        """错误转字典"""
        try:
            ModelResolver.resolve(SimpleUser, {'name': 'test'})
        except ModelError as e:
            d = e.to_dict()
            self.assertIn('message', d)
            self.assertIn('field_errors', d)


if __name__ == '__main__':
    unittest.main()

