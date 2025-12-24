# -*- coding: utf-8 -*-
"""重新安装 Cullinan 到项目虚拟环境

这个脚本会：
1. 卸载虚拟环境中的旧版本
2. 安装当前项目的开发版本
3. 验证安装正确

Author: Plumeink
"""
import subprocess
import sys
import os

print("=" * 70)
print("重新安装 Cullinan 框架")
print("=" * 70)

project_root = r"G:\pj\Cullinan - 副本 (3)"
target_project = r"G:\pj\discord_bot_raven"

print(f"\n源项目: {project_root}")
print(f"目标项目: {target_project}")

# 步骤 1: 激活目标项目的虚拟环境并卸载旧版本
print("\n步骤 1: 卸载虚拟环境中的旧版本...")

venv_python = os.path.join(target_project, ".venv", "Scripts", "python.exe")
if not os.path.exists(venv_python):
    print(f"❌ 虚拟环境 Python 不存在: {venv_python}")
    sys.exit(1)

print(f"   使用 Python: {venv_python}")

try:
    result = subprocess.run(
        [venv_python, "-m", "pip", "uninstall", "cullinan", "-y"],
        capture_output=True,
        text=True,
        cwd=target_project
    )
    print(result.stdout)
    if result.returncode == 0:
        print("✅ 卸载成功")
    else:
        print("⚠️ 卸载可能失败（或已经不存在）")
        print(result.stderr)
except Exception as e:
    print(f"❌ 卸载失败: {e}")
    sys.exit(1)

# 步骤 2: 安装当前项目的开发版本
print("\n步骤 2: 安装当前项目的开发版本...")

try:
    result = subprocess.run(
        [venv_python, "-m", "pip", "install", "-e", project_root],
        capture_output=True,
        text=True,
        cwd=target_project
    )
    print(result.stdout)
    if result.returncode == 0:
        print("✅ 安装成功")
    else:
        print("❌ 安装失败")
        print(result.stderr)
        sys.exit(1)
except Exception as e:
    print(f"❌ 安装失败: {e}")
    sys.exit(1)

# 步骤 3: 验证安装
print("\n步骤 3: 验证安装...")

verify_script = """
import cullinan.controller.core
import inspect

# 检查模块位置
module_file = inspect.getsourcefile(cullinan.controller.core)
print(f"模块位置: {module_file}")

# 检查 set_fragment_method 是否有 return
source = inspect.getsource(cullinan.controller.core.EncapsulationHandler.set_fragment_method)
if 'return result' in source:
    print("✅ set_fragment_method 有 return result")
else:
    print("❌ set_fragment_method 缺少 return result")

if 'async def dummy' in source:
    print("✅ dummy 是 async def")
else:
    print("❌ dummy 不是 async def")

if 'inspect.isawaitable' in source:
    print("✅ 使用 inspect.isawaitable")
else:
    print("⚠️ 未使用 inspect.isawaitable")
"""

try:
    result = subprocess.run(
        [venv_python, "-c", verify_script],
        capture_output=True,
        text=True,
        cwd=target_project
    )
    print(result.stdout)
    if result.stderr:
        print("stderr:", result.stderr)

    if "✅ set_fragment_method 有 return result" in result.stdout:
        print("\n✅ 验证成功！修复后的代码已安装")
    else:
        print("\n❌ 验证失败！代码可能未正确安装")
        sys.exit(1)

except Exception as e:
    print(f"❌ 验证失败: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("安装完成！")
print("=" * 70)

print("\n下一步:")
print(f"1. 进入目标项目: cd {target_project}")
print("2. 重新启动你的应用")
print("3. 测试接口")
print("\n如果仍有问题，重启 Python 进程确保加载新代码")

