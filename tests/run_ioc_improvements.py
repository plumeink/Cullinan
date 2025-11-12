# -*- coding: utf-8 -*-
"""IoC/DI 改进综合测试运行器

运行所有与 T0.1, T0.2, T0.3 相关的测试
"""

import sys
import subprocess


def run_tests():
    """运行所有 IoC 改进相关的测试"""
    
    print("="*70)
    print("Cullinan IoC/DI 改进 - 综合测试")
    print("="*70)
    print()
    
    test_files = [
        'tests/test_injection_mro.py',
        'tests/test_registry_concurrency.py',
        'tests/test_duplicate_policy.py',
    ]
    
    print("测试文件列表：")
    for i, test_file in enumerate(test_files, 1):
        print(f"  {i}. {test_file}")
    print()
    
    print("运行测试...")
    print("-"*70)
    
    # 使用 pytest 运行所有测试
    cmd = ['python', '-m', 'pytest'] + test_files + ['-v', '--tb=short']
    
    result = subprocess.run(cmd, capture_output=False)
    
    print("-"*70)
    print()
    
    if result.returncode == 0:
        print("✅ 所有测试通过！")
        print()
        print("短期目标（T0.1-T0.3）已完成：")
        print("  ✅ T0.1: MRO-aware 注入元数据查找（已验证）")
        print("  ✅ T0.2: Registry 并发安全（已加锁）")
        print("  ✅ T0.3: 可配置重复注册策略（已验证）")
        print()
        print("下一步：中期目标（T1.1-T1.3）")
        print("  ⏳ T1.1: Provider/Binding 抽象")
        print("  ⏳ T1.2: Scope 引入")
        print("  ⏳ T1.3: 完善构造器注入")
        return 0
    else:
        print("❌ 测试失败")
        print()
        print("请检查上述错误信息并修复问题")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())

