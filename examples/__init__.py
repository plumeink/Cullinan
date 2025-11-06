# -*- coding: utf-8 -*-
"""Examples package"""

# 导入所有示例模块，确保它们被打包工具包含
try:
    from . import test_controller
except ImportError:
    # 如果作为脚本直接运行，相对导入可能失败
    pass

