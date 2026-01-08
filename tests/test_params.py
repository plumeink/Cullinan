# -*- coding: utf-8 -*-
"""Cullinan Params Module Tests

测试参数标记类。

Author: Plumeink
"""

import unittest

from cullinan.params import (
    Param,
    Path,
    Query,
    Body,
    Header,
    File,
    UNSET,
)


class TestUNSET(unittest.TestCase):
    """测试 UNSET 哨兵"""

    def test_singleton(self):
        """UNSET 应该是单例"""
        from cullinan.params.base import _UNSET
        a = _UNSET()
        b = _UNSET()
        self.assertIs(a, b)
        self.assertIs(a, UNSET)

    def test_bool_is_false(self):
        """UNSET 的布尔值应为 False"""
        self.assertFalse(UNSET)
        self.assertFalse(bool(UNSET))

    def test_repr(self):
        """UNSET 的字符串表示"""
        self.assertEqual(repr(UNSET), '<UNSET>')


class TestParam(unittest.TestCase):
    """测试 Param 基类"""

    def test_default_values(self):
        """默认值测试"""
        p = Param()
        self.assertEqual(p.type_, str)
        self.assertTrue(p.required)
        self.assertIs(p.default, UNSET)
        self.assertIsNone(p.name)

    def test_with_type(self):
        """指定类型"""
        p = Param(int)
        self.assertEqual(p.type_, int)

    def test_with_default_sets_required_false(self):
        """有默认值时 required 自动为 False"""
        p = Param(str, default='test')
        self.assertFalse(p.required)
        self.assertEqual(p.default, 'test')

    def test_explicit_required_with_default(self):
        """显式 required=True 但有默认值时，required 仍为 False"""
        p = Param(str, required=True, default='test')
        self.assertFalse(p.required)

    def test_validators(self):
        """验证器构建"""
        p = Param(int, ge=0, le=100, min_length=1)
        validators = p.get_validators()
        self.assertEqual(len(validators), 3)
        self.assertIn(('ge', 0), validators)
        self.assertIn(('le', 100), validators)
        self.assertIn(('min_length', 1), validators)

    def test_has_default(self):
        """has_default 方法"""
        p1 = Param()
        p2 = Param(default='test')
        self.assertFalse(p1.has_default())
        self.assertTrue(p2.has_default())

    def test_get_default(self):
        """get_default 方法"""
        p1 = Param()
        p2 = Param(default='test')
        self.assertIsNone(p1.get_default())
        self.assertEqual(p2.get_default(), 'test')

    def test_repr(self):
        """字符串表示"""
        p = Param(int, name='age', default=0)
        repr_str = repr(p)
        self.assertIn('Param', repr_str)
        self.assertIn('int', repr_str)
        self.assertIn('age', repr_str)


class TestPath(unittest.TestCase):
    """测试 Path 参数类型"""

    def test_source(self):
        """来源标识"""
        p = Path(int)
        self.assertEqual(p.source, 'path')

    def test_always_required(self):
        """Path 参数始终必填"""
        p = Path(int)
        self.assertTrue(p.required)

    def test_no_default(self):
        """Path 参数不支持默认值"""
        p = Path(int)
        self.assertIs(p.default, UNSET)

    def test_with_validators(self):
        """带验证器"""
        p = Path(int, ge=1)
        validators = p.get_validators()
        self.assertIn(('ge', 1), validators)


class TestQuery(unittest.TestCase):
    """测试 Query 参数类型"""

    def test_source(self):
        """来源标识"""
        p = Query(str)
        self.assertEqual(p.source, 'query')

    def test_with_default(self):
        """带默认值"""
        p = Query(int, default=1)
        self.assertFalse(p.required)
        self.assertEqual(p.default, 1)

    def test_optional(self):
        """可选参数"""
        p = Query(str, required=False)
        self.assertFalse(p.required)


class TestBody(unittest.TestCase):
    """测试 Body 参数类型"""

    def test_source(self):
        """来源标识"""
        p = Body(str)
        self.assertEqual(p.source, 'body')

    def test_with_validators(self):
        """带验证器"""
        p = Body(int, ge=0, le=100)
        validators = p.get_validators()
        self.assertIn(('ge', 0), validators)
        self.assertIn(('le', 100), validators)


class TestHeader(unittest.TestCase):
    """测试 Header 参数类型"""

    def test_source(self):
        """来源标识"""
        p = Header(str)
        self.assertEqual(p.source, 'header')

    def test_with_alias(self):
        """带别名"""
        p = Header(str, alias='Authorization')
        self.assertEqual(p.alias, 'Authorization')

    def test_optional_with_default(self):
        """可选带默认值"""
        p = Header(str, default='Bearer token')
        self.assertFalse(p.required)
        self.assertEqual(p.default, 'Bearer token')


class TestFile(unittest.TestCase):
    """测试 File 参数类型"""

    def test_source(self):
        """来源标识"""
        p = File()
        self.assertEqual(p.source, 'file')

    def test_type_is_bytes(self):
        """文件类型为 bytes"""
        p = File()
        self.assertEqual(p.type_, bytes)

    def test_max_size(self):
        """最大文件大小"""
        p = File(max_size=1024)
        self.assertEqual(p.max_size, 1024)

    def test_allowed_types(self):
        """允许的 MIME 类型"""
        p = File(allowed_types=['image/png', 'image/jpeg'])
        self.assertEqual(p.allowed_types, ['image/png', 'image/jpeg'])

    def test_repr(self):
        """字符串表示"""
        p = File(name='avatar', max_size=1024)
        repr_str = repr(p)
        self.assertIn('File', repr_str)
        self.assertIn('avatar', repr_str)


if __name__ == '__main__':
    unittest.main()

