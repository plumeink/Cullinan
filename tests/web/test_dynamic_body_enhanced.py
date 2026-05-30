# -*- coding: utf-8 -*-
"""DynamicBody 增强功能测试

测试新增的判空方法和安全访问功能。

Author: Plumeink
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cullinan.params import DynamicBody, SafeAccessor, EMPTY


def test_basic_access():
    """测试基本访问"""
    print("1. 测试基本访问...")
    body = DynamicBody({'name': 'John', 'age': 25})
    
    assert body.name == 'John'
    assert body.age == 25
    assert body.get('name') == 'John'
    assert body.get('missing', 'default') == 'default'
    
    print("   PASSED")


def test_has_method():
    """测试 has 方法"""
    print("2. 测试 has 方法...")
    body = DynamicBody({'name': 'John', 'email': None, 'empty_str': ''})
    
    assert body.has('name') == True
    assert body.has('email') == True  # 存在但值为 None
    assert body.has('missing') == False
    assert body.has('empty_str') == True
    
    print("   PASSED")


def test_has_value_method():
    """测试 has_value 方法"""
    print("3. 测试 has_value 方法...")
    body = DynamicBody({
        'name': 'John',
        'email': None,
        'empty_str': '',
        'empty_list': [],
        'zero': 0,
        'valid_list': [1, 2, 3],
    })
    
    assert body.has_value('name') == True
    assert body.has_value('email') == False  # None
    assert body.has_value('empty_str') == False  # ''
    assert body.has_value('empty_list') == False  # []
    assert body.has_value('zero') == False  # 0 is falsy
    assert body.has_value('valid_list') == True
    assert body.has_value('missing') == False
    
    print("   PASSED")


def test_is_empty_methods():
    """测试 is_empty 和 is_not_empty 方法"""
    print("4. 测试 is_empty/is_not_empty 方法...")
    
    empty_body = DynamicBody({})
    assert empty_body.is_empty() == True
    assert empty_body.is_not_empty() == False
    
    body = DynamicBody({'name': 'John'})
    assert body.is_empty() == False
    assert body.is_not_empty() == True
    
    print("   PASSED")


def test_is_null_methods():
    """测试 is_null 和 is_not_null 方法"""
    print("5. 测试 is_null/is_not_null 方法...")
    body = DynamicBody({'name': 'John', 'email': None})
    
    assert body.is_null('name') == False
    assert body.is_not_null('name') == True
    
    assert body.is_null('email') == True  # None
    assert body.is_not_null('email') == False
    
    assert body.is_null('missing') == True  # 不存在
    assert body.is_not_null('missing') == False
    
    print("   PASSED")


def test_get_nested():
    """测试嵌套安全访问"""
    print("6. 测试 get_nested 方法...")
    body = DynamicBody({
        'user': {
            'name': 'John',
            'address': {
                'city': 'New York',
                'zip': '10001'
            }
        }
    })
    
    # 存在的嵌套路径
    assert body.get_nested('user.name') == 'John'
    assert body.get_nested('user.address.city') == 'New York'
    
    # 不存在的嵌套路径
    assert body.get_nested('user.phone', 'N/A') == 'N/A'
    assert body.get_nested('user.address.country', 'USA') == 'USA'
    assert body.get_nested('missing.path.deep', 'default') == 'default'
    
    # 嵌套返回 DynamicBody
    address = body.get_nested('user.address')
    assert isinstance(address, DynamicBody)
    assert address.city == 'New York'
    
    print("   PASSED")


def test_typed_getters():
    """测试类型化的 getter 方法"""
    print("7. 测试类型化 getter 方法...")
    body = DynamicBody({
        'name': 'John',
        'age': 25,
        'price': 19.99,
        'active': True,
        'active_str': 'true',
        'tags': ['a', 'b', 'c'],
        'invalid_int': 'not_a_number',
    })
    
    # get_str
    assert body.get_str('name') == 'John'
    assert body.get_str('age') == '25'  # 转换为字符串
    assert body.get_str('missing') == ''
    assert body.get_str('missing', 'default') == 'default'
    
    # get_int
    assert body.get_int('age') == 25
    assert body.get_int('missing') == 0
    assert body.get_int('missing', 100) == 100
    assert body.get_int('invalid_int') == 0  # 转换失败返回默认值
    
    # get_float
    assert body.get_float('price') == 19.99
    assert body.get_float('age') == 25.0
    assert body.get_float('missing') == 0.0
    
    # get_bool
    assert body.get_bool('active') == True
    assert body.get_bool('active_str') == True
    assert body.get_bool('missing') == False
    
    # get_list
    assert body.get_list('tags') == ['a', 'b', 'c']
    assert body.get_list('missing') == []
    assert body.get_list('missing', ['default']) == ['default']
    assert body.get_list('name') == []  # 非列表返回默认值
    
    print("   PASSED")


def test_safe_accessor_basic():
    """测试 SafeAccessor 基本功能"""
    print("8. 测试 SafeAccessor 基本功能...")
    body = DynamicBody({
        'user': {
            'name': 'John',
            'address': {
                'city': 'New York'
            }
        }
    })
    
    # 访问存在的属性
    assert body.safe.user.name.value == 'John'
    assert body.safe.user.address.city.value == 'New York'
    
    # 访问不存在的属性
    assert body.safe.user.phone.value is None
    assert body.safe.user.phone.value_or('N/A') == 'N/A'
    assert body.safe.missing.deep.path.value_or('default') == 'default'
    
    print("   PASSED")


def test_safe_accessor_exists():
    """测试 SafeAccessor 存在性检查"""
    print("9. 测试 SafeAccessor exists/is_null/is_not_null...")
    body = DynamicBody({
        'user': {'name': 'John', 'email': None}
    })
    
    # exists
    assert body.safe.user.exists == True
    assert body.safe.user.name.exists == True
    assert body.safe.user.phone.exists == False
    assert body.safe.missing.exists == False
    
    # is_null / is_not_null
    assert body.safe.user.name.is_null == False
    assert body.safe.user.name.is_not_null == True
    assert body.safe.user.email.is_null == True  # None
    assert body.safe.user.phone.is_null == True  # 不存在
    
    print("   PASSED")


def test_safe_accessor_bool():
    """测试 SafeAccessor 布尔转换"""
    print("10. 测试 SafeAccessor 布尔转换...")
    body = DynamicBody({
        'active': True,
        'inactive': False,
        'name': 'John',
        'empty': '',
    })
    
    assert bool(body.safe.active) == True
    assert bool(body.safe.inactive) == False
    assert bool(body.safe.name) == True
    assert bool(body.safe.empty) == False
    assert bool(body.safe.missing) == False
    
    print("   PASSED")


def test_backward_compatibility():
    """测试向后兼容性"""
    print("11. 测试向后兼容性...")
    body = DynamicBody({'name': 'John', 'age': 25})
    
    # 原有功能仍然正常
    assert body.name == 'John'
    assert body['name'] == 'John'
    assert 'name' in body
    assert body.get('name') == 'John'
    assert body.to_dict() == {'name': 'John', 'age': 25}
    assert len(body) == 2
    assert bool(body) == True
    
    # 迭代
    keys = list(body.keys())
    assert 'name' in keys
    assert 'age' in keys
    
    print("   PASSED")


def test_empty_sentinel():
    """测试 EMPTY 哨兵"""
    print("12. 测试 EMPTY 哨兵...")
    
    assert bool(EMPTY) == False
    assert EMPTY is EMPTY  # 单例
    
    # EMPTY 与 None 不同
    assert EMPTY is not None
    
    print("   PASSED")


def test_complex_nested():
    """测试复杂嵌套场景"""
    print("13. 测试复杂嵌套场景...")
    body = DynamicBody({
        'users': [
            {'name': 'John', 'role': 'admin'},
            {'name': 'Jane', 'role': 'user'}
        ],
        'config': {
            'debug': True,
            'database': {
                'host': 'localhost',
                'port': 5432
            }
        }
    })
    
    # 通过 get_nested 访问
    assert body.get_nested('config.debug') == True
    assert body.get_nested('config.database.host') == 'localhost'
    assert body.get_nested('config.database.port') == 5432
    
    # 列表需要直接访问
    assert len(body.users) == 2
    
    # safe accessor
    assert body.safe.config.database.host.value == 'localhost'
    assert body.safe.config.missing.deep.value_or('default') == 'default'
    
    print("   PASSED")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("DynamicBody 增强功能测试")
    print("=" * 60)
    print()
    
    tests = [
        test_basic_access,
        test_has_method,
        test_has_value_method,
        test_is_empty_methods,
        test_is_null_methods,
        test_get_nested,
        test_typed_getters,
        test_safe_accessor_basic,
        test_safe_accessor_exists,
        test_safe_accessor_bool,
        test_backward_compatibility,
        test_empty_sentinel,
        test_complex_nested,
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
            print(f"   ERROR: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("所有测试通过!")
        return True
    else:
        print(f"有 {failed} 个测试失败!")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

