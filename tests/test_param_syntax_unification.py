# -*- coding: utf-8 -*-
"""参数语法统一化测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_required_classmethod():
    """测试 .as_required() 类方法"""
    print("1. 测试 .as_required() 类方法...")

    from cullinan.params import Query, Body, Header, File, Path

    # Query.as_required()
    q = Query.as_required(int)
    assert q.required == True, f"Query.as_required() should set required=True, got {q.required}"
    assert q.type_ == int, f"Query.as_required(int) should have type_=int, got {q.type_}"

    # Body.as_required()
    b = Body.as_required(str, min_length=1)
    assert b.required == True
    assert b.type_ == str
    assert b.min_length == 1

    # Header.as_required()
    h = Header.as_required(str, alias="Authorization")
    assert h.required == True
    assert h.alias == "Authorization"

    # File.as_required()
    f = File.as_required(max_size=5*1024*1024)
    assert f.required == True
    assert f.max_size == 5*1024*1024

    # Path 默认就是 required，不需要 as_required()
    p = Path(int)
    assert p.required == True

    print("   .as_required() 类方法测试通过")
    return True


def test_default_value_syntax():
    """测试默认值语法 param: Type = ParamType(...)"""
    print("2. 测试默认值语法...")

    from cullinan.params import Query, Body, Header, File, ParamResolver

    def handler(
        self,
        # 新的统一语法
        page: int = Query(default=1),
        name: str = Body(required=True),
        auth: str = Header(alias="Authorization"),
        avatar: File = File(max_size=5*1024*1024),
    ):
        pass

    config = ParamResolver.analyze_params(handler)

    assert config['page']['source'] == 'query', f"page source: {config['page']['source']}"
    assert config['page']['type'] == int
    assert config['page']['default'] == 1

    assert config['name']['source'] == 'body', f"name source: {config['name']['source']}"
    assert config['name']['required'] == True

    assert config['auth']['source'] == 'header', f"auth source: {config['auth']['source']}"
    assert config['auth']['param_spec'].alias == "Authorization"

    assert config['avatar']['source'] == 'file', f"avatar source: {config['avatar']['source']}"

    print("   默认值语法测试通过")
    return True


def test_pure_type_annotation_as_query():
    """测试纯类型注解默认作为 Query"""
    print("3. 测试纯类型注解默认作为 Query...")

    from cullinan.params import ParamResolver

    def handler(
        self,
        page: int,           # 应该作为 Query(int)
        size: int = 10,      # 应该作为 Query(int, default=10)
        name: str = "test",  # 应该作为 Query(str, default="test")
        flag: bool = False,  # 应该作为 Query(bool, default=False)
    ):
        pass

    config = ParamResolver.analyze_params(handler)

    assert config['page']['source'] == 'query', f"page source: {config['page']['source']}"
    assert config['page']['type'] == int
    assert config['page']['required'] == True

    assert config['size']['source'] == 'query', f"size source: {config['size']['source']}"
    assert config['size']['default'] == 10
    assert config['size']['required'] == False

    assert config['name']['source'] == 'query', f"name source: {config['name']['source']}"
    assert config['name']['default'] == "test"

    assert config['flag']['source'] == 'query', f"flag source: {config['flag']['source']}"
    assert config['flag']['default'] == False

    print("   纯类型注解默认 Query 测试通过")
    return True


def test_file_required_syntax():
    """测试 File.as_required() 语法"""
    print("4. 测试 File.as_required() 语法...")

    from cullinan.params import File, ParamResolver

    def handler(
        self,
        avatar: File = File.as_required(max_size=5*1024*1024, allowed_types=['image/*']),
    ):
        pass

    config = ParamResolver.analyze_params(handler)

    assert config['avatar']['source'] == 'file'
    assert config['avatar']['required'] == True
    assert config['avatar']['param_spec'].max_size == 5*1024*1024
    assert config['avatar']['param_spec'].allowed_types == ['image/*']

    print("   File.as_required() 语法测试通过")
    return True


def test_backward_compatibility():
    """测试向后兼容性"""
    print("5. 测试向后兼容性...")

    from cullinan.params import Path, Query, Body, Header, DynamicBody, RawBody, ParamResolver

    # 旧语法仍然有效
    def old_style(
        self,
        id: Path(int),
        page: Query(int, default=1),
        name: Body(str, required=True),
        auth: Header(str, alias="Authorization"),
        body: DynamicBody,
        raw: RawBody,
    ):
        pass

    config = ParamResolver.analyze_params(old_style)

    assert config['id']['source'] == 'path'
    assert config['page']['source'] == 'query'
    assert config['name']['source'] == 'body'
    assert config['auth']['source'] == 'header'
    assert config['body']['source'] == 'body'
    assert config['raw']['source'] == 'raw_body'

    print("   向后兼容性测试通过")
    return True


def test_mixed_syntax():
    """测试混合语法"""
    print("6. 测试混合语法...")

    from cullinan.params import Path, Query, Body, Header, File, DynamicBody, ParamResolver

    def handler(
        self,
        # 旧语法
        id: Path(int),
        # 新语法（默认值方式）
        page: int = Query(default=1),
        name: str = Body(required=True),
        # 纯类型注解（作为 Query）
        limit: int = 100,
        # File.as_required()
        avatar: File = File.as_required(max_size=5*1024*1024),
        # DynamicBody
        extra: DynamicBody = None,
    ):
        pass

    config = ParamResolver.analyze_params(handler)

    assert config['id']['source'] == 'path'
    assert config['page']['source'] == 'query'
    assert config['name']['source'] == 'body'
    assert config['limit']['source'] == 'query'
    assert config['limit']['default'] == 100
    assert config['avatar']['source'] == 'file'
    assert config['avatar']['required'] == True
    assert config['extra']['source'] == 'body'

    print("   混合语法测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("参数语法统一化测试")
    print("=" * 60)
    print()

    tests = [
        test_required_classmethod,
        test_default_value_syntax,
        test_pure_type_annotation_as_query,
        test_file_required_syntax,
        test_backward_compatibility,
        test_mixed_syntax,
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

