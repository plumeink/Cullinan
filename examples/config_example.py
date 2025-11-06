# -*- coding: utf-8 -*-
"""
使用配置文件的示例

展示如何使用 Cullinan 配置来精确指定用户包
"""

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s: %(message)s'
)

# ============================================================
# 方式 1: 代码配置（推荐）
# ============================================================

from cullinan import configure

# 在创建 Application 之前配置
configure(
    user_packages=['your_app'],  # 指定你的包
    verbose=True,                 # 启用详细日志
    auto_scan=False               # 禁用自动扫描，只使用配置的包
)

# ============================================================
# 方式 2: JSON 配置文件
# ============================================================

import json
from cullinan import get_config

# 加载配置文件
with open('cullinan.json', 'r') as f:
    config_data = json.load(f)
    get_config().from_dict(config_data)

# ============================================================
# 方式 3: 环境变量
# ============================================================

import os

if os.getenv('CULLINAN_USER_PACKAGES'):
    packages = os.getenv('CULLINAN_USER_PACKAGES').split(',')
    configure(user_packages=packages)

# ============================================================
# 创建应用（配置在此之前完成）
# ============================================================

from cullinan import Application

def main():
    print("=" * 60)
    print("Cullinan with Configuration")
    print("=" * 60)

    # 显示配置
    config = get_config()
    print(f"User packages: {config.user_packages}")
    print(f"Auto scan: {config.auto_scan}")
    print(f"Verbose: {config.verbose}")
    print("=" * 60)
    print()

    # 创建应用
    app = Application()

    # 验证 Controller 注册
    from cullinan.controller import handler_list
    print(f"Registered handlers: {len(handler_list)}")
    for handler in handler_list[:5]:
        print(f"  - {handler[0]}")
    if len(handler_list) > 5:
        print(f"  ... and {len(handler_list) - 5} more")
    print()

    print("Starting application...")
    app.run()

if __name__ == '__main__':
    main()

