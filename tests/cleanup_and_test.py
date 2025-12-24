# -*- coding: utf-8 -*-
"""自动清理缓存并重新测试

Author: Plumeink
"""
import os
import shutil
import subprocess
import sys

print("=" * 70)
print("Cullinan 框架 - 缓存清理和测试工具")
print("=" * 70)

project_root = r"G:\pj\Cullinan - 副本 (3)"
os.chdir(project_root)

print(f"\n当前目录: {os.getcwd()}")

# 步骤 1: 清理 __pycache__ 和 .pyc 文件
print("\n步骤 1: 清理 Python 缓存...")
count_pycache = 0
count_pyc = 0

for root, dirs, files in os.walk(project_root):
    # 删除 __pycache__ 目录
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        try:
            shutil.rmtree(pycache_path)
            count_pycache += 1
            print(f"   删除: {pycache_path}")
        except Exception as e:
            print(f"   警告: 无法删除 {pycache_path}: {e}")

    # 删除 .pyc 文件
    for file in files:
        if file.endswith('.pyc'):
            pyc_path = os.path.join(root, file)
            try:
                os.remove(pyc_path)
                count_pyc += 1
                print(f"   删除: {pyc_path}")
            except Exception as e:
                print(f"   警告: 无法删除 {pyc_path}: {e}")

print(f"\n✅ 删除了 {count_pycache} 个 __pycache__ 目录")
print(f"✅ 删除了 {count_pyc} 个 .pyc 文件")

# 步骤 2: 删除 egg-info
print("\n步骤 2: 清理 egg-info...")
egg_info = os.path.join(project_root, "cullinan.egg-info")
if os.path.exists(egg_info):
    try:
        shutil.rmtree(egg_info)
        print(f"✅ 删除: {egg_info}")
    except Exception as e:
        print(f"⚠️ 警告: {e}")
else:
    print("   (不存在)")

# 步骤 3: 验证核心文件
print("\n步骤 3: 验证核心文件...")
core_file = os.path.join(project_root, "cullinan", "controller", "core.py")
if os.path.exists(core_file):
    print(f"✅ 找到: {core_file}")

    # 检查关键代码
    with open(core_file, 'r', encoding='utf-8') as f:
        content = f.read()

        checks = [
            ("set_fragment_method 有 return result", "return result" in content[content.find("def set_fragment_method"):content.find("def set_fragment_method") + 1000]),
            ("request_handler 有 self.finish()", "self.finish()" in content),
            ("request_handler 有 self.write", "self.write(resp_obj.get_body())" in content),
            ("使用 inspect.isawaitable", "inspect.isawaitable(" in content),
        ]

        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"   {status} {check_name}")
else:
    print(f"❌ 未找到: {core_file}")
    sys.exit(1)

# 步骤 4: 重新编译
print("\n步骤 4: 重新编译 core.py...")
try:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", core_file],
        capture_output=True,
        text=True,
        check=True
    )
    print("✅ 编译成功")
except subprocess.CalledProcessError as e:
    print(f"❌ 编译失败:")
    print(e.stderr)
    sys.exit(1)

# 步骤 5: 验证导入
print("\n步骤 5: 验证模块导入...")
try:
    import cullinan.controller.core as core_module
    import inspect

    source_file = inspect.getsourcefile(core_module)
    print(f"✅ 导入成功")
    print(f"   模块位置: {source_file}")

    if project_root in source_file:
        print(f"✅ 使用的是当前项目的代码")
    else:
        print(f"⚠️ 警告: 使用的不是当前项目的代码！")
        print(f"   预期路径包含: {project_root}")
        print(f"   实际路径: {source_file}")

except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 步骤 6: 运行快速测试
print("\n步骤 6: 运行快速集成测试...")
print("   (这将启动一个测试服务器并发送请求)")

try:
    # 运行测试脚本
    test_script = os.path.join(project_root, "diagnose_empty_response_detailed.py")
    if os.path.exists(test_script):
        print(f"   运行: {test_script}")
        result = subprocess.run(
            [sys.executable, "-B", test_script],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr

        # 检查关键输出
        if "🔥 handle_test 方法被调用" in output:
            print("   ✅ Controller 方法被调用")
        else:
            print("   ❌ Controller 方法未被调用")

        if "✅ 响应体:" in output and "executed" in output:
            print("   ✅ 响应正常返回")
        else:
            print("   ❌ 响应异常")

        if "❌ 响应体为空" in output:
            print("   ❌ 响应体为空！")
        else:
            print("   ✅ 响应体不为空")

        # 显示关键输出
        for line in output.split('\n'):
            if '🔥' in line or '✅' in line or '❌' in line:
                print(f"      {line}")

    else:
        print(f"   ⚠️ 测试脚本不存在: {test_script}")

except subprocess.TimeoutExpired:
    print("   ⚠️ 测试超时（这是正常的，服务器可能还在运行）")
except Exception as e:
    print(f"   ⚠️ 测试执行出错: {e}")

print("\n" + "=" * 70)
print("清理和验证完成！")
print("=" * 70)

print("\n📝 下一步:")
print("1. 重新启动你的应用:")
print("   python -B your_app.py")
print("")
print("2. 发送测试请求:")
print('   curl -X POST http://localhost:4080/api/webhook \\')
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"test": "data"}\'')
print("")
print("3. 观察输出中是否有:")
print("   - '🔥 方法被调用' 消息")
print("   - 非空的响应体")

