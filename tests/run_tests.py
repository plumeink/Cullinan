# -*- coding: utf-8 -*-
"""测试运行器 - 处理 Windows 编码问题"""

import sys
import os
import subprocess

# 设置 UTF-8 编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 测试列表
tests = [
    'tests/test_injection_basic.py',
    'tests/test_complete_injection_flow.py',
    'tests/test_fallback_injection.py',
]

print("\n" + "="*70)
print("Running Cullinan Framework Tests")
print("="*70 + "\n")

results = []
for test in tests:
    test_name = os.path.basename(test)
    print(f"Running {test_name}...", end=" ")
    
    try:
        result = subprocess.run(
            [sys.executable, test],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30
        )
        
        if result.returncode == 0:
            print("[OK]")
            results.append(True)
        else:
            print("[FAIL]")
            print(f"  Error: {result.stderr[:200]}")
            results.append(False)
    except subprocess.TimeoutExpired:
        print("[TIMEOUT]")
        results.append(False)
    except Exception as e:
        print(f"[ERROR] {e}")
        results.append(False)

print("\n" + "="*70)
print(f"Test Results: {sum(results)}/{len(results)} passed")
print("="*70)

if all(results):
    print("\n[OK] All tests passed!")
    sys.exit(0)
else:
    print("\n[FAIL] Some tests failed!")
    sys.exit(1)

