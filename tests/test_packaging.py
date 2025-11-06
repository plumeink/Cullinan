# -*- coding: utf-8 -*-
"""
Cullinan 打包支持单元测试

测试环境检测和模块扫描功能
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
import os

# 导入要测试的函数
from cullinan.application import (
    is_pyinstaller_frozen,
    is_nuitka_compiled,
    get_pyinstaller_mode,
    get_nuitka_standalone_mode,
)


class TestEnvironmentDetection(unittest.TestCase):
    """测试环境检测功能"""

    def test_normal_environment(self):
        """测试正常（非打包）环境"""
        # 在正常环境下，这些函数应该返回 False/None
        self.assertFalse(is_pyinstaller_frozen())
        self.assertIsNone(get_pyinstaller_mode())

    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/_MEI123456', create=True)
    def test_pyinstaller_onefile_detection(self):
        """测试 PyInstaller onefile 模式检测"""
        self.assertTrue(is_pyinstaller_frozen())
        mode = get_pyinstaller_mode()
        self.assertEqual(mode, 'onefile')

    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/app/dist/myapp', create=True)
    def test_pyinstaller_onedir_detection(self):
        """测试 PyInstaller onedir 模式检测"""
        self.assertTrue(is_pyinstaller_frozen())
        mode = get_pyinstaller_mode()
        self.assertEqual(mode, 'onedir')

    @patch('sys.__compiled__', True, create=True)
    def test_nuitka_detection(self):
        """测试 Nuitka 编译环境检测"""
        self.assertTrue(is_nuitka_compiled())

    @patch('sys.frozen', True, create=True)
    @patch('sys.__compiled__', True, create=True)
    @patch('sys.executable', '/tmp/onefile_12345/myapp')
    def test_nuitka_onefile_detection(self):
        """测试 Nuitka onefile 模式检测"""
        mode = get_nuitka_standalone_mode()
        self.assertEqual(mode, 'onefile')

    @patch('sys.frozen', True, create=True)
    @patch('sys.__compiled__', True, create=True)
    @patch('sys.executable', '/app/dist/myapp.dist/myapp')
    def test_nuitka_standalone_detection(self):
        """测试 Nuitka standalone 模式检测"""
        mode = get_nuitka_standalone_mode()
        self.assertEqual(mode, 'standalone')


class TestModuleScanning(unittest.TestCase):
    """测试模块扫描功能"""

    def test_development_scanning(self):
        """测试开发环境的模块扫描"""
        from cullinan.application import file_list_func

        # 在开发环境下应该能扫描到模块
        modules = file_list_func()
        self.assertIsInstance(modules, list)

        # 应该能扫描到 cullinan 自身的模块
        # 注意：实际扫描会过滤掉 cullinan 框架模块
        print(f"\n扫描到 {len(modules)} 个模块")
        if modules:
            print(f"示例模块: {modules[:5]}")


class TestReflectModule(unittest.TestCase):
    """测试模块反射导入功能"""

    def test_import_existing_module(self):
        """测试导入已存在的模块"""
        from cullinan.application import reflect_module

        # 导入一个标准库模块
        # 注意：reflect_module 设计为静默失败，所以我们只是确保不抛异常
        try:
            reflect_module('os', 'nobody')
            success = True
        except Exception as e:
            success = False
            print(f"导入失败: {e}")

        self.assertTrue(success)

    def test_import_nonexistent_module(self):
        """测试导入不存在的模块"""
        from cullinan.application import reflect_module

        # 导入不存在的模块应该静默失败（不抛异常）
        try:
            reflect_module('nonexistent_module_12345', 'nobody')
            success = True
        except Exception as e:
            success = False
            print(f"意外异常: {e}")

        self.assertTrue(success)


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Cullinan 打包支持测试")
    print("=" * 60)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleScanning))
    suite.addTests(loader.loadTestsFromTestCase(TestReflectModule))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    print(f"测试完成: {result.testsRun} 个测试")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

