#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_tests.py - Cullinan 完整测试套件

运行 Cullinan 的所有单元测试，生成详细的测试报告。

使用方法:
    python tests/run_tests.py                 # 运行所有测试
    python tests/run_tests.py --verbose       # 详细输出
    python tests/run_tests.py --coverage      # 生成覆盖率报告
    python tests/run_tests.py --quick         # 快速测试（跳过耗时测试）
"""

import sys
import os
import unittest
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 颜色输出支持
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    class Fore:
        GREEN = RED = YELLOW = BLUE = CYAN = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def print_header(text):
    """打印标题"""
    if COLORS_AVAILABLE:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
        print(f"{text}")
        print(f"{'='*70}{Style.RESET_ALL}\n")
    else:
        print(f"\n{'='*70}")
        print(text)
        print(f"{'='*70}\n")


def print_success(text):
    """打印成功信息"""
    if COLORS_AVAILABLE:
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")
    else:
        print(f"✓ {text}")


def print_error(text):
    """打印错误信息"""
    if COLORS_AVAILABLE:
        print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")
    else:
        print(f"✗ {text}")


def print_warning(text):
    """打印警告信息"""
    if COLORS_AVAILABLE:
        print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")
    else:
        print(f"⚠ {text}")


def run_tests(verbose=False, quick=False):
    """运行测试套件"""
    print_header("Cullinan 单元测试套件")

    # 显示环境信息
    print(f"Python 版本: {sys.version}")
    print(f"测试目录: {Path(__file__).parent}")
    print()

    # 创建测试加载器
    loader = unittest.TestLoader()

    # 发现所有测试
    start_dir = Path(__file__).parent
    suite = loader.discover(str(start_dir), pattern='test_*.py')

    # 统计测试数量
    test_count = suite.countTestCases()
    print(f"发现 {test_count} 个测试用例\n")

    if test_count == 0:
        print_warning("没有找到测试用例！")
        return False

    # 运行测试
    print_header("开始运行测试")
    start_time = time.time()

    # 创建测试运行器
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)

    result = runner.run(suite)

    # 计算耗时
    elapsed_time = time.time() - start_time

    # 打印结果摘要
    print_header("测试结果摘要")

    print(f"总测试数: {result.testsRun}")
    print(f"耗时: {elapsed_time:.2f} 秒")
    print()

    if result.wasSuccessful():
        print_success(f"所有测试通过！({result.testsRun}/{result.testsRun})")
        return True
    else:
        print_error(f"测试失败！")
        print(f"  失败: {len(result.failures)}")
        print(f"  错误: {len(result.errors)}")
        print(f"  跳过: {len(result.skipped)}")

        # 打印失败详情
        if result.failures:
            print_header("失败的测试")
            for test, traceback in result.failures:
                print(f"\n{test}:")
                print(traceback)

        # 打印错误详情
        if result.errors:
            print_header("错误的测试")
            for test, traceback in result.errors:
                print(f"\n{test}:")
                print(traceback)

        return False


def check_coverage():
    """检查测试覆盖率"""
    try:
        import coverage
    except ImportError:
        print_warning("coverage 未安装，跳过覆盖率检查")
        print("安装方法: pip install coverage")
        return

    print_header("生成测试覆盖率报告")

    # 创建覆盖率对象
    cov = coverage.Coverage(source=['cullinan'])
    cov.start()

    # 运行测试
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'tests'
    suite = loader.discover(str(start_dir), pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=0)
    runner.run(suite)

    # 停止覆盖率收集
    cov.stop()
    cov.save()

    # 生成报告
    print()
    print("覆盖率报告:")
    print("-" * 70)
    cov.report()

    # 生成 HTML 报告
    htmlcov_dir = Path(__file__).parent / 'htmlcov'
    cov.html_report(directory=str(htmlcov_dir))
    print()
    print_success(f"HTML 报告已生成: {htmlcov_dir}/index.html")


def check_dependencies():
    """检查测试依赖"""
    print_header("检查测试依赖")

    dependencies = {
        'tornado': 'Tornado Web Framework',
        'sqlalchemy': 'SQLAlchemy ORM',
    }

    missing = []

    for module, name in dependencies.items():
        try:
            __import__(module)
            print_success(f"{name} - 已安装")
        except ImportError:
            print_error(f"{name} - 未安装")
            missing.append(module)

    optional_deps = {
        'coverage': '测试覆盖率工具',
        'colorama': '彩色输出支持',
    }

    print()
    print("可选依赖:")
    for module, name in optional_deps.items():
        try:
            __import__(module)
            print_success(f"{name} - 已安装")
        except ImportError:
            print_warning(f"{name} - 未安装（可选）")

    print()

    if missing:
        print_error(f"缺少必需依赖: {', '.join(missing)}")
        print(f"安装方法: pip install {' '.join(missing)}")
        return False

    return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Cullinan 单元测试套件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/run_tests.py                 # 运行所有测试
  python tests/run_tests.py --verbose       # 详细输出
  python tests/run_tests.py --coverage      # 生成覆盖率报告
  python tests/run_tests.py --check-deps    # 只检查依赖
        """
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )

    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='生成测试覆盖率报告'
    )

    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='快速测试（跳过耗时测试）'
    )

    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='只检查依赖，不运行测试'
    )

    args = parser.parse_args()

    # 只检查依赖
    if args.check_deps:
        success = check_dependencies()
        return 0 if success else 1

    # 检查依赖
    if not check_dependencies():
        return 1

    # 运行测试
    if args.coverage:
        check_coverage()
        return 0
    else:
        success = run_tests(verbose=args.verbose, quick=args.quick)
        return 0 if success else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)

