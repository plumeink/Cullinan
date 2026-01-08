# -*- coding: utf-8 -*-
"""Cullinan Codec Module Tests

测试 Codec 模块的编解码功能。

Author: Plumeink
"""

import unittest
import json

from cullinan.codec import (
    BodyCodec,
    ResponseCodec,
    JsonBodyCodec,
    JsonResponseCodec,
    FormBodyCodec,
    DecodeError,
    EncodeError,
    CodecRegistry,
    get_codec_registry,
    reset_codec_registry,
)


class TestJsonBodyCodec(unittest.TestCase):
    """测试 JSON 请求体解码"""

    def setUp(self):
        self.codec = JsonBodyCodec()

    def test_decode_empty_body(self):
        """空请求体应返回空字典"""
        result = self.codec.decode(b'')
        self.assertEqual(result, {})

    def test_decode_valid_json(self):
        """正常 JSON 解码"""
        body = b'{"name": "test", "age": 18}'
        result = self.codec.decode(body)
        self.assertEqual(result, {"name": "test", "age": 18})

    def test_decode_json_array(self):
        """JSON 数组应被包装"""
        body = b'[1, 2, 3]'
        result = self.codec.decode(body)
        self.assertEqual(result, {"_value": [1, 2, 3]})

    def test_decode_invalid_json(self):
        """无效 JSON 应抛出 DecodeError"""
        body = b'invalid json'
        with self.assertRaises(DecodeError):
            self.codec.decode(body)

    def test_decode_with_charset(self):
        """带字符编码的解码"""
        body = '{"name": "中文"}'.encode('utf-8')
        result = self.codec.decode(body, charset='utf-8')
        self.assertEqual(result, {"name": "中文"})

    def test_supports_content_type(self):
        """Content-Type 支持检测"""
        self.assertTrue(JsonBodyCodec.supports('application/json'))
        self.assertTrue(JsonBodyCodec.supports('application/json; charset=utf-8'))
        self.assertTrue(JsonBodyCodec.supports('text/json'))
        self.assertFalse(JsonBodyCodec.supports('text/plain'))


class TestJsonResponseCodec(unittest.TestCase):
    """测试 JSON 响应编码"""

    def setUp(self):
        self.codec = JsonResponseCodec()

    def test_encode_dict(self):
        """编码字典"""
        data = {"name": "test", "age": 18}
        result = self.codec.encode(data)
        self.assertEqual(json.loads(result.decode('utf-8')), data)

    def test_encode_with_chinese(self):
        """编码中文"""
        data = {"name": "中文"}
        result = self.codec.encode(data)
        self.assertIn("中文", result.decode('utf-8'))

    def test_get_content_type(self):
        """获取 Content-Type"""
        ct = self.codec.get_content_type()
        self.assertIn('application/json', ct)
        self.assertIn('utf-8', ct)


class TestFormBodyCodec(unittest.TestCase):
    """测试 Form 请求体解码"""

    def setUp(self):
        self.codec = FormBodyCodec()

    def test_decode_empty_body(self):
        """空请求体应返回空字典"""
        result = self.codec.decode(b'')
        self.assertEqual(result, {})

    def test_decode_simple_form(self):
        """简单表单解码"""
        body = b'name=test&age=18'
        result = self.codec.decode(body)
        self.assertEqual(result, {"name": "test", "age": "18"})

    def test_decode_multi_value(self):
        """多值字段"""
        body = b'tags=a&tags=b&tags=c'
        result = self.codec.decode(body)
        self.assertEqual(result, {"tags": ["a", "b", "c"]})

    def test_supports_content_type(self):
        """Content-Type 支持检测"""
        self.assertTrue(FormBodyCodec.supports('application/x-www-form-urlencoded'))
        self.assertFalse(FormBodyCodec.supports('application/json'))


class TestCodecRegistry(unittest.TestCase):
    """测试 Codec 注册表"""

    def setUp(self):
        reset_codec_registry()
        self.registry = get_codec_registry()

    def tearDown(self):
        reset_codec_registry()

    def test_default_codecs_registered(self):
        """默认 Codec 应已注册"""
        body_codecs = self.registry.list_body_codecs()
        self.assertTrue(any(c == JsonBodyCodec for c in body_codecs))
        self.assertTrue(any(c == FormBodyCodec for c in body_codecs))

    def test_get_body_codec_json(self):
        """获取 JSON Codec"""
        codec = self.registry.get_body_codec('application/json')
        self.assertIsInstance(codec, JsonBodyCodec)

    def test_get_body_codec_form(self):
        """获取 Form Codec"""
        codec = self.registry.get_body_codec('application/x-www-form-urlencoded')
        self.assertIsInstance(codec, FormBodyCodec)

    def test_decode_body_json(self):
        """通过注册表解码 JSON"""
        body = b'{"test": true}'
        result = self.registry.decode_body(body, 'application/json')
        self.assertEqual(result, {"test": True})

    def test_decode_body_form(self):
        """通过注册表解码 Form"""
        body = b'key=value'
        result = self.registry.decode_body(body, 'application/x-www-form-urlencoded')
        self.assertEqual(result, {"key": "value"})

    def test_encode_response(self):
        """通过注册表编码响应"""
        data = {"status": "ok"}
        encoded, content_type = self.registry.encode_response(data)
        self.assertIn('application/json', content_type)
        self.assertEqual(json.loads(encoded.decode('utf-8')), data)


if __name__ == '__main__':
    unittest.main()

