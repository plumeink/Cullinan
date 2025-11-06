# -*- coding: utf-8 -*-
"""
Hello World - Simplest Cullinan Application / 最简单的 Cullinan 应用

This is a minimal Cullinan application example demonstrating basic usage.
这是一个最小化的 Cullinan 应用示例，演示基本用法。

Install Cullinan / 安装 Cullinan:
    # From source (development version) / 从源码安装（开发版）
    pip install -e /path/to/Cullinan

    # Or after PyPI release / 或等待 PyPI 发布后
    pip install cullinan

Run / 运行方法:
    python hello_world.py

    # With Chinese output / 使用中文输出:
    # Windows: set CULLINAN_LANG=zh && python hello_world.py
    # Linux/Mac: CULLINAN_LANG=zh python hello_world.py

Visit / 访问:
    http://localhost:8080/api/hello
    http://localhost:8080/api/greet?name=YourName
"""

import os
from cullinan import configure, application
from cullinan.controller import controller, get_api

# Configure Cullinan / 配置 Cullinan（打包时需要）
configure(user_packages=['__main__'])

# Language selection / 语言选择
LANG = os.getenv('CULLINAN_LANG', 'en')  # Default: en, Options: en, zh

MESSAGES = {
    'en': {
        'banner': 'Cullinan Hello World Application',
        'starting': 'Starting server on http://localhost:8080',
        'endpoints': 'Try these endpoints:',
        'stop': 'Press Ctrl+C to stop',
        'hello': 'Hello, Cullinan!',
        'greet': 'Hello, {}!'
    },
    'zh': {
        'banner': 'Cullinan Hello World 应用',
        'starting': '正在启动服务器：http://localhost:8080',
        'endpoints': '尝试以下端点：',
        'stop': '按 Ctrl+C 停止',
        'hello': '你好，Cullinan！',
        'greet': '你好，{}！'
    }
}

def _(key, *args):
    """Get localized message / 获取本地化消息"""
    msg = MESSAGES.get(LANG, MESSAGES['en']).get(key, key)
    return msg.format(*args) if args else msg


@controller(url='/api')
class HelloController:
    """Simple Hello World Controller / 简单的 Hello World 控制器"""

    @get_api(url='/hello')
    def hello(self, query_params):
        """Return welcome message / 返回欢迎消息"""
        return {'message': _('hello')}

    @get_api(url='/greet', query_params=['name'])
    def greet(self, query_params):
        """Personalized greeting / 个性化问候"""
        name = query_params.get('name', 'World')
        return {'message': _('greet', name)}


def main():
    """Application entry point / 应用入口"""
    print("="*60)
    print(_('banner'))
    print("="*60)
    print()
    print(_('starting'))
    print()
    print(_('endpoints'))
    print("  - http://localhost:8080/api/hello")
    print("  - http://localhost:8080/api/greet?name=YourName")
    print()
    print(_('stop'))
    print("="*60)
    print()

    application.run()


if __name__ == '__main__':
    main()

