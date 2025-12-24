# -*- coding: utf-8 -*-
"""
Cullinan Framework Configuration

配置框架的模块扫描行为，特别是对于打包环境
"""

import os
import sys
from typing import List, Optional

class CullinanConfig:
    """Cullinan 框架配置类"""

    def __init__(self):
        # 用户包目录列表（相对于项目根目录或绝对路径）
        # 例如: ['myapp', 'myapp.controllers', 'myapp.services']
        self.user_packages: List[str] = []

        # 项目根目录（自动检测或手动设置）
        self.project_root: Optional[str] = None

        # 是否启用详细日志
        self.verbose: bool = False

        # 是否自动扫描（如果为 False，只导入 user_packages）
        self.auto_scan: bool = True

        # 显式注册的 Service 类列表（优先级高于自动扫描）
        # 例如: [DatabaseService, CacheService]
        self.explicit_services: List = []

        # 显式注册的 Controller 类列表（优先级高于自动扫描）
        # 例如: [UserController, AdminController]
        self.explicit_controllers: List = []

        # 模块扫描黑名单（不扫描这些包）
        self.exclude_packages: List[str] = [
            # Testing
            'test', 'tests', '__pycache__', '.pytest_cache', '.tox',
            # Virtual environments
            'venv', 'env', '.venv', '.env', 'virtualenv',
            # Version control
            '.git', '.svn', '.hg',
            # IDEs
            '.vscode', '.idea', '.vs',
            # Build/Distribution
            'dist', 'build', 'eggs', '*.egg-info', 'htmlcov',
            # Documentation
            'docs', 'doc', 'site',
            # Node.js (for full-stack projects)
            'node_modules',
            # Python caches
            '__pypackages__', '.mypy_cache', '.ruff_cache',
        ]

        # 启动错误处理策略
        # 'strict': Service 初始化失败时立即退出（默认，最安全）
        # 'warn': Service 初始化失败时记录警告并继续（降级模式）
        # 'ignore': 忽略 Service 初始化失败（不推荐，仅用于调试）
        self.startup_error_policy: str = 'strict'

        # RequestContext 特性开关（v0.81+）
        # 允许用户根据需要启用或禁用 RequestContext 的特定功能
        self.context_features = {
            # 是否启用请求 ID 自动生成
            'auto_request_id': True,

            # 是否启用请求计时
            'timing': True,

            # 是否启用元数据存储
            'metadata': True,

            # 是否启用清理回调
            'cleanup_callbacks': True,

            # 是否启用调试日志
            'debug_logging': False,

            # 请求 ID 格式：'uuid'（默认）/ 'sequential' / 'custom'
            'request_id_format': 'uuid',

            # 自定义请求 ID 生成器（当 request_id_format='custom' 时使用）
            'custom_request_id_generator': None,
        }

        # ====================================================================
        # BACKWARD_COMPAT: v0.8 - 向后兼容开关
        # 此选项将在 v1.0 移除，届时将不再支持旧 API
        # ====================================================================

        # 是否启用向后兼容模式（v1.0 将默认为 False）
        # 禁用后，使用废弃的 API 将抛出错误而不是警告
        self.enable_backward_compat: bool = True

        # ====================================================================
        # END BACKWARD_COMPAT
        # ====================================================================

    def add_user_package(self, package: str):
        """添加用户包"""
        if package not in self.user_packages:
            self.user_packages.append(package)

    def set_project_root(self, root: str):
        """设置项目根目录"""
        self.project_root = os.path.abspath(root)

    def set_verbose(self, verbose: bool):
        """设置详细日志"""
        self.verbose = verbose

    def from_dict(self, config: dict):
        """从字典加载配置"""
        if 'user_packages' in config:
            self.user_packages = config['user_packages']
        if 'project_root' in config:
            self.project_root = config['project_root']
        if 'verbose' in config:
            self.verbose = config['verbose']
        if 'auto_scan' in config:
            self.auto_scan = config['auto_scan']
        if 'explicit_services' in config:
            self.explicit_services = config['explicit_services']
        if 'explicit_controllers' in config:
            self.explicit_controllers = config['explicit_controllers']
        if 'exclude_packages' in config:
            self.exclude_packages = config['exclude_packages']
        if 'startup_error_policy' in config:
            self.startup_error_policy = config['startup_error_policy']
        return self

    def to_dict(self) -> dict:
        """导出为字典"""
        return {
            'user_packages': self.user_packages,
            'project_root': self.project_root,
            'verbose': self.verbose,
            'auto_scan': self.auto_scan,
            'explicit_services': self.explicit_services,
            'explicit_controllers': self.explicit_controllers,
            'exclude_packages': self.exclude_packages,
            'startup_error_policy': self.startup_error_policy
        }


# 全局配置实例
_config = CullinanConfig()


def get_config() -> CullinanConfig:
    """获取全局配置实例"""
    return _config


def configure(
    user_packages: Optional[List[str]] = None,
    project_root: Optional[str] = None,
    verbose: bool = False,
    auto_scan: bool = True,
    explicit_services: Optional[List] = None,
    explicit_controllers: Optional[List] = None,
    exclude_packages: Optional[List[str]] = None,
    startup_error_policy: str = 'strict'
):
    """配置 Cullinan 框架

    Args:
        user_packages: 用户包列表，例如 ['myapp', 'myapp.controllers']
        project_root: 项目根目录（如果不指定，会自动推断）
        verbose: 是否启用详细日志
        auto_scan: 是否自动扫描（False 时只导入指定的包）
        explicit_services: 显式注册的 Service 类列表，例如 [DatabaseService, CacheService]
        explicit_controllers: 显式注册的 Controller 类列表，例如 [UserController, AdminController]
        exclude_packages: 排除的包名列表
        startup_error_policy: 启动错误处理策略
            - 'strict': Service 失败时立即退出（默认，最安全）
            - 'warn': Service 失败时记录警告并继续（降级模式）
            - 'ignore': 忽略失败（不推荐，仅调试用）

    Example:
        >>> from cullinan import configure
        >>> configure(
        ...     user_packages=['your_app'],
        ...     verbose=True,
        ...     startup_error_policy='warn'  # 允许部分 Service 失败
        ... )

        >>> # 使用显式注册（跳过自动扫描，提升性能）
        >>> from cullinan import configure
        >>> from myapp.services import DatabaseService, CacheService
        >>> from myapp.controllers import UserController
        >>> configure(
        ...     explicit_services=[DatabaseService, CacheService],
        ...     explicit_controllers=[UserController],
        ...     auto_scan=False  # 禁用自动扫描
        ... )
    """
    global _config

    if user_packages is not None:
        _config.user_packages = user_packages

        # 自动推断并添加项目根目录到 sys.path
        if project_root is None:
            project_root = _auto_detect_project_root(user_packages)

        if project_root and project_root not in sys.path:
            sys.path.insert(0, project_root)
            if verbose:
                print(f"Auto-added project root to sys.path: {project_root}")

    if project_root is not None:
        _config.set_project_root(project_root)

    _config.verbose = verbose
    _config.auto_scan = auto_scan

    if explicit_services is not None:
        _config.explicit_services = explicit_services

    if explicit_controllers is not None:
        _config.explicit_controllers = explicit_controllers

    if exclude_packages is not None:
        _config.exclude_packages = exclude_packages

    # 验证启动错误策略
    valid_policies = ['strict', 'warn', 'ignore']
    if startup_error_policy not in valid_policies:
        raise ValueError(
            f"Invalid startup_error_policy: {startup_error_policy}. "
            f"Must be one of: {', '.join(valid_policies)}"
        )
    _config.startup_error_policy = startup_error_policy

    return _config


def _auto_detect_project_root(user_packages: List[str]) -> Optional[str]:
    """自动检测项目根目录

    根据配置的用户包名，向上查找项目根目录
    例如：user_packages=['club.fnep'] -> 查找包含 club/fnep 的目录
    支持所有打包环境 (development/Nuitka/PyInstaller)
    """
    import inspect

    # In frozen/packaged environments, use path_utils for reliable path detection
    try:
        from cullinan.path_utils import get_base_path, is_frozen

        if is_frozen():
            # In frozen mode, return base path directly
            return str(get_base_path())
    except ImportError:
        pass  # Fallback to legacy inspection method
    except Exception:
        pass  # Handle any other errors gracefully

    # 获取调用 configure 的文件路径
    frame = inspect.currentframe()
    if frame is None:
        return None

    try:
        # 向上查找两层：configure -> caller
        caller_frame = frame.f_back
        if caller_frame and caller_frame.f_back:
            caller_frame = caller_frame.f_back

        if caller_frame is None:
            return None

        caller_file = caller_frame.f_globals.get('__file__')
        if not caller_file:
            return None

        current_dir = os.path.dirname(os.path.abspath(caller_file))

        # 如果 user_packages 包含点号分隔的包名，尝试推断根目录
        for package in user_packages:
            if '.' in package:
                # 例如 'club.fnep' -> 查找包含 'club' 的父目录
                parts = package.split('.')
                top_package = parts[0]

                # 从当前目录向上查找
                search_dir = current_dir
                for _ in range(5):  # 最多向上查找 5 级
                    # 检查是否存在 top_package 目录
                    package_path = os.path.join(search_dir, top_package)
                    if os.path.isdir(package_path):
                        # 找到了，返回这个目录
                        return search_dir

                    parent = os.path.dirname(search_dir)
                    if parent == search_dir:  # 已经到根目录
                        break
                    search_dir = parent

        # 如果没有找到，返回调用者文件的父目录的父目录
        # 这适用于 project/app/main.py 的结构
        return os.path.dirname(os.path.dirname(current_dir))

    finally:
        del frame


