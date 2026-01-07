# -*- coding: utf-8 -*-
"""
Cullinan 框架测试运行器

Author: Plumeink

运行所有依赖注入相关测试：
1. test_di_fix.py - 基础修复验证
2. test_comprehensive_di.py - 全方位测试
3. test_botcontroller_regression.py - 专项回归测试
"""

import sys
import subprocess
import os

sys.path.insert(0, '.')


def run_test(test_file: str, description: str) -> bool:
    """运行单个测试文件"""
    print(f"\n{'=' * 70}")
    print(f"运行: {description}")
    print(f"文件: {test_file}")
    print('=' * 70)

    result = subprocess.run(
        [sys.executable, test_file],
        cwd=os.path.dirname(os.path.abspath(__file__)) + '/..',
        capture_output=False
    )

    return result.returncode == 0


def main():
    """运行所有测试"""
    print("=" * 70)
    print("Cullinan 框架依赖注入测试套件")
    print("Author: Plumeink")
    print("=" * 70)

    tests = [
        ("tests/test_di_fix.py", "基础修复验证"),
        ("tests/test_comprehensive_di.py", "全方位测试套件"),
        ("tests/test_botcontroller_regression.py", "BotController 专项回归测试"),
    ]

    results = []

    for test_file, description in tests:
        success = run_test(test_file, description)
        results.append((description, success))

    # 总结
    print("\n" + "=" * 70)
    print("所有测试执行完成")
    print("=" * 70)

    all_passed = True
    for description, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {description}")
        if not success:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("结果: 全部通过")
    else:
        print("结果: 存在失败的测试")

    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

