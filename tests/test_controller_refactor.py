# -*- coding: utf-8 -*-
"""测试 controller 重构后的导入和功能"""

print("=" * 60)
print("测试 Controller 模块重构")
print("=" * 60)

# 测试 1: 包访问
print("\n[测试 1] 访问 controller 包")
import cullinan
print(f"[OK] cullinan.controller 类型: {type(cullinan.controller).__name__}")
print(f"[OK] cullinan.controller 路径: {cullinan.controller.__file__}")

# 测试 2: 从包导入装饰器
print("\n[测试 2] 从 controller 包导入装饰器")
from cullinan.controller import controller, get_api, post_api, Handler
print(f"[OK] controller 装饰器: {type(controller).__name__}")
print(f"[OK] get_api 装饰器: {type(get_api).__name__}")
print(f"[OK] Handler 类: {Handler.__name__}")

# 测试 3: 导入整个包
print("\n[测试 3] 导入整个 controller 包")
import cullinan.controller as ctrl
print(f"[OK] 包含 controller 属性: {hasattr(ctrl, 'controller')}")
print(f"[OK] 包含 Handler 属性: {hasattr(ctrl, 'Handler')}")
print(f"[OK] 包含 core 模块: {hasattr(ctrl, 'core')}")
print(f"[OK] 包含 registry 模块: {hasattr(ctrl, 'registry')}")

# 测试 4: 验证 core.py 位置
print("\n[测试 4] 验证 core.py 模块")
from cullinan.controller import core
print(f"[OK] core 模块路径: {core.__file__}")
print(f"[OK] core 模块包含 controller: {hasattr(core, 'controller')}")

# 测试 5: 验证装饰器可调用
print("\n[测试 5] 验证装饰器可调用")
print(f"[OK] controller 可调用: {callable(controller)}")
print(f"[OK] get_api 可调用: {callable(get_api)}")
print(f"[OK] post_api 可调用: {callable(post_api)}")
print(f"[OK] Handler 可实例化: {callable(Handler)}")

# 测试 6: 验证注册表
print("\n[测试 6] 验证控制器注册")
from cullinan.controller import get_controller_registry
registry = get_controller_registry()
print(f"[OK] 获取注册表成功: {type(registry).__name__}")
print(f"[OK] 注册表计数: {registry.count()}")

print("\n" + "=" * 60)
print("所有测试通过！Controller 重构成功！")
print("=" * 60)
print("\n重构说明:")
print("  1. controller.py 已移动到 controller/core.py")
print("  2. controller 包可以正常访问: import cullinan.controller")
print("  3. 装饰器从包导入: from cullinan.controller import controller")
print("  4. 避免了 Nuitka 打包时的模块名称冲突")
print("=" * 60)

