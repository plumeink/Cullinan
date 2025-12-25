# -*- coding: utf-8 -*-
"""Cullinan IoC/DI 2.0 - Factory 统一创建路径

作者：Plumeink

本模块实现 2.0 架构的 Factory 层：
- 统一实例创建路径
- 集成现有 InjectionExecutor/Injectable（如需要）
- 条件过滤、循环依赖检测、scope 缓存

注意：当前 ApplicationContext 已内置基本的 factory 功能，
本模块提供扩展接口以便后续集成现有注入系统。
"""

from typing import Any, Optional, Callable, List, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .context import ApplicationContext
    from .definitions import Definition

logger = logging.getLogger(__name__)


class Factory:
    """统一实例创建工厂
    
    职责（按 2.6.4 Contract）：
    - 条件过滤
    - 循环依赖检测（有序链）
    - scope 缓存
    - 调用 definition.factory(ctx)
    - 调用 injection executor 完成依赖注入（如启用）
    """
    
    __slots__ = ('_context', '_injection_enabled', '_post_processors')
    
    def __init__(self, context: 'ApplicationContext'):
        """初始化 Factory
        
        Args:
            context: ApplicationContext 实例
        """
        self._context = context
        self._injection_enabled = False
        self._post_processors: List[Callable[[Any, 'Definition'], Any]] = []
    
    def enable_injection(self) -> None:
        """启用依赖注入后处理"""
        self._injection_enabled = True
    
    def add_post_processor(self, processor: Callable[[Any, 'Definition'], Any]) -> None:
        """添加实例后处理器
        
        Args:
            processor: 接收 (instance, definition) 返回处理后的 instance
        """
        self._post_processors.append(processor)
    
    def resolve(self, definition: 'Definition', injection_point: Optional[str] = None) -> Any:
        """解析并创建实例
        
        委托给 ApplicationContext._resolve()，但可在此添加额外处理。
        
        Args:
            definition: 定义
            injection_point: 注入点（用于诊断）
            
        Returns:
            实例对象
        """
        # 使用 context 的内部解析方法
        instance = self._context._resolve(definition)
        
        # 应用后处理器
        for processor in self._post_processors:
            try:
                instance = processor(instance, definition)
            except Exception as e:
                logger.warning(f"后处理器执行失败: {e}")
        
        return instance
    
    def create_raw(self, definition: 'Definition') -> Any:
        """直接调用 factory 创建原始实例（不经过 scope 缓存）
        
        Args:
            definition: 定义
            
        Returns:
            新创建的实例
        """
        return definition.factory(self._context)


__all__ = ['Factory']

