# -*- coding: utf-8 -*-
"""统一的注入元信息模型（Task-3.3）

提供统一的注入点表示和元信息管理，简化注入逻辑。

作者：Plumeink
"""

from dataclasses import dataclass, field
from typing import Type, Optional, Any, Dict, List
from enum import Enum


class ResolveStrategy(Enum):
    """依赖解析策略"""
    AUTO = 'auto'        # 自动推断（优先类型，回退名称）
    BY_TYPE = 'by_type'  # 按类型解析
    BY_NAME = 'by_name'  # 按名称解析


@dataclass
class InjectionPoint:
    """统一的注入点元信息

    表示一个需要注入依赖的位置（字段或构造函数参数）。
    这是所有注入方式（Inject、InjectByName、@injectable）的统一表示。

    Attributes:
        attr_name: 属性名称（如 'user_service'）
        dependency_name: 依赖名称（如 'UserService'）
        required: 是否必需（True 表示找不到会抛出异常）
        attr_type: 类型注解（如果有的话）
        resolve_strategy: 解析策略

    Example:
        # 从 Inject() 创建
        point = InjectionPoint(
            attr_name='user_service',
            dependency_name='UserService',
            required=True,
            attr_type=UserService,
            resolve_strategy=ResolveStrategy.AUTO
        )

        # 从 InjectByName() 创建
        point = InjectionPoint(
            attr_name='user_service',
            dependency_name='UserService',
            required=True,
            attr_type=None,
            resolve_strategy=ResolveStrategy.BY_NAME
        )
    """
    # 基本信息
    attr_name: str                          # 属性名称
    dependency_name: str                    # 依赖名称
    required: bool = True                   # 是否必需

    # 类型信息（可选）
    attr_type: Optional[Type] = None        # 类型注解

    # 解析策略
    resolve_strategy: ResolveStrategy = ResolveStrategy.AUTO

    # 缓存标志（内部使用，不序列化）
    _cache_enabled: bool = field(default=True, init=False, repr=False)

    def __post_init__(self):
        """验证和标准化"""
        if not self.attr_name:
            raise ValueError("attr_name cannot be empty")
        if not self.dependency_name:
            raise ValueError("dependency_name cannot be empty")

    def to_legacy_tuple(self) -> tuple:
        """转换为旧格式（向后兼容）

        Returns:
            (dependency_name, required) 元组
        """
        return (self.dependency_name, self.required)

    @classmethod
    def from_legacy_tuple(cls, attr_name: str, legacy: tuple) -> 'InjectionPoint':
        """从旧格式创建（向后兼容）

        Args:
            attr_name: 属性名称
            legacy: (dependency_name, required) 元组

        Returns:
            InjectionPoint 实例
        """
        dependency_name, required = legacy
        return cls(
            attr_name=attr_name,
            dependency_name=dependency_name,
            required=required,
            resolve_strategy=ResolveStrategy.AUTO
        )

    def __hash__(self):
        """支持作为字典键"""
        return hash((self.attr_name, self.dependency_name))

    def __eq__(self, other):
        """支持比较"""
        if not isinstance(other, InjectionPoint):
            return False
        return (
            self.attr_name == other.attr_name and
            self.dependency_name == other.dependency_name and
            self.required == other.required
        )


class UnifiedInjectionMetadata:
    """统一的注入元数据（Task-3.3）

    管理一个类的所有注入点。
    替代旧的 InjectionMetadata，使用 InjectionPoint 作为统一表示。

    Attributes:
        target_class: 目标类
        injection_points: 注入点列表

    Example:
        metadata = UnifiedInjectionMetadata(UserController)
        metadata.add_injection_point(InjectionPoint(
            attr_name='user_service',
            dependency_name='UserService',
            required=True
        ))
    """

    __slots__ = ('target_class', 'injection_points', '_points_by_attr')

    def __init__(self, target_class: Type):
        """初始化元数据

        Args:
            target_class: 目标类
        """
        self.target_class = target_class
        self.injection_points: List[InjectionPoint] = []
        self._points_by_attr: Dict[str, InjectionPoint] = {}

    def add_injection_point(self, point: InjectionPoint) -> None:
        """添加注入点

        Args:
            point: 注入点
        """
        # 检查重复
        if point.attr_name in self._points_by_attr:
            # 更新现有的
            existing = self._points_by_attr[point.attr_name]
            self.injection_points.remove(existing)

        self.injection_points.append(point)
        self._points_by_attr[point.attr_name] = point

    def get_injection_point(self, attr_name: str) -> Optional[InjectionPoint]:
        """获取指定属性的注入点

        Args:
            attr_name: 属性名称

        Returns:
            注入点，如果不存在则返回 None
        """
        return self._points_by_attr.get(attr_name)

    def has_injections(self) -> bool:
        """检查是否有注入点

        Returns:
            True 如果有注入点
        """
        return len(self.injection_points) > 0

    def to_legacy_format(self) -> Dict[str, tuple]:
        """转换为旧格式（向后兼容）

        Returns:
            {attr_name: (dependency_name, required)} 字典
        """
        return {
            point.attr_name: point.to_legacy_tuple()
            for point in self.injection_points
        }

    @classmethod
    def from_legacy_format(cls, target_class: Type, legacy: Dict[str, tuple]) -> 'UnifiedInjectionMetadata':
        """从旧格式创建（向后兼容）

        Args:
            target_class: 目标类
            legacy: {attr_name: (dependency_name, required)} 字典

        Returns:
            UnifiedInjectionMetadata 实例
        """
        metadata = cls(target_class)
        for attr_name, legacy_tuple in legacy.items():
            point = InjectionPoint.from_legacy_tuple(attr_name, legacy_tuple)
            metadata.add_injection_point(point)
        return metadata

    def __repr__(self):
        return f"UnifiedInjectionMetadata({self.target_class.__name__}, {len(self.injection_points)} points)"

    def __len__(self):
        return len(self.injection_points)


# ============================================================================
# 辅助函数
# ============================================================================

def infer_dependency_name(attr_name: str, attr_type: Optional[Type] = None,
                         explicit_name: Optional[str] = None) -> str:
    """推断依赖名称

    优先���：
    1. 显式指定的名称（explicit_name）
    2. 类型注解的类名（attr_type.__name__）
    3. 属性名转换（snake_case -> PascalCase）

    Args:
        attr_name: 属性名称（如 'user_service'）
        attr_type: 类型注解（如 UserService）
        explicit_name: 显式指定的名称（如 'UserService'）

    Returns:
        推断的依赖名称

    Example:
        >>> infer_dependency_name('user_service', UserService)
        'UserService'
        >>> infer_dependency_name('user_service', None, 'CustomService')
        'CustomService'
        >>> infer_dependency_name('email_service')
        'EmailService'
    """
    # 1. 优先使用显式名称
    if explicit_name:
        return explicit_name

    # 2. 从类型注解推断
    if attr_type is not None:
        # 支持字符串注解（如 'UserService'）
        if isinstance(attr_type, str):
            return attr_type
        # 支持实际类型
        if hasattr(attr_type, '__name__'):
            return attr_type.__name__

    # 3. 从属性名推断（snake_case -> PascalCase）
    if '_' in attr_name:
        # 例如: user_service -> UserService
        return ''.join(word.capitalize() for word in attr_name.split('_'))

    # 回退：返回属性名本身
    return attr_name


__all__ = [
    'InjectionPoint',
    'UnifiedInjectionMetadata',
    'ResolveStrategy',
    'infer_dependency_name',
]

