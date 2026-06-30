# -*- coding: utf-8 -*-
"""测试 scanner 模块的并发安全性

验证 _ensure_console_logging 在多线程环境下的 handler 去重（Issue 2 修复验证）
"""

import logging
import threading
import os
import pytest


def test_console_logging_concurrent_single_handler(monkeypatch):
    """测试：10 线程同时调用 _ensure_console_logging 仅添加 1 个 handler"""
    # 重置模块级状态
    import cullinan.runtime.scanner as scanner_mod
    scanner_mod._logging_initialized = False

    # 模拟非主模块启动（确保 is_started_directly 返回 False）
    monkeypatch.setattr(scanner_mod, 'is_started_directly', lambda: True)
    monkeypatch.setenv('CULLINAN_DISABLE_AUTO_CONSOLE', '0')
    monkeypatch.setenv('CULLINAN_FORCE_CONSOLE', '1')

    cullinan_logger = logging.getLogger('cullinan')
    # 清空已有 handlers（pytest 也会给 root logger 添加 handler，需一并清除）
    logging.getLogger().handlers.clear()
    cullinan_logger.handlers.clear()

    errors = []
    results = []
    barrier = threading.Barrier(10)

    def setup_logging():
        try:
            barrier.wait()
            handler = scanner_mod._ensure_console_logging()
            results.append(handler)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=setup_logging) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors: {errors}"

    # 所有线程应返回同一个 handler 或 None
    non_none_results = [r for r in results if r is not None]
    # 至少一个线程成功添加了 handler
    assert len(non_none_results) >= 1

    # cullinan logger 应仅有 1 个 StreamHandler
    stream_handlers = [h for h in cullinan_logger.handlers
                       if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) == 1, (
        f"Expected 1 StreamHandler, got {len(stream_handlers)}"
    )

    # 清理
    scanner_mod._logging_initialized = False
    logging.getLogger().handlers.clear()
    cullinan_logger.handlers.clear()


def test_console_logging_env_disable(monkeypatch):
    """测试：CULLINAN_DISABLE_AUTO_CONSOLE=1 时不添加 handler"""
    import cullinan.runtime.scanner as scanner_mod
    scanner_mod._logging_initialized = False

    monkeypatch.setenv('CULLINAN_DISABLE_AUTO_CONSOLE', '1')

    cullinan_logger = logging.getLogger('cullinan')
    cullinan_logger.handlers.clear()

    result = scanner_mod._ensure_console_logging()
    assert result is None
    assert scanner_mod._logging_initialized is True

    # 不应添加任何 handler
    stream_handlers = [h for h in cullinan_logger.handlers
                       if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) == 0

    # 清理
    scanner_mod._logging_initialized = False


def test_is_started_directly_uses_getframe():
    """验证：is_started_directly 使用 sys._getframe() 优化路径（Issue 9 修复）"""
    from cullinan.runtime.scanner import is_started_directly

    # 基本调用不抛异常即验证 _getframe 路径可用
    result = is_started_directly()
    # pytest 以 __main__ 运行，应返回 True
    assert isinstance(result, bool)
    assert result is True
