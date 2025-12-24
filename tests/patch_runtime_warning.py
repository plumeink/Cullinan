# -*- coding: utf-8 -*-
"""快速修补脚本：修复 cullinan RuntimeWarning "coroutine was never awaited"

作者：Plumeink
日期：2025-12-24

用途：直接修补已安装的 cullinan 包，无需重装
"""

import os
import sys
import shutil
from pathlib import Path

def find_cullinan_core():
    """查找已安装的 cullinan/controller/core.py"""
    try:
        import cullinan
        cullinan_path = Path(cullinan.__file__).parent
        core_file = cullinan_path / 'controller' / 'core.py'

        if core_file.exists():
            return core_file
        else:
            print(f"❌ 找不到 core.py: {core_file}")
            return None
    except ImportError:
        print("❌ cullinan 未安装")
        return None

def backup_file(file_path):
    """备份原文件"""
    backup_path = str(file_path) + '.backup'
    shutil.copy2(file_path, backup_path)
    print(f"✅ 已备份: {backup_path}")
    return backup_path

def patch_core_file(core_file):
    """修补 core.py 文件"""
    print(f"\n修补文件: {core_file}")

    # 读取原文件
    with open(core_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已修复
    if 'if inspect.iscoroutine(result):' in content and 'async def async_wrapper' in content:
        print("✅ 文件已经是修复后的版本，无需修补")
        return True

    # 查找需要替换的代码块
    old_pattern = """    @classmethod
    def set_fragment_method(cls, cls_obj: Any, func: Callable[[object, tuple, dict], None]):
        # Check if the function is a coroutine function (async def)
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def dummy(self, *args, **kwargs):
                return await func(self, *args, **kwargs)
        else:
            @functools.wraps(func)
            def dummy(self, *args, **kwargs):
                return func(self, *args, **kwargs)

        setattr(cls_obj, func.__name__, dummy)"""

    new_pattern = """    @classmethod
    def set_fragment_method(cls, cls_obj: Any, func: Callable[[object, tuple, dict], None]):
        # CRITICAL FIX: The wrapper functions from @get_api/@post_api are async,
        # but when called synchronously they return unawaited coroutines.
        # We must ensure the dummy wrapper is also async and properly awaits.
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def dummy(self, *args, **kwargs):
                return await func(self, *args, **kwargs)
            setattr(cls_obj, func.__name__, dummy)
        else:
            # For truly synchronous functions, check if calling returns a coroutine
            # (defensive: handle edge case where func looks sync but returns coroutine)
            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                result = func(self, *args, **kwargs)
                # If result is a coroutine, await it
                if inspect.iscoroutine(result):
                    return await result
                return result
            
            # Tornado handles async wrappers properly
            setattr(cls_obj, func.__name__, async_wrapper)"""

    if old_pattern in content:
        # 备份
        backup_path = backup_file(core_file)

        # 替换
        new_content = content.replace(old_pattern, new_pattern)

        # 写回
        with open(core_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ 修补成功！")
        print(f"   备份文件: {backup_path}")
        print(f"   如需还原，运行: copy \"{backup_path}\" \"{core_file}\"")
        return True
    else:
        print("❌ 未找到匹配的代码模式")
        print("   可能版本不匹配，建议手动修改或重装框架")
        return False

def main():
    print("=" * 80)
    print("Cullinan RuntimeWarning 修补工具")
    print("=" * 80)

    # 查找文件
    core_file = find_cullinan_core()
    if not core_file:
        print("\n❌ 无法定位 cullinan 安装位置")
        print("   建议：pip uninstall cullinan && pip install -e .")
        return 1

    print(f"\n找到 cullinan: {core_file}")

    # 修补
    if patch_core_file(core_file):
        print("\n" + "=" * 80)
        print("✅ 修补完成！")
        print("=" * 80)
        print("\n下一步:")
        print("1. 重启你的应用")
        print("2. 检查是否还有 RuntimeWarning")
        print("3. 测试 POST 接口是否返回正确数据")
        print("\n如果问题解决，建议从源码重新安装:")
        print("  pip uninstall cullinan")
        print("  pip install -e G:\\pj\\Cullinan - 副本 (3)")
        return 0
    else:
        print("\n❌ 修补失败")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

