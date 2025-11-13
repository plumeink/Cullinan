# -*- coding: utf-8 -*-
"""Test service lifecycle strict mode after fix.

验证 Service 生命周期方法在同步/异步路径的严格检测。
"""

import pytest
import asyncio
from cullinan.service.base import Service
from cullinan.service.registry import get_service_registry
from cullinan.core import get_injection_registry


class SyncLifecycleService(Service):
    """完全同步的生命周期服务"""

    def on_init(self):
        self.init_called = True

    def on_startup(self):
        self.startup_called = True

    def on_shutdown(self):
        self.shutdown_called = True

    def on_destroy(self):
        self.destroy_called = True


class AsyncOnInitService(Service):
    """on_init 是异步的服务"""

    async def on_init(self):
        await asyncio.sleep(0.01)
        self.init_called = True


class AsyncOnStartupService(Service):
    """on_startup 是异步的服务"""

    def on_init(self):
        self.init_called = True

    async def on_startup(self):
        await asyncio.sleep(0.01)
        self.startup_called = True


class AsyncOnShutdownService(Service):
    """on_shutdown 是异步的服务"""

    def on_init(self):
        self.init_called = True

    async def on_shutdown(self):
        await asyncio.sleep(0.01)
        self.shutdown_called = True


class AsyncOnDestroyService(Service):
    """on_destroy 是异步的服务"""

    def on_init(self):
        self.init_called = True

    async def on_destroy(self):
        await asyncio.sleep(0.01)
        self.destroy_called = True


class TestServiceLifecycleStrictMode:
    """测试服务生命周期严格模式"""

    def setup_method(self):
        """每个测试前清理注册表"""
        registry = get_service_registry()
        registry.clear()
        registry._instances.clear()
        registry._initialized.clear()

        injection_registry = get_injection_registry()
        injection_registry.clear()

    def test_sync_lifecycle_works_on_sync_path(self):
        """测试：完全同步的生命周期在同步路径正常工作"""
        registry = get_service_registry()
        registry.register('SyncService', SyncLifecycleService)

        # 同步初始化 - 应该成功
        registry.initialize_all()

        instance = registry.get_instance('SyncService')
        assert instance is not None
        assert instance.init_called is True
        assert instance.startup_called is True

        # 同步销毁 - 应该成功
        registry.destroy_all()
        assert instance.shutdown_called is True
        assert instance.destroy_called is True

    def test_async_on_init_fails_on_sync_path(self):
        """测试：async on_init 在同步路径应该抛出错误（wrapped in DependencyResolutionError）"""
        from cullinan.core.exceptions import DependencyResolutionError

        registry = get_service_registry()
        registry.register('AsyncInitService', AsyncOnInitService)

        # 尝试同步获取实例 - 应该失败
        with pytest.raises(DependencyResolutionError) as exc_info:
            registry.get_instance('AsyncInitService')

        # 检查错误消息包含关键信息
        error_msg = str(exc_info.value)
        assert 'AsyncInitService' in error_msg
        assert 'on_init()' in error_msg or 'async' in error_msg.lower()

    def test_async_on_startup_fails_on_sync_path(self):
        """测试：async on_startup 在同步路径应该抛出 RuntimeError"""
        registry = get_service_registry()
        registry.register('AsyncStartupService', AsyncOnStartupService)

        # 尝试同步初始化 - 应该失败
        with pytest.raises(RuntimeError) as exc_info:
            registry.initialize_all()

        assert 'on_startup()' in str(exc_info.value)
        assert 'is async' in str(exc_info.value)
        assert 'initialize_all_async' in str(exc_info.value)

    def test_async_on_shutdown_fails_on_sync_path(self):
        """测试：async on_shutdown 在同步路径应该抛出 RuntimeError"""
        registry = get_service_registry()
        registry.register('AsyncShutdownService', AsyncOnShutdownService)

        # 先初始化（同步 on_init）
        instance = registry.get_instance('AsyncShutdownService')
        assert instance is not None

        # 尝试同步销毁 - 应该失败
        with pytest.raises(RuntimeError) as exc_info:
            registry.destroy_all()

        assert 'on_shutdown()' in str(exc_info.value)
        assert 'is async' in str(exc_info.value)
        assert 'destroy_all_async' in str(exc_info.value)

    def test_async_on_destroy_fails_on_sync_path(self):
        """测试：async on_destroy 在同步路径应该抛出 RuntimeError"""
        registry = get_service_registry()
        registry.register('AsyncDestroyService', AsyncOnDestroyService)

        # 先初始化（同步 on_init）
        instance = registry.get_instance('AsyncDestroyService')
        assert instance is not None

        # 尝试同步销毁 - 应该失败
        with pytest.raises(RuntimeError) as exc_info:
            registry.destroy_all()

        assert 'on_destroy()' in str(exc_info.value)
        assert 'is async' in str(exc_info.value)
        assert 'destroy_all_async' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_lifecycle_works_on_async_path(self):
        """测试：异步生命周期在异步路径正常工作"""
        registry = get_service_registry()
        registry.register('AsyncInitService', AsyncOnInitService)
        registry.register('AsyncStartupService', AsyncOnStartupService)

        # 异步初始化 - 应该成功
        await registry.initialize_all_async()

        init_instance = registry.get_instance('AsyncInitService')
        startup_instance = registry.get_instance('AsyncStartupService')

        assert init_instance is not None
        assert hasattr(init_instance, 'init_called')
        assert init_instance.init_called is True

        assert startup_instance is not None
        assert hasattr(startup_instance, 'init_called')
        assert startup_instance.init_called is True
        # startup_called 应该在 on_startup 中设置
        assert hasattr(startup_instance, 'startup_called')
        assert startup_instance.startup_called is True

    @pytest.mark.asyncio
    async def test_async_shutdown_works_on_async_path(self):
        """测试：异步 shutdown 在异步路径正常工作"""
        registry = get_service_registry()
        registry.register('AsyncShutdownService', AsyncOnShutdownService)
        registry.register('AsyncDestroyService', AsyncOnDestroyService)

        # 先初始化
        shutdown_instance = registry.get_instance('AsyncShutdownService')
        destroy_instance = registry.get_instance('AsyncDestroyService')

        # 异步销毁 - 应该成功
        await registry.destroy_all_async()

        assert shutdown_instance.shutdown_called is True
        assert destroy_instance.destroy_called is True

    @pytest.mark.asyncio
    async def test_mixed_sync_async_lifecycle(self):
        """测试：混合同步/异步生命周期的服务"""

        class MixedService(Service):
            async def on_init(self):
                await asyncio.sleep(0.01)
                self.init_called = True

            def on_startup(self):
                # 同步 startup
                self.startup_called = True

            async def on_shutdown(self):
                await asyncio.sleep(0.01)
                self.shutdown_called = True

        registry = get_service_registry()
        registry.register('MixedService', MixedService)

        # 必须使用异步路径（因为有 async on_init）
        await registry.initialize_all_async()

        instance = registry.get_instance('MixedService')
        assert instance.init_called is True
        assert instance.startup_called is True

        # 必须使用异步销毁（因为有 async on_shutdown）
        await registry.destroy_all_async()
        assert instance.shutdown_called is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

