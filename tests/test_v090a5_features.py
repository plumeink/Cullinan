# -*- coding: utf-8 -*-
"""v0.90a5 新功能测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试所有新模块导入"""
    print("1. 测试导入...")
    
    from cullinan.params import (
        FileInfo, FileList,
        field_validator, FieldValidationError, validated_dataclass,
        Response, ResponseModel, ResponseSerializer, serialize_response,
    )
    
    print("   所有模块导入成功")
    return True


def test_file_info():
    """测试 FileInfo"""
    print("2. 测试 FileInfo...")
    
    from cullinan.params import FileInfo, FileList
    
    # 创建 FileInfo
    file = FileInfo(
        filename='test.png',
        body=b'fake image data',
        content_type='image/png',
    )
    
    assert file.filename == 'test.png'
    assert file.size == 15
    assert file.content_type == 'image/png'
    assert file.extension == 'png'
    assert file.is_image() == True
    assert file.is_pdf() == False
    assert file.match_type('image/*') == True
    assert file.match_type('application/pdf') == False
    
    # FileList
    files = FileList([
        FileInfo('a.png', b'data1', 'image/png'),
        FileInfo('b.jpg', b'data2', 'image/jpeg'),
        FileInfo('c.pdf', b'data3', 'application/pdf'),
    ])
    
    assert len(files) == 3
    assert files.count == 3
    assert 'a.png' in files.filenames
    
    images = files.filter_by_type('image/*')
    assert len(images) == 2
    
    print("   FileInfo 测试通过")
    return True


def test_field_validator():
    """测试 field_validator"""
    print("3. 测试 field_validator...")
    
    from dataclasses import dataclass
    from cullinan.params import field_validator, validated_dataclass, FieldValidationError
    
    @validated_dataclass
    class User:
        name: str
        email: str
        age: int = 0
        
        @field_validator('email')
        @classmethod
        def validate_email(cls, v):
            if '@' not in str(v):
                raise ValueError('Invalid email')
            return v
        
        @field_validator('age')
        @classmethod
        def validate_age(cls, v):
            if v < 0:
                raise ValueError('Age must be positive')
            return v
    
    # 正常情况
    user = User(name='John', email='john@example.com', age=25)
    assert user.name == 'John'
    assert user.email == 'john@example.com'
    
    # 校验失败
    try:
        user = User(name='John', email='invalid', age=25)
        assert False, "Should have raised error"
    except FieldValidationError as e:
        assert e.field == 'email'
    
    print("   field_validator 测试通过")
    return True


def test_response():
    """测试 Response 装饰器"""
    print("4. 测试 Response...")
    
    from dataclasses import dataclass
    from cullinan.params import Response, get_response_models, ResponseSerializer
    
    @dataclass
    class UserResponse:
        id: int
        name: str
    
    @Response(model=UserResponse, status_code=200, description="Success")
    @Response(status_code=404, description="Not found")
    def get_user(user_id):
        pass
    
    models = get_response_models(get_user)
    assert len(models) == 2, f"Expected 2 models, got {len(models)}"
    # 注意：装饰器堆叠顺序是从下往上，所以 404 先加入，200 后加入
    status_codes = [m.status_code for m in models]
    assert 200 in status_codes, f"200 not in {status_codes}"
    assert 404 in status_codes, f"404 not in {status_codes}"

    # 测试序列化
    user = UserResponse(id=1, name='John')
    result = ResponseSerializer.serialize(user)
    assert result == {'id': 1, 'name': 'John'}, f"Got {result}"

    # 测试 JSON
    json_str = ResponseSerializer.to_json(user)
    assert '"id": 1' in json_str or '"id":1' in json_str, f"Got {json_str}"

    print("   Response 测试通过")
    return True


def test_file_param_enhanced():
    """测试增强的 File 参数"""
    print("5. 测试增强的 File 参数...")
    
    from cullinan.params import File, FileInfo
    
    # 创建带校验的 File 参数
    file_param = File(
        max_size=1024,
        min_size=10,
        allowed_types=['image/*', 'application/pdf'],
        multiple=False,
    )
    
    assert file_param.max_size == 1024
    assert file_param.min_size == 10
    assert file_param.multiple == False
    
    # 校验通过
    valid_file = FileInfo('test.png', b'x' * 100, 'image/png')
    file_param.validate_file(valid_file)  # 不抛异常
    
    # 文件太大
    large_file = FileInfo('test.png', b'x' * 2000, 'image/png')
    try:
        file_param.validate_file(large_file)
        assert False, "Should have raised error"
    except ValueError as e:
        assert 'exceeds maximum' in str(e)
    
    # 类型不允许
    wrong_type = FileInfo('test.txt', b'x' * 100, 'text/plain')
    try:
        file_param.validate_file(wrong_type)
        assert False, "Should have raised error"
    except ValueError as e:
        assert 'not allowed' in str(e)
    
    print("   File 参数增强测试通过")
    return True


def test_response_serializer():
    """测试 ResponseSerializer"""
    print("6. 测试 ResponseSerializer...")
    
    from dataclasses import dataclass
    from typing import List
    from cullinan.params import ResponseSerializer, DynamicBody
    
    @dataclass
    class Address:
        city: str
        zip_code: str
    
    @dataclass
    class User:
        id: int
        name: str
        address: Address
        tags: List[str]
    
    user = User(
        id=1,
        name='John',
        address=Address(city='NYC', zip_code='10001'),
        tags=['admin', 'active'],
    )
    
    result = ResponseSerializer.serialize(user)
    
    assert result['id'] == 1
    assert result['name'] == 'John'
    assert result['address']['city'] == 'NYC'
    assert result['tags'] == ['admin', 'active']
    
    # 测试 DynamicBody
    body = DynamicBody({'name': 'Test', 'value': 123})
    result = ResponseSerializer.serialize(body)
    assert result == {'name': 'Test', 'value': 123}
    
    print("   ResponseSerializer 测试通过")
    return True


def test_file_resolver():
    """测试文件参数解析器"""
    print("7. 测试文件参数解析器...")

    from cullinan.params import File, FileInfo, FileList
    from cullinan.params.resolver import ParamResolver

    # 模拟 Tornado 文件格式
    tornado_file = {
        'filename': 'test.png',
        'body': b'fake image content',
        'content_type': 'image/png',
    }

    # 测试单文件解析
    file_spec = File(max_size=1024 * 1024)
    result = ParamResolver._resolve_file_param([tornado_file], file_spec, 'avatar')

    assert isinstance(result, FileInfo)
    assert result.filename == 'test.png'
    assert result.size == 18
    assert result.content_type == 'image/png'

    # 测试多文件解析
    file_spec_multi = File(multiple=True, max_count=10)
    files_data = [
        {'filename': 'a.png', 'body': b'data1', 'content_type': 'image/png'},
        {'filename': 'b.jpg', 'body': b'data2', 'content_type': 'image/jpeg'},
    ]

    result = ParamResolver._resolve_file_param(files_data, file_spec_multi, 'files')

    assert isinstance(result, FileList)
    assert len(result) == 2
    assert result[0].filename == 'a.png'
    assert result[1].filename == 'b.jpg'

    print("   文件参数解析器测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("v0.90a5 新功能测试")
    print("=" * 60)
    print()
    
    tests = [
        test_imports,
        test_file_info,
        test_field_validator,
        test_response,
        test_file_param_enhanced,
        test_response_serializer,
        test_file_resolver,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

