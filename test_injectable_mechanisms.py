# -*- coding: utf-8 -*-
"""
简化测试：检查 @injectable 和 InjectByName 的组合
"""

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

from cullinan.core import injectable, InjectByName, Inject, get_injection_registry

print("\n=== 测试 1: 只使用 InjectByName（不用 @injectable）===")

class Controller1:
    service = InjectByName('SomeService')

injection_registry = get_injection_registry()
print(f"Controller1 有注入需求: {injection_registry.has_injections(Controller1)}")
print(f"注入信息: {injection_registry.get_injection_info(Controller1)}")

print("\n=== 测试 2: 使用 InjectByName + @injectable ===")

@injectable
class Controller2:
    service = InjectByName('SomeService')

print(f"Controller2 有注入需求: {injection_registry.has_injections(Controller2)}")
print(f"注入信息: {injection_registry.get_injection_info(Controller2)}")

print("\n=== 测试 3: 使用 Inject + @injectable ===")

@injectable
class Controller3:
    service: 'SomeService' = Inject()

print(f"Controller3 有注入需求: {injection_registry.has_injections(Controller3)}")
print(f"注入信息: {injection_registry.get_injection_info(Controller3)}")

print("\n=== 结论 ===")
print("InjectByName 是描述符，不需要在 InjectionRegistry 中注册")
print("Inject 是标记，需要 @injectable 扫描并注册到 InjectionRegistry")

