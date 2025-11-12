# -*- coding: utf-8 -*-
"""
Cullinan Path Utils Test Script

测试 path_utils 模块在不同环境下的功能
"""

import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_path_utils():
    """测试 path_utils 模块"""
    print("=" * 70)
    print("Cullinan Path Utils Test")
    print("=" * 70)

    try:
        # 导入 path_utils
        from cullinan import (
            is_frozen,
            is_nuitka_compiled,
            is_pyinstaller_frozen,
            get_packaging_mode,
            get_base_path,
            get_cullinan_package_path,
            get_resource_path,
            get_module_file_path,
            get_executable_dir,
            get_user_data_dir,
            get_path_info,
            log_path_info,
        )

        print("✅ Successfully imported path_utils functions\n")

        # 测试环境检测
        print("1. Environment Detection:")
        print(f"   is_frozen: {is_frozen()}")
        print(f"   is_nuitka_compiled: {is_nuitka_compiled()}")
        print(f"   is_pyinstaller_frozen: {is_pyinstaller_frozen()}")
        print(f"   packaging_mode: {get_packaging_mode()}")
        print()

        # 测试路径解析
        print("2. Path Resolution:")
        print(f"   base_path: {get_base_path()}")
        print(f"   cullinan_package_path: {get_cullinan_package_path()}")
        print(f"   executable_dir: {get_executable_dir()}")
        print(f"   user_data_dir: {get_user_data_dir()}")
        print()

        # 测试模块文件查找
        print("3. Module File Resolution:")
        controller_path = get_module_file_path('controller.py', relative_to_cullinan=True)
        if controller_path:
            print(f"   ✅ controller.py found at: {controller_path}")
            print(f"   Exists: {controller_path.exists()}")
        else:
            print(f"   [ERROR] controller.py not found")
        print()

        # 测试资源路径
        print("4. Resource Path Resolution:")
        config_path = get_resource_path('config.yaml')
        print(f"   config.yaml would be at: {config_path}")
        print()

        # 打印完整路径信息
        print("5. Full Path Information:")
        log_path_info()
        print()

        # 测试 controller 导入
        print("6. Controller Module Test:")
        try:
            from cullinan import (
                controller,
                get_api,
                post_api,
                get_controller_registry,
            )
            print("   ✅ Controller decorators imported successfully")
            print(f"   controller: {controller}")
            print(f"   get_api: {get_api}")
            print(f"   post_api: {post_api}")
            print(f"   get_controller_registry: {get_controller_registry}")
        except Exception as e:
            print(f"   [ERROR] Controller import failed: {e}")
        print()

        # 测试核心模块
        print("7. Core Module Test:")
        try:
            from cullinan import (
                Registry,
                DependencyInjector,
                Inject,
                injectable,
            )
            print("   ✅ Core module imported successfully")
            print(f"   Registry: {Registry}")
            print(f"   DependencyInjector: {DependencyInjector}")
            print(f"   Inject: {Inject}")
            print(f"   injectable: {injectable}")
        except Exception as e:
            print(f"   [ERROR] Core module import failed: {e}")
        print()

        print("=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_controller_loading():
    """测试 controller.py 加载"""
    print("\n" + "=" * 70)
    print("Controller Loading Test")
    print("=" * 70)

    try:
        # 测试从 controller package 导入
        from cullinan.controller import (
            controller,
            get_api,
            post_api,
            Handler,
            response,
        )

        print("✅ Successfully imported from cullinan.controller")
        print(f"   controller: {controller}")
        print(f"   get_api: {get_api}")
        print(f"   post_api: {post_api}")
        print(f"   Handler: {Handler}")
        print(f"   response: {response}")

        return True

    except Exception as e:
        print(f"[ERROR] Controller loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Cullinan Framework - Path Utils Test" + " " * 17 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # 运行测试
    test1_passed = test_path_utils()
    test2_passed = test_controller_loading()

    # 总结
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Path Utils Test: {'✅ PASSED' if test1_passed else '[ERROR] FAILED'}")
    print(f"Controller Loading Test: {'✅ PASSED' if test2_passed else '[ERROR] FAILED'}")
    print("=" * 70)

    if test1_passed and test2_passed:
        print("\n🎉 All tests PASSED! The packaging fix is working correctly.")
        return 0
    else:
        print("\n[ERROR] Some tests FAILED. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

