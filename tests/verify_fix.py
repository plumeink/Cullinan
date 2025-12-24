# -*- coding: utf-8 -*-
"""验证 set_fragment_method 是否正确修复

Author: Plumeink
"""
import os
import re

print("=" * 70)
print("验证 set_fragment_method 修复")
print("=" * 70)

core_file = r"/cullinan/controller/core.py"

if not os.path.exists(core_file):
    print(f"❌ 文件不存在: {core_file}")
    exit(1)

print(f"\n检查文件: {core_file}")

with open(core_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 set_fragment_method 方法
match = re.search(r'def set_fragment_method\(.*?\n(.*?)(?=\n    @|\n    def |\nclass )', content, re.DOTALL)

if not match:
    print("❌ 找不到 set_fragment_method 方法")
    exit(1)

method_code = match.group(1)
print("\n找到 set_fragment_method 方法")
print("-" * 70)
print(method_code[:500] + "..." if len(method_code) > 500 else method_code)
print("-" * 70)

# 检查关键要素
checks = {
    "async def dummy": "async def dummy" in method_code,
    "result = func": "result = func(" in method_code,
    "inspect.isawaitable(result)": "inspect.isawaitable(result)" in method_code or "inspect.iscoroutine(result)" in method_code,
    "await result": "await result" in method_code,
    "return result": "return result" in method_code,
}

print("\n检查结果:")
print("-" * 70)

all_passed = True
for check_name, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")
    if not passed:
        all_passed = False

print("-" * 70)

if all_passed:
    print("\n✅ 所有检查通过！代码修复正确！")
    print("\n修复要点:")
    print("  1. dummy 是 async def")
    print("  2. 保存了 func() 的返回值")
    print("  3. 检查并 await 了可等待对象")
    print("  4. 返回了结果 (return result)")
else:
    print("\n❌ 代码修复不完整！")
    print("\n缺少的要素:")
    for check_name, passed in checks.items():
        if not passed:
            print(f"  - {check_name}")

    print("\n需要确保 set_fragment_method 包含以下代码:")
    print("""
    @functools.wraps(func)
    async def dummy(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result  # ← 必须有这一行！
    """)

print("\n" + "=" * 70)

# 检查具体的行
if "return result" in method_code:
    # 找到 return result 所在的行号
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'def set_fragment_method' in line:
            start_line = i
        if 'return result' in line and i > start_line:
            print(f"\n✅ 找到 'return result' 在第 {i} 行")
            print(f"   上下文:")
            for j in range(max(0, i-3), min(len(lines), i+2)):
                prefix = ">>> " if j == i-1 else "    "
                print(f"   {prefix}{lines[j]}")
            break

if all_passed:
    print("\n✅ 代码验证完成！")
    print("\n如果应用仍然报错，可能是因为:")
    print("  1. Python 使用了缓存的 .pyc 文件")
    print("  2. 应用使用的是安装在其他位置的旧版本")
    print("\n解决方案:")
    print("  1. 清理缓存: 删除所有 __pycache__ 目录")
    print("  2. 重新安装: pip uninstall cullinan && pip install -e .")
    print("  3. 重启应用: 完全停止并重新启动")
else:
    print("\n❌ 请修复代码后再次运行此脚本")

