# -*- coding: utf-8 -*-
"""
测试 Service 生命周期方法 (使用 ApplicationContext)

验证：
1. on_post_construct() 被调用
2. on_startup() 被调用
3. on_shutdown() 被调用
4. on_pre_destroy() 被调用
"""

import logging
import pytest

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

from cullinan.core import ApplicationContext, set_application_context, InjectByName
from cullinan.core.pending import PendingRegistry
from cullinan.core.services import service, Service

pytestmark = [
    pytest.mark.filterwarnings("ignore::cullinan.core.semantic_rules.ComponentDiscoveryWarning"),
    pytest.mark.filterwarnings("ignore::cullinan.core.semantic_rules.InjectionSemanticWarning"),
]


def test_service_lifecycle():
    # Reset state
    PendingRegistry.reset()

    # 记录调用的方法
    lifecycle_calls = []

    @service
    class TestService(Service):
        def on_post_construct(self):
            """构造后调用"""
            lifecycle_calls.append('on_post_construct')

        def on_startup(self):
            """启动时调用"""
            lifecycle_calls.append('on_startup')

        def on_shutdown(self):
            """关闭时调用"""
            lifecycle_calls.append('on_shutdown')

        def on_pre_destroy(self):
            """销毁前调用"""
            lifecycle_calls.append('on_pre_destroy')

    @service
    class DependentService(Service):
        """依赖 TestService 的 Service"""
        test_service = InjectByName('TestService')

        def on_post_construct(self):
            lifecycle_calls.append('DependentService.on_post_construct')

        def on_startup(self):
            lifecycle_calls.append('DependentService.on_startup')

    # 创建 ApplicationContext
    ctx = ApplicationContext()
    set_application_context(ctx)
    try:
        ctx.refresh()
        assert 'on_post_construct' in lifecycle_calls
        assert 'on_startup' in lifecycle_calls

        init_idx = lifecycle_calls.index('on_post_construct')
        startup_idx = lifecycle_calls.index('on_startup')
        assert init_idx < startup_idx

        test_idx = lifecycle_calls.index('on_post_construct')
        dep_idx = lifecycle_calls.index('DependentService.on_post_construct')
        assert test_idx < dep_idx
        lifecycle_calls.clear()
        ctx.shutdown()

        assert 'on_shutdown' in lifecycle_calls
        assert 'on_pre_destroy' in lifecycle_calls
    finally:
        set_application_context(None)
        PendingRegistry.reset()
