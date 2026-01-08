# -*- coding: utf-8 -*-
"""Cullinan TypeConverter and Auto Tests

测试类型转换和自动类型推断。

Author: Plumeink
"""

import unittest

from cullinan.params import (
    TypeConverter,
    ConversionError,
    Auto,
    AutoType,
    DynamicBody,
)


class TestTypeConverter(unittest.TestCase):
    """测试类型转换器"""

    def test_convert_to_str(self):
        """转换为字符串"""
        self.assertEqual(TypeConverter.convert(123, str), "123")
        self.assertEqual(TypeConverter.convert(True, str), "True")
        self.assertEqual(TypeConverter.convert(b"hello", str), "hello")

    def test_convert_to_int(self):
        """转换为整数"""
        self.assertEqual(TypeConverter.convert("123", int), 123)
        self.assertEqual(TypeConverter.convert("12.5", int), 12)
        self.assertEqual(TypeConverter.convert(12.9, int), 12)
        self.assertEqual(TypeConverter.convert(True, int), 1)
        self.assertEqual(TypeConverter.convert(False, int), 0)

    def test_convert_to_int_error(self):
        """整数转换错误"""
        with self.assertRaises(ConversionError):
            TypeConverter.convert("", int)
        with self.assertRaises(ConversionError):
            TypeConverter.convert("abc", int)

    def test_convert_to_float(self):
        """转换为浮点数"""
        self.assertEqual(TypeConverter.convert("12.5", float), 12.5)
        self.assertEqual(TypeConverter.convert("123", float), 123.0)
        self.assertEqual(TypeConverter.convert(123, float), 123.0)

    def test_convert_to_float_error(self):
        """浮点数转换错误"""
        with self.assertRaises(ConversionError):
            TypeConverter.convert("", float)

    def test_convert_to_bool(self):
        """转换为布尔值"""
        # 真值
        self.assertTrue(TypeConverter.convert("true", bool))
        self.assertTrue(TypeConverter.convert("True", bool))
        self.assertTrue(TypeConverter.convert("1", bool))
        self.assertTrue(TypeConverter.convert("yes", bool))
        self.assertTrue(TypeConverter.convert("on", bool))

        # 假值
        self.assertFalse(TypeConverter.convert("false", bool))
        self.assertFalse(TypeConverter.convert("False", bool))
        self.assertFalse(TypeConverter.convert("0", bool))
        self.assertFalse(TypeConverter.convert("no", bool))
        self.assertFalse(TypeConverter.convert("off", bool))
        self.assertFalse(TypeConverter.convert("", bool))

    def test_convert_to_bool_error(self):
        """布尔值转换错误"""
        with self.assertRaises(ConversionError):
            TypeConverter.convert("maybe", bool)

    def test_convert_to_list(self):
        """转换为列表"""
        self.assertEqual(TypeConverter.convert("a,b,c", list), ["a", "b", "c"])
        self.assertEqual(TypeConverter.convert("[1,2,3]", list), [1, 2, 3])
        self.assertEqual(TypeConverter.convert((1, 2), list), [1, 2])
        self.assertEqual(TypeConverter.convert("single", list), ["single"])
        self.assertEqual(TypeConverter.convert("", list), [])

    def test_convert_to_dict(self):
        """转换为字典"""
        self.assertEqual(TypeConverter.convert('{"a": 1}', dict), {"a": 1})
        self.assertEqual(TypeConverter.convert({"a": 1}, dict), {"a": 1})

    def test_convert_to_dict_error(self):
        """字典转换错误"""
        with self.assertRaises(ConversionError):
            TypeConverter.convert("not json", dict)

    def test_convert_to_bytes(self):
        """转换为字节"""
        self.assertEqual(TypeConverter.convert("hello", bytes), b"hello")
        self.assertEqual(TypeConverter.convert(b"hello", bytes), b"hello")

    def test_convert_none(self):
        """None 值处理"""
        self.assertIsNone(TypeConverter.convert(None, str))
        self.assertIsNone(TypeConverter.convert(None, int))

    def test_convert_same_type(self):
        """相同类型直接返回"""
        self.assertEqual(TypeConverter.convert("test", str), "test")
        self.assertEqual(TypeConverter.convert(123, int), 123)

    def test_can_convert(self):
        """can_convert 方法"""
        self.assertTrue(TypeConverter.can_convert("123", int))
        self.assertFalse(TypeConverter.can_convert("abc", int))


class TestAuto(unittest.TestCase):
    """测试自动类型推断"""

    def test_infer_none(self):
        """推断 None"""
        self.assertIsNone(Auto.infer(None))
        self.assertIsNone(Auto.infer("null"))
        self.assertIsNone(Auto.infer("None"))

    def test_infer_bool(self):
        """推断布尔值"""
        self.assertTrue(Auto.infer("true"))
        self.assertTrue(Auto.infer("True"))
        self.assertTrue(Auto.infer("yes"))
        self.assertFalse(Auto.infer("false"))
        self.assertFalse(Auto.infer("no"))

    def test_infer_int(self):
        """推断整数"""
        self.assertEqual(Auto.infer("123"), 123)
        self.assertEqual(Auto.infer("-456"), -456)
        self.assertEqual(Auto.infer("0"), 0)

    def test_infer_float(self):
        """推断浮点数"""
        self.assertEqual(Auto.infer("12.5"), 12.5)
        self.assertEqual(Auto.infer("-3.14"), -3.14)
        self.assertEqual(Auto.infer("1e10"), 1e10)

    def test_infer_dict(self):
        """推断字典"""
        result = Auto.infer('{"name": "test"}')
        self.assertEqual(result, {"name": "test"})

    def test_infer_list(self):
        """推断列表"""
        result = Auto.infer('[1, 2, 3]')
        self.assertEqual(result, [1, 2, 3])

    def test_infer_string(self):
        """保持字符串"""
        self.assertEqual(Auto.infer("hello"), "hello")
        self.assertEqual(Auto.infer(""), "")

    def test_infer_non_string(self):
        """非字符串直接返回"""
        self.assertEqual(Auto.infer(123), 123)
        self.assertEqual(Auto.infer([1, 2]), [1, 2])

    def test_infer_type(self):
        """推断类型"""
        self.assertEqual(Auto.infer_type("123"), int)
        self.assertEqual(Auto.infer_type("12.5"), float)
        self.assertEqual(Auto.infer_type("true"), bool)
        self.assertEqual(Auto.infer_type("hello"), str)
        self.assertEqual(Auto.infer_type('{"a":1}'), dict)
        self.assertEqual(Auto.infer_type('[1,2]'), list)


class TestAutoType(unittest.TestCase):
    """测试 AutoType 标记"""

    def test_is_class(self):
        """AutoType 是一个类"""
        self.assertTrue(isinstance(AutoType, type))


class TestDynamicBody(unittest.TestCase):
    """测试动态请求体"""

    def setUp(self):
        self.body = DynamicBody({
            'name': 'test',
            'age': 18,
            'user': {'id': 1, 'role': 'admin'}
        })

    def test_attribute_access(self):
        """属性访问"""
        self.assertEqual(self.body.name, 'test')
        self.assertEqual(self.body.age, 18)

    def test_nested_access(self):
        """嵌套访问"""
        self.assertEqual(self.body.user.id, 1)
        self.assertEqual(self.body.user.role, 'admin')

    def test_attribute_not_found(self):
        """属性不存在"""
        with self.assertRaises(AttributeError):
            _ = self.body.email

    def test_get_method(self):
        """get 方法"""
        self.assertEqual(self.body.get('name'), 'test')
        self.assertEqual(self.body.get('email', 'default'), 'default')

    def test_dict_access(self):
        """字典式访问"""
        self.assertEqual(self.body['name'], 'test')

    def test_contains(self):
        """包含检查"""
        self.assertTrue('name' in self.body)
        self.assertFalse('email' in self.body)

    def test_set_attribute(self):
        """设置属性"""
        self.body.email = 'test@example.com'
        self.assertEqual(self.body.email, 'test@example.com')

    def test_delete_attribute(self):
        """删除属性"""
        self.body.temp = 'value'
        del self.body.temp
        self.assertFalse('temp' in self.body)

    def test_iteration(self):
        """迭代"""
        keys = list(self.body)
        self.assertIn('name', keys)
        self.assertIn('age', keys)

    def test_len(self):
        """长度"""
        self.assertEqual(len(self.body), 3)

    def test_bool(self):
        """布尔值"""
        self.assertTrue(bool(self.body))
        self.assertFalse(bool(DynamicBody({})))

    def test_to_dict(self):
        """转换为字典"""
        data = self.body.to_dict()
        self.assertEqual(data['name'], 'test')

    def test_equality(self):
        """相等性"""
        other = DynamicBody({'name': 'test', 'age': 18, 'user': {'id': 1, 'role': 'admin'}})
        self.assertEqual(self.body, other)
        self.assertEqual(self.body, {'name': 'test', 'age': 18, 'user': {'id': 1, 'role': 'admin'}})

    def test_update(self):
        """更新数据"""
        self.body.update({'email': 'test@example.com'})
        self.assertEqual(self.body.email, 'test@example.com')

    def test_copy(self):
        """浅拷贝"""
        copy = self.body.copy()
        self.assertEqual(copy.name, 'test')
        copy.name = 'modified'
        self.assertEqual(self.body.name, 'test')  # 原始不变


if __name__ == '__main__':
    unittest.main()

