# -*- coding: utf-8 -*-
"""依赖注入工具函数（Task-3.4）

提取公共的注入逻辑，减少重复代码。

作者：Plumeink
"""

from typing import Type, Optional, Any


def resolve_dependency_name_from_annotation(
    explicit_name: Optional[str],
    attr_name: str,
    attr_type: Any
) -> str:
    """从类型注解解析依赖名称（统一逻辑）

    优先级：
    1. 明确指定的名称
    2. 字符串类型注解（'ServiceName'）
    3. 实际类型的 __name__
    4. 属性名转换（snake_case -> PascalCase）

    Args:
        explicit_name: 明确指定的名称
        attr_name: 属性名
        attr_type: 类型注解

    Returns:
        解析后的依赖名称

    Example:
        >>> resolve_dependency_name_from_annotation(None, 'user_service', UserService)
        'UserService'
        >>> resolve_dependency_name_from_annotation(None, 'user_service', 'UserService')
        'UserService'
        >>> resolve_dependency_name_from_annotation('MyService', 'service', str)
        'MyService'
    """
    # 1. 优先使用明确指定的名称
    if explicit_name:
        return explicit_name

    # 2. 支持字符串类型注解（无需 import）
    if isinstance(attr_type, str):
        return attr_type

    # 3. 从实际类型推断
    if attr_type is not Any and hasattr(attr_type, '__name__'):
        return attr_type.__name__

    # 4. 回退到属性名转换（snake_case -> PascalCase）
    if '_' in attr_name:
        return ''.join(word.capitalize() for word in attr_name.split('_'))

    return attr_name


def convert_snake_to_pascal(name: str) -> str:
    """将 snake_case 转换为 PascalCase

    Args:
        name: snake_case 格式的名称

    Returns:
        PascalCase 格式的名称

    Example:
        >>> convert_snake_to_pascal('user_service')
        'UserService'
        >>> convert_snake_to_pascal('cache')
        'Cache'
    """
    if '_' in name:
        return ''.join(word.capitalize() for word in name.split('_'))
    return name.capitalize() if name else name

