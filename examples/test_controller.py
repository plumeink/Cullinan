# -*- coding: utf-8 -*-
"""
示例 Controller 模块

演示 Cullinan 的 Controller 基本用法
"""

from cullinan.controller import controller, get_api


@controller(url='/api')
class TestController:
    """测试控制器"""

    @get_api(url='/hello')
    def hello(self, query_params):
        """Hello World 接口"""
        return {'message': 'Hello from Cullinan!', 'status': 'ok'}

    @get_api(url='/info')
    def info(self, query_params):
        """返回环境信息"""
        import sys
        import os

        # 检测运行环境
        is_frozen = getattr(sys, 'frozen', False)
        is_nuitka = '__compiled__' in globals() or hasattr(sys, '__compiled__')
        is_pyinstaller = hasattr(sys, '_MEIPASS')

        env_info = {
            'frozen': is_frozen,
            'nuitka': is_nuitka,
            'pyinstaller': is_pyinstaller,
            'executable': sys.executable,
            'cwd': os.getcwd(),
            'python_version': sys.version,
        }

        if is_pyinstaller:
            env_info['meipass'] = getattr(sys, '_MEIPASS', None)

        return env_info

    @get_api(url='/test')
    def test(self, query_params):
        """测试接口"""
        return {
            'status': 'success',
            'message': 'Controller is working!',
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }

