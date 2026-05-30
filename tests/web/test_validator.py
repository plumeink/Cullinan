# -*- coding: utf-8 -*-
"""Cullinan ParamValidator Tests

测试参数校验器。

Author: Plumeink
"""

import unittest

from cullinan.params import (
    ParamValidator,
    ValidationError,
    Param,
    Query,
)


class TestValidationError(unittest.TestCase):
    """测试 ValidationError"""

    def test_basic_error(self):
        """基本错误"""
        err = ValidationError("test error", param_name="age", value=5)
        self.assertEqual(err.message, "test error")
        self.assertEqual(err.param_name, "age")
        self.assertEqual(err.value, 5)

    def test_to_dict(self):
        """转换为字典"""
        err = ValidationError("test", param_name="x", value=1, constraint="ge:0")
        d = err.to_dict()
        self.assertEqual(d['message'], "test")
        self.assertEqual(d['param'], "x")
        self.assertEqual(d['constraint'], "ge:0")


class TestParamValidatorRequired(unittest.TestCase):
    """测试必填校验"""

    def test_required_with_value(self):
        """必填有值"""
        ParamValidator.validate_required("test", True, "name")  # 不抛出

    def test_required_without_value(self):
        """必填无值"""
        with self.assertRaises(ValidationError) as ctx:
            ParamValidator.validate_required(None, True, "name")
        self.assertIn("required", ctx.exception.message)

    def test_optional_without_value(self):
        """可选无值"""
        ParamValidator.validate_required(None, False, "name")  # 不抛出


class TestParamValidatorNumeric(unittest.TestCase):
    """测试数值校验"""

    def test_ge_pass(self):
        """ge 通过"""
        ParamValidator.validate_ge(10, 5, "age")
        ParamValidator.validate_ge(5, 5, "age")

    def test_ge_fail(self):
        """ge 失败"""
        with self.assertRaises(ValidationError):
            ParamValidator.validate_ge(3, 5, "age")

    def test_ge_none(self):
        """ge None 跳过"""
        ParamValidator.validate_ge(None, 5, "age")

    def test_le_pass(self):
        """le 通过"""
        ParamValidator.validate_le(5, 10, "age")
        ParamValidator.validate_le(10, 10, "age")

    def test_le_fail(self):
        """le 失败"""
        with self.assertRaises(ValidationError):
            ParamValidator.validate_le(15, 10, "age")

    def test_gt_pass(self):
        """gt 通过"""
        ParamValidator.validate_gt(10, 5, "age")

    def test_gt_fail(self):
        """gt 失败 (等于也不行)"""
        with self.assertRaises(ValidationError):
            ParamValidator.validate_gt(5, 5, "age")

    def test_lt_pass(self):
        """lt 通过"""
        ParamValidator.validate_lt(5, 10, "age")

    def test_lt_fail(self):
        """lt 失败 (等于也不行)"""
        with self.assertRaises(ValidationError):
            ParamValidator.validate_lt(10, 10, "age")


class TestParamValidatorLength(unittest.TestCase):
    """测试长度校验"""

    def test_min_length_pass(self):
        """min_length 通过"""
        ParamValidator.validate_min_length("hello", 3, "name")
        ParamValidator.validate_min_length([1, 2, 3], 2, "items")

    def test_min_length_fail(self):
        """min_length 失败"""
        with self.assertRaises(ValidationError):
            ParamValidator.validate_min_length("hi", 3, "name")

    def test_max_length_pass(self):
        """max_length 通过"""
        ParamValidator.validate_max_length("hi", 10, "name")

    def test_max_length_fail(self):
        """max_length 失败"""
        with self.assertRaises(ValidationError):
            ParamValidator.validate_max_length("hello world", 5, "name")


class TestParamValidatorRegex(unittest.TestCase):
    """测试正则校验"""

    def test_regex_pass(self):
        """regex 通过"""
        ParamValidator.validate_regex("test@example.com", r".+@.+\..+", "email")

    def test_regex_fail(self):
        """regex 失败"""
        with self.assertRaises(ValidationError):
            ParamValidator.validate_regex("invalid-email", r".+@.+\..+", "email")

    def test_regex_none(self):
        """regex None 跳过"""
        ParamValidator.validate_regex(None, r".+", "field")


class TestParamValidatorBatch(unittest.TestCase):
    """测试批量校验"""

    def test_validate_multiple(self):
        """多个规则"""
        validators = [('ge', 0), ('le', 100)]
        ParamValidator.validate(50, validators, "score")

    def test_validate_fail_first(self):
        """第一个规则失败"""
        validators = [('ge', 10), ('le', 100)]
        with self.assertRaises(ValidationError):
            ParamValidator.validate(5, validators, "score")

    def test_validate_unknown_rule(self):
        """未知规则"""
        with self.assertRaises(ValueError):
            ParamValidator.validate(10, [('unknown', 5)], "x")


class TestParamValidatorWithParam(unittest.TestCase):
    """测试与 Param 类集成"""

    def test_validate_param_required(self):
        """校验 Param 必填"""
        param = Query(int, name="age")
        with self.assertRaises(ValidationError):
            ParamValidator.validate_param(param, None)

    def test_validate_param_with_constraints(self):
        """校验 Param 约束"""
        param = Query(int, name="age", ge=0, le=150)
        ParamValidator.validate_param(param, 25)

        with self.assertRaises(ValidationError):
            ParamValidator.validate_param(param, -5)

    def test_validate_param_optional(self):
        """校验可选 Param"""
        param = Query(int, name="page", default=1)
        ParamValidator.validate_param(param, None)  # 不抛出，因为有默认值 = 不必填


if __name__ == '__main__':
    unittest.main()

