# -*- coding: utf-8 -*-
"""Legacy middleware registration API (Backward Compatibility).

This module provides backward compatibility for the old middleware
registration API. It will be removed in v1.0.

DEPRECATED: Use @middleware decorator instead.

Author: Plumeink
"""

# ============================================================================
# BACKWARD_COMPAT: v0.8 - 以下代码用于向后兼容，计划在 v1.0 移除
# 替代方案：使用 @middleware 装饰器代替手动注册
# ============================================================================

import logging
from typing import Type, Optional
from cullinan.deprecation import deprecated, warn_deprecated

logger = logging.getLogger(__name__)


@deprecated(
    version="0.8",
    alternative="@middleware decorator",
    removal_version="1.0"
)
def register_middleware_manual(middleware_class: Type,
                              priority: int = 100,
                              name: Optional[str] = None):
    """手动注册中间件（已废弃）.

    此函数已废弃，建议使用 @middleware 装饰器。

    Args:
        middleware_class: 中间件类
        priority: 优先级
        name: 可选的名称

    Example (DEPRECATED):
        >>> register_middleware_manual(MyMiddleware, priority=50)

    Recommended:
        >>> @middleware(priority=50)
        >>> class MyMiddleware(Middleware):
        ...     pass
    """
    from cullinan.middleware.registry import get_middleware_registry

    registry = get_middleware_registry()
    registry.register(middleware_class, priority=priority, name=name)

    logger.warning(
        f"register_middleware_manual() is deprecated. "
        f"Use @middleware decorator instead."
    )


@deprecated(
    version="0.8",
    alternative="MiddlewareRegistry.get_all()",
    removal_version="1.0"
)
def get_registered_middlewares():
    """获取所有已注册的中间件（已废弃）.

    Returns:
        所有已注册的中间件列表
    """
    from cullinan.middleware.registry import get_middleware_registry

    registry = get_middleware_registry()
    return registry.get_all()


# ============================================================================
# END BACKWARD_COMPAT
# ============================================================================

