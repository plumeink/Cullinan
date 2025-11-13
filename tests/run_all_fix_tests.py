# -*- coding: utf-8 -*-
"""
综合测试运行器 - 验证所有 IoC/DI 修复

运行所有修复的测试并生成报告。
"""

import sys
import os
import time
import subprocess

project_path = r'G:\pj\Cullinan'
if project_path not in sys.path:
    sys.path.insert(0, project_path)


def run_test_file(test_file, description):
    """运行单个测试文件"""
    print(f"\n{'='*70}")
    print(f"运行: {description}")
    print(f"文件: {test_file}")
    print('='*70)

    start_time = time.time()

    try:
        # 直接导入并运行测试
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        elapsed = time.time() - start_time

        # 打印输出
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        success = result.returncode == 0

        print(f"\n{'[OK]' if success else '[FAIL]'} 完成于 {elapsed:.2f}秒")

        return {
            'name': description,
            'file': test_file,
            'success': success,
            'elapsed': elapsed,
            'returncode': result.returncode
        }

    except subprocess.TimeoutExpired:
        print(f"\n[FAIL] 测试超时 (>30秒)")
        return {
            'name': description,
            'file': test_file,
            'success': False,
            'elapsed': 30.0,
            'returncode': -1,
            'error': 'Timeout'
        }
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        return {
            'name': description,
            'file': test_file,
            'success': False,
            'elapsed': time.time() - start_time,
            'returncode': -2,
            'error': str(e)
        }


def main():
    """主测试运行器"""
    print("=" * 70)
    print("Cullinan Core IoC/DI 修复 - 综合测试套件")
    print("=" * 70)
    print(f"Python: {sys.version}")
    print(f"项目路径: {project_path}")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试列表
    tests = [
        ('tests/simple_verify.py', '修复 #01: 快速验证（MRO查找）'),
        ('tests/test_threading_safety.py', '修复 #02: 线程安全测试'),
        ('tests/test_duplicate_policy.py', '修复 #03: 重复注册策略测试'),
        ('tests/test_circular_dependency.py', '修复 #04: 循环依赖检测测试'),
    ]

    results = []

    # 运行所有测试
    for test_file, description in tests:
        full_path = os.path.join(project_path, test_file)
        if os.path.exists(full_path):
            result = run_test_file(full_path, description)
            results.append(result)
        else:
            print(f"\n[FAIL] 测试文件不存在: {test_file}")
            results.append({
                'name': description,
                'file': test_file,
                'success': False,
                'elapsed': 0,
                'error': 'File not found'
            })

    # 生成报告
    print("\n" + "=" * 70)
    print("测试报告总结")
    print("=" * 70)

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - passed_tests
    total_time = sum(r['elapsed'] for r in results)

    print(f"\n总测试数: {total_tests}")
    print(f"通过: {passed_tests} [OK]")
    print(f"失败: {failed_tests} [FAIL]")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"成功率: {(passed_tests/total_tests*100):.1f}%")

    print("\n详细结果:")
    print("-" * 70)
    for i, result in enumerate(results, 1):
        status = "[OK] 通过" if result['success'] else "[FAIL] 失败"
        print(f"{i}. {result['name']}")
        print(f"   状态: {status}")
        print(f"   耗时: {result['elapsed']:.2f}秒")
        if 'error' in result:
            print(f"   错误: {result['error']}")
        print()

    print("=" * 70)

    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！所有修复已验证成功。")
        print("\n第一阶段修复完成情况:")
        print("  ✅ 修复 #01: 子类注入元数据 MRO 查找")
        print("  ✅ 修复 #02: 注册表线程安全（加锁）")
        print("  ✅ 修复 #03: 重复注册处理策略")
        print("  ✅ 修复 #04: 循环依赖检测")
        print("\n下一步: 开始第二阶段修复（#05-#07）")
        return 0
    else:
        print(f"\n[WARN]️  {failed_tests} 个测试失败，需要检查。")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

