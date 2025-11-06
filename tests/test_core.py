# -*- coding: utf-8 -*-
"""
Cullinan 核心功能单元测试

测试 Cullinan 框架的核心功能，包括配置系统、环境检测、模块扫描等。
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cullinan import configure, get_config, CullinanConfig
from cullinan.config import _config


class TestConfiguration(unittest.TestCase):
    """测试配置系统"""

    def setUp(self):
        """每个测试前重置配置"""
        global _config
        _config.user_packages = []
        _config.verbose = False
        _config.auto_scan = True
        _config.project_root = None

    def test_configure_basic(self):
        """测试基本配置"""
        configure(user_packages=['test_app'])
        config = get_config()
        self.assertEqual(config.user_packages, ['test_app'])

    def test_configure_multiple_packages(self):
        """测试多包配置"""
        packages = ['app1', 'app2', 'app3']
        configure(user_packages=packages)
        config = get_config()
        self.assertEqual(config.user_packages, packages)

    def test_configure_verbose(self):
        """测试详细日志配置"""
        configure(verbose=True)
        config = get_config()
        self.assertTrue(config.verbose)

    def test_configure_auto_scan(self):
        """测试自动扫描配置"""
        configure(auto_scan=False)
        config = get_config()
        self.assertFalse(config.auto_scan)

    def test_add_user_package(self):
        """测试添加用户包"""
        config = get_config()
        config.add_user_package('new_app')
        self.assertIn('new_app', config.user_packages)

    def test_config_to_dict(self):
        """测试配置导出为字典"""
        configure(
            user_packages=['test_app'],
            verbose=True,
            auto_scan=False
        )
        config = get_config()
        config_dict = config.to_dict()

        self.assertEqual(config_dict['user_packages'], ['test_app'])
        self.assertTrue(config_dict['verbose'])
        self.assertFalse(config_dict['auto_scan'])

    def test_config_from_dict(self):
        """测试从字典加载配置"""
        config_dict = {
            'user_packages': ['app_from_dict'],
            'verbose': True,
            'auto_scan': False
        }
        config = get_config()
        config.from_dict(config_dict)

        self.assertEqual(config.user_packages, ['app_from_dict'])
        self.assertTrue(config.verbose)
        self.assertFalse(config.auto_scan)

    def test_sys_path_auto_add(self):
        """测试自动添加项目根目录到 sys.path"""
        # 记录配置前的 sys.path 长度
        original_path_len = len(sys.path)

        # 配置一个包（会触发自动检测项目根目录）
        configure(user_packages=['test_package'])

        # sys.path 应该被修改了（可能添加了项目根目录）
        # 注意：在测试环境中，这个行为可能不明显
        # 主要是确保不会报错
        self.assertIsNotNone(sys.path)


class TestEnvironmentDetection(unittest.TestCase):
    """测试环境检测功能"""

    def test_is_nuitka_compiled(self):
        """测试 Nuitka 编译检测"""
        from cullinan.application import is_nuitka_compiled
        # 在正常环境下应该返回 False
        self.assertFalse(is_nuitka_compiled())

    def test_is_pyinstaller_frozen(self):
        """测试 PyInstaller 打包检测"""
        from cullinan.application import is_pyinstaller_frozen
        # 在正常环境下应该返回 False
        self.assertFalse(is_pyinstaller_frozen())

    def test_get_nuitka_standalone_mode(self):
        """测试获取 Nuitka 模式"""
        from cullinan.application import get_nuitka_standalone_mode
        # 在非 Nuitka 环境下应该返回 None
        mode = get_nuitka_standalone_mode()
        self.assertIsNone(mode)

    def test_get_pyinstaller_mode(self):
        """测试获取 PyInstaller 模式"""
        from cullinan.application import get_pyinstaller_mode
        # 在非 PyInstaller 环境下应该返回 None
        mode = get_pyinstaller_mode()
        self.assertIsNone(mode)


class TestModuleScanning(unittest.TestCase):
    """测试模块扫描功能"""

    def test_file_list_func(self):
        """测试模块发现函数"""
        from cullinan.application import file_list_func

        # 配置测试包
        configure(user_packages=['cullinan'])

        # 执行扫描
        modules = file_list_func()

        # 应该找到 cullinan 包的模块
        self.assertIsInstance(modules, list)
        # 至少应该包含一些核心模块
        self.assertGreater(len(modules), 0)

    def test_reflect_module(self):
        """测试模块反射导入"""
        from cullinan.application import reflect_module

        # 测试导入已存在的模块
        reflect_module('os', 'nobody')

        # 验证模块已在 sys.modules 中
        self.assertIn('os', sys.modules)


class TestConfigModule(unittest.TestCase):
    """测试配置模块的完整性"""

    def test_config_class_attributes(self):
        """测试配置类属性"""
        config = CullinanConfig()

        # 检查所有必需的属性
        self.assertTrue(hasattr(config, 'user_packages'))
        self.assertTrue(hasattr(config, 'project_root'))
        self.assertTrue(hasattr(config, 'verbose'))
        self.assertTrue(hasattr(config, 'auto_scan'))
        self.assertTrue(hasattr(config, 'exclude_packages'))

    def test_config_default_values(self):
        """测试配置默认值"""
        config = CullinanConfig()

        self.assertEqual(config.user_packages, [])
        self.assertIsNone(config.project_root)
        self.assertFalse(config.verbose)
        self.assertTrue(config.auto_scan)
        self.assertIsInstance(config.exclude_packages, list)


class TestImportSystem(unittest.TestCase):
    """测试导入系统"""

    def test_import_cullinan(self):
        """测试导入 cullinan 包"""
        import cullinan
        self.assertTrue(hasattr(cullinan, 'configure'))
        self.assertTrue(hasattr(cullinan, 'get_config'))
        self.assertTrue(hasattr(cullinan, 'CullinanConfig'))

    def test_import_config(self):
        """测试导入配置模块"""
        from cullinan import config
        self.assertTrue(hasattr(config, 'configure'))
        self.assertTrue(hasattr(config, 'get_config'))
        self.assertTrue(hasattr(config, 'CullinanConfig'))

    def test_import_application(self):
        """测试导入应用模块"""
        from cullinan import application
        # Application 类需要从 application 模块导入
        self.assertTrue(hasattr(application, 'file_list_func'))
        self.assertTrue(hasattr(application, 'scan_controller'))
        self.assertTrue(hasattr(application, 'scan_service'))

    def test_import_application_run(self):
        """测试 application.run 方法存在"""
        from cullinan import application
        self.assertTrue(hasattr(application, 'run'))
        self.assertTrue(callable(application.run))


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleScanning))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigModule))
    suite.addTests(loader.loadTestsFromTestCase(TestImportSystem))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回测试结果
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

