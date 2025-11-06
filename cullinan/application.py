# -*- coding: utf-8 -*-
import importlib
import inspect
import os
import pkgutil
import importlib.util
import logging
import signal

import tornado.ioloop
from cullinan.controller import handler_list, header_list
from dotenv import load_dotenv
from pathlib import Path
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpserver
from tornado.options import define, options
import sys
from cullinan.exceptions import CallerPackageException

# Module-level logger (FastAPI-style)
logger = logging.getLogger(__name__)


def is_pyinstaller_frozen():
    """检测是否为 PyInstaller 打包环境"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def is_nuitka_compiled():
    """检测是否为 Nuitka 编译环境"""
    # Nuitka 在编译时会设置 __compiled__ 属性
    return '__compiled__' in globals() or hasattr(sys, '__compiled__')


def get_nuitka_standalone_mode():
    """检测 Nuitka 的打包模式
    返回: 'onefile', 'standalone', 或 None
    """
    if not is_nuitka_compiled():
        return None

    # Nuitka onefile 模式特征
    # 1. sys.frozen 为 True
    # 2. 可执行文件会解压到临时目录
    if getattr(sys, 'frozen', False):
        # 检查是否存在 .dist 目录（standalone 特征）
        exe_dir = os.path.dirname(sys.executable)
        # onefile 模式通常在临时目录运行，路径包含随机字符
        if 'onefile' in exe_dir.lower() or 'temp' in exe_dir.lower() or '_MEI' in exe_dir:
            return 'onefile'
        return 'standalone'

    return None


def get_pyinstaller_mode():
    """检测 PyInstaller 的打包模式
    返回: 'onefile', 'onedir', 或 None
    """
    if not is_pyinstaller_frozen():
        return None

    # PyInstaller onefile 模式会设置 sys._MEIPASS
    if hasattr(sys, '_MEIPASS'):
        # 检查 _MEIPASS 是否在临时目录（onefile 特征）
        meipass = sys._MEIPASS
        if '_MEI' in meipass or 'Temp' in meipass or 'tmp' in meipass:
            return 'onefile'
        return 'onedir'

    return None


def get_caller_package():
    """Return a best-effort caller package name for the importing application.

    We walk the stack and pick the first frame whose module is not part of the
    `cullinan` package. Prefer module.__package__ if available, otherwise
    derive a dotted package name from the filename relative to the current
    working directory.
    """
    stack = inspect.stack()
    cwd = os.getcwd()
    for frame_info in stack:
        module = inspect.getmodule(frame_info[0])
        if not module:
            continue
        mod_name = getattr(module, '__name__', '')
        if mod_name and mod_name.startswith('cullinan'):
            continue
        pkg = getattr(module, '__package__', None)
        if pkg:
            # return top-level package
            return pkg.split('.')[0]
        # derive from filename
        try:
            rel = os.path.relpath(frame_info.filename, cwd)
            pkg_from_path = os.path.dirname(rel).replace(os.sep, '.')
            if pkg_from_path == '.':
                pkg_from_path = ''
            return pkg_from_path
        except Exception:
            continue
    raise CallerPackageException()


def scan_modules_nuitka():
    """Nuitka 打包后的模块扫描逻辑

    优先使用配置的 user_packages，精确扫描用户代码
    """
    logger.info("\t|||\t\t\tDetected Nuitka compiled environment")

    mode = get_nuitka_standalone_mode()
    logger.info("\t|||\t\t\tNuitka mode: %s", mode or "unknown")

    modules = []

    # 获取配置
    from cullinan.config import get_config
    config = get_config()

    # 策略1: 使用配置的用户包（推荐方式）
    if config.user_packages:
        logger.info("\t|||\t\t\tUsing configured user packages: %s", config.user_packages)

        for package_name in config.user_packages:
            try:
                # 先尝试导入包
                pkg = importlib.import_module(package_name)
                logger.debug("\t|||\t\t\tImported package: %s", package_name)

                # 添加包本身
                if package_name not in modules:
                    modules.append(package_name)

                # 扫描包下的所有子模块
                if hasattr(pkg, '__path__'):
                    # 使用 pkgutil 扫描子模块
                    for finder, name, is_pkg in pkgutil.walk_packages(pkg.__path__, package_name + '.'):
                        if name not in modules:
                            modules.append(name)
                            logger.debug("\t|||\t\t\tFound submodule: %s", name)

            except Exception as e:
                logger.warning("\t|||\t\t\tFailed to import package %s: %s", package_name, str(e))

                # 回退：尝试从 sys.modules 中查找该包的模块
                for mod_name in sys.modules.keys():
                    if mod_name.startswith(package_name):
                        if mod_name not in modules:
                            modules.append(mod_name)

        logger.info("\t|||\t\t\tFound %d modules from configured packages", len(modules))

        # 如果配置了包且找到了模块，直接返回，不再执行后续逻辑
        if modules:
            return modules

    # 策略2: 如果没有配置或配置的包没找到模块，使用智能检测
    if config.auto_scan:
        logger.info("\t|||\t\t\tNo user packages configured or no modules found, using smart detection")
        logger.debug("\t|||\t\t\tScanning sys.modules (total: %d)", len(sys.modules))

        # 使用更专业的方式：检查模块是否来自用户代码
        def is_user_module(mod_name: str, mod) -> bool:
            """判断是否为用户模块（而非标准库或第三方库）"""
            # 排除框架自身
            if mod_name.startswith('cullinan'):
                return False

            # 排除内置模块
            if mod_name.startswith('_'):
                return False

            # 排除明显的顶层标准库模块（没有点号的）
            # 用户模块通常是包结构，如 myapp.controllers
            if '.' not in mod_name:
                # 但保留一些可能的用户顶层包
                # 通过检查 __file__ 来判断
                pass

            # 检查模块文件路径
            mod_file = getattr(mod, '__file__', None)
            if not mod_file:
                return False

            # 排除 site-packages 中的第三方库
            if 'site-packages' in mod_file:
                return False

            # 排除标准库（通常在 lib/python3.x/ 下）
            if 'lib' + os.sep + 'python' in mod_file:
                return False

            # 排除打包工具自身的模块
            if 'nuitka' in mod_file.lower() or 'pyinstaller' in mod_file.lower():
                return False

            # 排除常见的系统路径
            system_paths = [
                os.path.join(sys.prefix, 'lib'),
                os.path.join(sys.prefix, 'Lib'),  # Windows
            ]
            for sys_path in system_paths:
                if mod_file.startswith(sys_path):
                    return False

            return True

        for mod_name in list(sys.modules.keys()):
            mod = sys.modules.get(mod_name)
            if mod and is_user_module(mod_name, mod):
                logger.debug("\t|||\t\t\tFound potential user module: %s", mod_name)
                modules.append(mod_name)

        logger.info("\t|||\t\t\tFound %d user modules in sys.modules", len(modules))

    # 策略3: 尝试从 __main__ 推断用户包名并强制导入
    # 这对于 Nuitka 打包后的情况特别重要
    if '__main__' in sys.modules and len(modules) == 0:
        main_mod = sys.modules['__main__']
        main_file = getattr(main_mod, '__file__', None)

        if main_file:
            # 从主文件路径推断包名
            # 例如: .../your_app/application.py -> your_app
            main_file_abs = os.path.abspath(main_file)
            logger.debug("\t|||\t\t\t__main__ file: %s", main_file_abs)

            # 尝试找到包的根目录
            current_dir = os.path.dirname(main_file_abs)
            package_parts = []

            # 向上查找，直到没有 __init__.py
            while os.path.exists(os.path.join(current_dir, '__init__.py')):
                package_parts.insert(0, os.path.basename(current_dir))
                current_dir = os.path.dirname(current_dir)

            if package_parts:
                # 构建包名
                package_name = '.'.join(package_parts)
                logger.info("\t|||\t\t\tInferred package from __main__: %s", package_name)

                # 尝试扫描这个包的所有子模块
                try:
                    # 尝试导入包
                    pkg = importlib.import_module(package_name)
                    logger.debug("\t|||\t\t\tSuccessfully imported package: %s", package_name)

                    # 扫描包中的所有模块
                    if hasattr(pkg, '__path__'):
                        for finder, name, is_pkg in pkgutil.walk_packages(pkg.__path__, package_name + '.'):
                            if name not in modules:
                                modules.append(name)
                                logger.debug("\t|||\t\t\tFound submodule: %s", name)

                    # 也添加包本身
                    if package_name not in modules:
                        modules.append(package_name)

                    logger.info("\t|||\t\t\tAdded %d modules from inferred package", len(modules))
                except Exception as e:
                    logger.warning("\t|||\t\t\tFailed to import inferred package %s: %s", package_name, str(e))

    # 特别处理：确保 __main__ 模块也被包含（controller 可能定义在主文件中）
    if '__main__' in sys.modules and '__main__' not in modules:
        main_mod = sys.modules['__main__']
        if hasattr(main_mod, '__file__'):
            logger.info("\t|||\t\t\tAdding __main__ module for scanning")
            modules.insert(0, '__main__')  # 优先处理主模块

    # 策略2: 尝试从可执行文件目录扫描 Python 文件
    # 对于 Nuitka standalone 模式，编译后的文件会在特定目录
    if len(modules) <= 1:  # 只有 __main__ 或者没有模块
        exe_dir = os.path.dirname(sys.executable)
        logger.info("\t|||\t\t\tScanning Nuitka directory for Python modules: %s", exe_dir)

        scanned_modules = []

        # 遍历目录查找 Python 相关文件
        for root, dirs, files in os.walk(exe_dir):
            # 排除系统目录
            dirs[:] = [d for d in dirs if not d.startswith('_') and d not in ['lib', 'bin', 'Lib']]

            # 检查是否是 Python 包（有 __init__.py 或 __init__.pyc）
            is_package = any(f in files for f in ['__init__.py', '__init__.pyc', '__init__.pyi'])

            if is_package or any(f.endswith(('.py', '.pyc', '.pyd', '.so')) for f in files):
                # 计算相对路径作为模块前缀
                rel_path = os.path.relpath(root, exe_dir)

                if rel_path == '.':
                    prefix = ''
                else:
                    # 将路径转换为模块名
                    prefix = rel_path.replace(os.sep, '.')

                    # 跳过明显的系统包和框架包
                    if any(prefix.startswith(p) for p in ['cullinan', 'tornado', 'certifi', '_']):
                        continue

                # 扫描目录中的 Python 文件
                for f in files:
                    if f.endswith('.py') and f != '__init__.py':
                        mod_name = f[:-3]  # 去除 .py
                        full_mod = f"{prefix}.{mod_name}" if prefix else mod_name

                        if full_mod not in scanned_modules and not full_mod.startswith('cullinan'):
                            scanned_modules.append(full_mod)
                            logger.debug("\t|||\t\t\tFound Python file: %s -> module: %s", f, full_mod)

                    elif f.endswith('.pyc') and f != '__init__.pyc':
                        mod_name = f[:-4]  # 去除 .pyc
                        full_mod = f"{prefix}.{mod_name}" if prefix else mod_name

                        if full_mod not in scanned_modules and not full_mod.startswith('cullinan'):
                            scanned_modules.append(full_mod)
                            logger.debug("\t|||\t\t\tFound compiled file: %s -> module: %s", f, full_mod)

                    elif f.endswith(('.pyd', '.so')):
                        # 扩展模块
                        mod_name = f.split('.')[0]
                        full_mod = f"{prefix}.{mod_name}" if prefix else mod_name

                        if full_mod not in scanned_modules and not full_mod.startswith('cullinan'):
                            scanned_modules.append(full_mod)
                            logger.debug("\t|||\t\t\tFound extension: %s -> module: %s", f, full_mod)

                # 如果是包，也添加包本身
                if is_package and prefix and not prefix.startswith('cullinan'):
                    if prefix not in scanned_modules:
                        scanned_modules.append(prefix)
                        logger.debug("\t|||\t\t\tFound package: %s", prefix)

        if scanned_modules:
            logger.info("\t|||\t\t\tFound %d modules via directory scanning", len(scanned_modules))
            # 合并到 modules 列表
            for mod in scanned_modules:
                if mod not in modules:
                    modules.append(mod)

    # 策略3: 尝试从可执行文件目录扫描 .pyd/.so 扩展模块（旧逻辑保留）
    if mode == 'standalone' and len(modules) <= 1:
        exe_dir = os.path.dirname(sys.executable)
        logger.info("\t|||\t\t\tScanning Nuitka standalone directory: %s", exe_dir)

        # 查找 .pyd (Windows) 或 .so (Linux) 扩展模块
        for root, dirs, files in os.walk(exe_dir):
            # 排除明显的系统目录
            dirs[:] = [d for d in dirs if not d.startswith('_') and d not in ['lib', 'bin']]

            for f in files:
                # Nuitka 编译的模块扩展名
                if f.endswith('.pyd') or f.endswith('.so') or f.endswith('.pyc'):
                    # 提取模块名
                    mod_name = f.rsplit('.', 1)[0]
                    # 去除 Nuitka 可能添加的后缀
                    if '.' in mod_name:
                        mod_name = mod_name.split('.')[0]

                    # 尝试构建完整的模块路径
                    rel_path = os.path.relpath(root, exe_dir)
                    if rel_path != '.':
                        full_mod = rel_path.replace(os.sep, '.') + '.' + mod_name
                    else:
                        full_mod = mod_name

                    if full_mod not in modules and not full_mod.startswith('cullinan'):
                        modules.append(full_mod)

    # 策略3: onefile 模式，尝试从调用栈推断包名
    if mode == 'onefile' and not modules:
        try:
            caller_pkg = get_caller_package()
            if caller_pkg:
                logger.info("\t|||\t\t\tInferred package: %s", caller_pkg)
                # 尝试导入包并扫描其子模块
                try:
                    pkg = importlib.import_module(caller_pkg)
                    # 遍历包的所有属性
                    for attr_name in dir(pkg):
                        if not attr_name.startswith('_'):
                            attr = getattr(pkg, attr_name, None)
                            if inspect.ismodule(attr):
                                mod_name = getattr(attr, '__name__', None)
                                if mod_name and mod_name not in modules:
                                    modules.append(mod_name)
                except Exception as e:
                    logger.debug("\t|||\t\t\tFailed to import package %s: %s", caller_pkg, e)
        except CallerPackageException:
            pass

    # 策略4: 尝试通过 __main__ 模块的路径推断
    if not modules:
        main_mod = sys.modules.get('__main__')
        if main_mod and hasattr(main_mod, '__file__'):
            main_file = os.path.abspath(main_mod.__file__)
            main_dir = os.path.dirname(main_file)

            # 扫描 __main__ 所在目录
            logger.info("\t|||\t\t\tScanning from __main__ directory: %s", main_dir)
            for root, dirs, files in os.walk(main_dir):
                dirs[:] = [d for d in dirs if not d.startswith('_')]

                if '__init__.py' in files or '__init__.pyc' in files:
                    rel = os.path.relpath(root, main_dir)
                    prefix = '' if rel == '.' else rel.replace(os.sep, '.') + '.'

                    for f in files:
                        if (f.endswith('.py') or f.endswith('.pyc')) and f != '__init__.py':
                            mod_name = prefix + f.rsplit('.', 1)[0]
                            if mod_name not in modules:
                                modules.append(mod_name)

    logger.info("\t|||\t\t\tFound %d modules via Nuitka scanning", len(modules))
    return modules


def scan_modules_pyinstaller():
    """PyInstaller 打包后的模块扫描逻辑

    优先使用配置的 user_packages，精确扫描用户代码
    """
    logger.info("\t|||\t\t\tDetected PyInstaller frozen environment")

    mode = get_pyinstaller_mode()
    logger.info("\t|||\t\t\tPyInstaller mode: %s", mode or "unknown")

    modules = []

    # 获取配置
    from cullinan.config import get_config
    config = get_config()

    # 策略1: 使用配置的用户包（推荐方式）
    if config.user_packages:
        logger.info("\t|||\t\t\tUsing configured user packages: %s", config.user_packages)

        for package_name in config.user_packages:
            try:
                # 先尝试导入包
                pkg = importlib.import_module(package_name)
                logger.debug("\t|||\t\t\tImported package: %s", package_name)

                # 添加包本身
                if package_name not in modules:
                    modules.append(package_name)

                # 扫描包下的所有子模块
                if hasattr(pkg, '__path__'):
                    for finder, name, is_pkg in pkgutil.walk_packages(pkg.__path__, package_name + '.'):
                        if name not in modules:
                            modules.append(name)
                            logger.debug("\t|||\t\t\tFound submodule: %s", name)

            except Exception as e:
                logger.warning("\t|||\t\t\tFailed to import package %s: %s", package_name, str(e))

                # 回退：尝试从 sys.modules 中查找该包的模块
                for mod_name in sys.modules.keys():
                    if mod_name.startswith(package_name):
                        if mod_name not in modules:
                            modules.append(mod_name)

        logger.info("\t|||\t\t\tFound %d modules from configured packages", len(modules))

        # 如果配置了包且找到了模块，直接返回
        if modules:
            return modules

    # 策略2: 如果没有配置或配置的包没找到模块，使用目录扫描
    if config.auto_scan:
        logger.info("\t|||\t\t\tNo user packages configured or no modules found, using directory scanning")

        base_dirs = []

        # 获取 PyInstaller 的临时解压目录
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            base_dirs.append(meipass)
            logger.info("\t|||\t\t\tPyInstaller _MEIPASS: %s", meipass)

        # 也检查可执行文件目录（onedir 模式）
        if mode == 'onedir':
            exe_dir = os.path.dirname(sys.executable)
            if exe_dir not in base_dirs:
                base_dirs.append(exe_dir)
                logger.info("\t|||\t\t\tPyInstaller exe directory: %s", exe_dir)

        seen = set()

        # 使用更专业的方式：检查模块是否来自用户代码
        def is_user_module_path(file_path: str) -> bool:
            """判断文件路径是否为用户模块"""
            if not file_path:
                return False

            # 排除框架和常见第三方库
            excluded_names = ['cullinan', 'tornado', 'certifi', 'PIL', 'charset_normalizer']
            for name in excluded_names:
                if name in file_path:
                    return False

            return True

        for base in base_dirs:
            if not base or not os.path.isdir(base):
                continue

            logger.info("\t|||\t\t\tScanning directory: %s", base)

            # 遍历目录查找 Python 模块
            for root, dirs, files in os.walk(base):
                # 排除系统目录
                dirs[:] = [d for d in dirs if not d.startswith('_')]

                # 检查是否是 Python 包（包含 __init__.py）
                has_init = '__init__.py' in files or '__init__.pyc' in files

                if not has_init:
                    continue

                # 计算相对路径作为包前缀
                rel = os.path.relpath(root, base)
                if rel == '.':
                    prefix = ''
                else:
                    prefix = rel.replace(os.sep, '.') + '.'

                # 扫描包中的所有 Python 文件
                for f in files:
                    if (f.endswith('.py') or f.endswith('.pyc')) and f not in ['__init__.py', '__init__.pyc']:
                        mod_name = f.rsplit('.', 1)[0]
                        full_mod = prefix + mod_name

                        # 使用路径检查而非硬编码的前缀列表
                        file_path = os.path.join(root, f)
                        if is_user_module_path(file_path) and full_mod not in seen:
                            seen.add(full_mod)
                            modules.append(full_mod)

        # 策略3: 从 sys.modules 补充扫描
        def is_user_module(mod_name: str, mod) -> bool:
            """判断是否为用户模块"""
            if mod_name.startswith('cullinan') or mod_name.startswith('_'):
                return False

            mod_file = getattr(mod, '__file__', None)
            if not mod_file:
                return False

            # 检查是否在 _MEIPASS 中
            if meipass and meipass in mod_file:
                return is_user_module_path(mod_file)

            return False

        for mod_name in list(sys.modules.keys()):
            if mod_name in seen:
                continue

            mod = sys.modules.get(mod_name)
            if mod and is_user_module(mod_name, mod):
                seen.add(mod_name)
                modules.append(mod_name)

        logger.info("\t|||\t\t\tFound %d modules via PyInstaller scanning", len(modules))

    return modules



def list_submodules(package_name):
    """List all submodule full names under a package (non-recursive and recursive via pkgutil.walk_packages).

    Returns a list of dotted module names like 'mypkg.submod'. If the package cannot be
    imported or has no __path__, returns an empty list.
    """
    try:
        package = importlib.import_module(package_name)
    except Exception:
        return []

    submodules = []
    if hasattr(package, '__path__'):
        for finder, name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
            # include both packages and modules so decorators/register-time code runs on import
            submodules.append(name)
    return submodules


def reflect_module(module_name: str, func: str):
    """Import a module by dotted name and optionally call a function on it.

    - If `func` is 'nobody' or 'controller' we only import the module (decorators will run at import).
    - Otherwise, if the attribute named `func` exists and is callable, call it.

    Errors during import or call are logged but swallowed to keep scanning robust.
    """
    if not module_name:
        return

    # sanitize package-style paths that may come from file-system discovery
    if module_name.endswith('.py'):
        module_name = module_name[:-3]
    module_name = module_name.strip('.')

    if not module_name:
        return

    logger.debug("\t|||\t\t\tReflecting module: %s (func: %s)", module_name, func)

    mod = None

    # 策略0: 优先检查 sys.modules（Nuitka 环境下模块通常已加载）
    if module_name in sys.modules:
        mod = sys.modules[module_name]
        logger.info("\t|||\t\t\t✓ Found in sys.modules: %s", module_name)

        # 对于 controller 和 service，模块已加载意味着装饰器已执行
        if func in ('nobody', 'controller'):
            logger.debug("\t|||\t\t\t✓ Module already loaded (decorators executed): %s", module_name)
            return

        # 继续调用函数（如果需要）
        if func not in ('nobody', 'controller'):
            try:
                fn = getattr(mod, func, None)
                if callable(fn):
                    fn()
                    logger.debug("\t|||\t\t\t✓ Called function: %s.%s", module_name, func)
            except Exception as e:
                logger.debug("\t|||\t\t\t✗ Error calling %s.%s: %s", module_name, func, str(e))
        return

    # 策略1: 标准导入（适用于所有环境）
    try:
        mod = importlib.import_module(module_name)
        logger.info("\t|||\t\t\t✓ Successfully imported: %s", module_name)

        # 对于 controller 和 service，导入即可（装饰器会执行）
        if func in ('nobody', 'controller'):
            logger.debug("\t|||\t\t\t✓ Module imported (decorators executed): %s", module_name)
            return

    except ImportError as e:
        error_msg = str(e)
        logger.warning("\t|||\t\t\t✗ Import failed for %s: %s", module_name, error_msg)

        # 策略2: 尝试相对导入（Nuitka 编译后可能需要）
        if is_nuitka_compiled() and '.' in module_name:
            # 尝试从父包导入
            parts = module_name.rsplit('.', 1)
            if len(parts) == 2:
                parent_pkg, mod_part = parts
                try:
                    parent = importlib.import_module(parent_pkg)
                    if hasattr(parent, mod_part):
                        mod = getattr(parent, mod_part)
                        logger.info("\t|||\t\t\t✓ Imported as attribute: %s from %s", mod_part, parent_pkg)

                        if func in ('nobody', 'controller'):
                            return
                    else:
                        # 尝试使用 __import__ 的 fromlist 参数
                        try:
                            mod = __import__(module_name, fromlist=[mod_part])
                            logger.info("\t|||\t\t\t✓ Imported using __import__: %s", module_name)

                            if func in ('nobody', 'controller'):
                                return
                        except Exception as e2:
                            logger.debug("\t|||\t\t\t✗ __import__ also failed: %s", str(e2))
                except Exception as e3:
                    logger.debug("\t|||\t\t\t✗ Relative import failed: %s", str(e3))

        # 策略3: 打包环境特殊处理 - 从 sys.modules 获取
        if module_name in sys.modules:
            mod = sys.modules[module_name]
            logger.info("\t|||\t\t\t✓ Found in sys.modules: %s", module_name)

            if func in ('nobody', 'controller'):
                return
    except ImportError as e:
        logger.warning("\t|||\t\t\t✗ Import failed for %s: %s", module_name, str(e))

        # 策略2: 打包环境特殊处理
        # 尝试从 sys.modules 直接获取（可能已被打包工具预加载）
        if module_name in sys.modules:
            mod = sys.modules[module_name]
            logger.info("\t|||\t\t\t✓ Found in sys.modules: %s", module_name)
        else:
            # 策略3: 尝试通过文件路径导入（最后手段）
            if is_pyinstaller_frozen() or is_nuitka_compiled():
                # 尝试构建可能的文件路径
                base_dirs = []

                if is_pyinstaller_frozen():
                    meipass = getattr(sys, '_MEIPASS', None)
                    if meipass:
                        base_dirs.append(meipass)

                if is_nuitka_compiled():
                    exe_dir = os.path.dirname(sys.executable)
                    base_dirs.append(exe_dir)

                for base in base_dirs:
                    module_path = os.path.join(base, module_name.replace('.', os.sep) + '.py')
                    if os.path.exists(module_path):
                        try:
                            spec = importlib.util.spec_from_file_location(module_name, module_path)
                            if spec and spec.loader:
                                mod = importlib.util.module_from_spec(spec)
                                sys.modules[module_name] = mod  # 注册到 sys.modules
                                spec.loader.exec_module(mod)
                                logger.info("\t|||\t\t\t✓ Imported from file: %s", module_path)
                                break
                        except Exception as e:
                            logger.warning("\t|||\t\t\t✗ Failed to import from file %s: %s", module_path, str(e))
    except Exception as e:
        logger.warning("\t|||\t\t\t✗ Unexpected error importing %s: %s", module_name, str(e))
        return

    if mod is None:
        logger.warning("\t|||\t\t\t✗ Could not import module: %s", module_name)
        return

    # 对于 controller 和 service，只需导入即可（装饰器会在导入时执行）
    if func in ('nobody', 'controller'):
        logger.debug("\t|||\t\t\t✓ Module imported (decorators executed): %s", module_name)
        return

    # 调用指定的函数（如果存在）
    try:
        fn = getattr(mod, func, None)
        if callable(fn):
            fn()
            logger.debug("\t|||\t\t\t✓ Called function: %s.%s", module_name, func)
    except Exception as e:
        logger.debug("\t|||\t\t\t✗ Error calling %s.%s: %s", module_name, func, str(e))
        return


def file_list_func():
    """Discover candidate modules to import/reflect.

    Strategy (best-effort, in order):
      1. 检测是否为打包环境（Nuitka 或 PyInstaller）
         - 如果是 Nuitka，使用 scan_modules_nuitka()
         - 如果是 PyInstaller，使用 scan_modules_pyinstaller()
      2. 尝试通过调用者包名扫描（开发环境）
      3. 回退到扫描当前工作目录

    Returns a list of dotted module names.
    """
    logger.info("\t|||\t\t\tStarting module discovery...")

    # 策略1: 检测打包环境并使用专门的扫描逻辑
    # 注意：Nuitka 检测优先，因为它可能也设置 sys.frozen
    if is_nuitka_compiled():
        logger.info("\t|||\t\t\t=== Using Nuitka scanning strategy ===")
        modules = scan_modules_nuitka()
        if modules:
            logger.info("\t|||\t\t\tDiscovered %d modules", len(modules))
            return modules
    elif is_pyinstaller_frozen():
        logger.info("\t|||\t\t\t=== Using PyInstaller scanning strategy ===")
        modules = scan_modules_pyinstaller()
        if modules:
            logger.info("\t|||\t\t\tDiscovered %d modules", len(modules))
            return modules

    # 策略2: 开发环境 - 尝试通过调用者包名扫描
    logger.info("\t|||\t\t\t=== Using development environment scanning ===")
    try:
        caller_pkg = get_caller_package()
        if caller_pkg:
            logger.info("\t|||\t\t\tCaller package: %s", caller_pkg)
            mods = list_submodules(caller_pkg)
            if mods:
                logger.info("\t|||\t\t\tDiscovered %d modules via package scanning", len(mods))
                return mods
    except CallerPackageException:
        logger.debug("\t|||\t\t\tCould not determine caller package")
        pass

    # 策略3: 回退 - 扫描当前工作目录
    logger.info("\t|||\t\t\t=== Fallback: scanning current working directory ===")
    modules = []
    cwd = os.getcwd()
    logger.info("\t|||\t\t\tScanning directory: %s", cwd)

    for root, dirs, files in os.walk(cwd):
        # 排除隐藏目录和虚拟环境
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'env', '__pycache__', 'build', 'dist']]

        if '__init__.py' not in files:
            continue

        rel = os.path.relpath(root, cwd)
        if rel == '.':
            prefix = ''
        else:
            prefix = rel.replace(os.sep, '.') + '.'

        for f in files:
            if f.endswith('.py') and f != '__init__.py':
                modules.append(prefix + f[:-3])

    logger.info("\t|||\t\t\tDiscovered %d modules via directory scanning", len(modules))
    return modules


def scan_controller(modules: list):
    for mod in modules:
        reflect_module(mod, 'controller')


def scan_service(modules: list):
    for mod in modules:
        reflect_module(mod, 'nobody')


def get_index_list(url_list: list) -> list:
    index_list = []
    for index in range(0, url_list.__len__()):
        if url_list[index] == '([a-zA-Z0-9-]+)':
            index_list.append(index)
    index_list.append('*')
    return index_list


def sort_url():
    if handler_list.__len__() == 0:
        return
    handler_list_length = []
    for index in range(0, handler_list.__len__()):
        handler_list[index] = list(handler_list[index])
        handler_list[index][0] = handler_list[index][0].split('/')
        index_list = get_index_list(handler_list[index][0])
        handler_list_length.append(index_list.__len__())
        handler_list[index].append(index_list)
    for index in range(0, max(handler_list_length)):
        for i in range(0, handler_list.__len__()):
            for j in range(i + 1, handler_list.__len__()):
                if handler_list[i][2].__len__() >= index + 1 and handler_list[j][2].__len__() >= index + 1:
                    if handler_list[i][2][index] != '*' and handler_list[j][2][index] != '*':
                        if handler_list[i][2][index] < handler_list[j][2][index]:
                            handler_list[i], handler_list[j] = handler_list[j], handler_list[i]
                    elif handler_list[i][2][index] != '*' and handler_list[j][2][index] == '*':
                        handler_list[i], handler_list[j] = handler_list[j], handler_list[i]
                    elif handler_list[i][2][index] == '*':
                        continue
    for item in handler_list:
        url = ""
        for index in range(1, len(item[0])):
            url = url + "/" + item[0][index]
        item[0] = url
        del item[2]


def is_started_directly() -> bool:
    """Return True if the process was started directly (a __main__ frame exists).

    We inspect the stack and check whether any frame's module name is '__main__'.
    This is a conservative heuristic: if the framework is imported by another
    application (e.g. tests, embedding, REPL), we won't auto-install console handlers.
    """
    try:
        for frame_info in inspect.stack():
            module = inspect.getmodule(frame_info[0])
            if module is None:
                continue
            if getattr(module, '__name__', '') == '__main__':
                return True
    except Exception:
        pass
    return False


def _ensure_console_logging():
    """Ensure framework logs appear on console when the application hasn't configured logging.

    Behavior:
    - If the root logger already has handlers, assume application configured logging and do nothing.
    - If the 'cullinan' package logger already has handlers, do nothing.
    - Otherwise add a StreamHandler to stdout on the 'cullinan' logger at INFO level.
    - Honor env var CULLINAN_DISABLE_AUTO_CONSOLE=1 to disable this behavior.
    """
    try:
        if os.getenv('CULLINAN_DISABLE_AUTO_CONSOLE', '0') == '1':
            return None
        # Allow forcing console handler via env var (useful in tests/IDE runs)
        force = os.getenv('CULLINAN_FORCE_CONSOLE', '0').lower() in ('1', 'true', 'yes')
        # only auto-enable console logging when the process was started directly
        # unless forced via CULLINAN_FORCE_CONSOLE
        if not force and not is_started_directly():
            return None
        root = logging.getLogger()
        # consider only "real" handlers (not NullHandler)
        root_has_real = any(not isinstance(h, logging.NullHandler) for h in getattr(root, 'handlers', []) if h is not None)
        if root_has_real:
            return None
        pkg_logger = logging.getLogger('cullinan')
        pkg_has_real = any(not isinstance(h, logging.NullHandler) for h in getattr(pkg_logger, 'handlers', []) if h is not None)
        if pkg_has_real:
            return None
        # add a console handler to the package logger
        console_handler = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        console_handler.setFormatter(fmt)
        # allow customizing console level via env var (e.g. DEBUG/INFO)
        lvl_name = os.getenv('CULLINAN_AUTO_CONSOLE_LEVEL', '').strip()
        if lvl_name:
            try:
                level = int(lvl_name)
            except Exception:
                level = getattr(logging, lvl_name.upper(), None)
            if isinstance(level, int):
                console_handler.setLevel(level)
            else:
                console_handler.setLevel(logging.INFO)
        else:
            console_handler.setLevel(logging.INFO)
        pkg_logger.addHandler(console_handler)
        pkg_logger.setLevel(logging.INFO)
        pkg_logger.propagate = False
        return console_handler
    except Exception:
        # never raise from logging setup
        return None


# ASCII banner used when the framework starts; backslashes are escaped so this
# compiles cleanly and prints exactly as intended.
BANNER = (
    "|||||||||||||||||||||||||||||||||||||||||||||||||\n"
    "|||                                           |||\n"
    "|||    _____      _ _ _                       |||\n"
    "|||   / ____|    | | (_)                      |||\n"
    "|||  | |    _   _| | |_ _ __   __ _ _ __      |||\n"
    "|||  | |   | | | | | | | '_ \\ / _` | '_ \\     |||\n"
    "|||  | |___| |_| | | | | | | | (_| | | | |    |||\n"
    "|||   \\_____\\__,_|_|_|_|_| |_|\\__,_|_| |_|    |||\n"
    "|||                                           |||\n"
    "|||||||||||||||||||||||||||||||||||||||||||||||||\n"
    "\t|||\n"
)


def run(handlers=None):
    if handlers is None:
        handlers = []
    # ensure console logging is available by default when the app hasn't configured logging
    # ensure logging handlers are present when appropriate (may install console handler)
    installed_handler = _ensure_console_logging()
    # If we installed a handler ourselves, temporarily set its formatter to '%(message)s'
    # so the banner is emitted verbatim via logging (no print necessary). Restore afterwards.
    if installed_handler is not None:
        old_fmt = None
        try:
            old_fmt = getattr(installed_handler, 'formatter', None)
            installed_handler.setFormatter(logging.Formatter('%(message)s'))
            logger.info(BANNER)
        finally:
            try:
                installed_handler.setFormatter(old_fmt)
            except Exception:
                pass
    else:
        logger.info(BANNER)
    logger.info("\t|||\tloading env...")
    load_dotenv()
    load_dotenv(verbose=True)
    env_path = Path(os.getcwd()) / '.env'
    load_dotenv(dotenv_path=env_path)
    settings = dict(
        template_path=os.path.join(os.getcwd(), 'templates'),
        static_path=os.path.join(os.getcwd(), 'static')
    )
    logger.info("\t|||\t\t└---scanning controller...")
    logger.info("\t|||\t\t\t...")
    scan_service(file_list_func())
    scan_controller(file_list_func())
    sort_url()
    mapping = tornado.web.Application(
        handlers=handler_list + handlers,
        **settings
    )
    logger.info("\t|||\t\t└---loading controller finish\n\t|||\t")
    define("port", default=os.getenv("SERVER_PORT", 4080), help="run on the given port", type=int)
    logger.info("\t|||\tloading env finish\n\t|||\t")
    http_server = tornado.httpserver.HTTPServer(mapping)
    if os.getenv("SERVER_THREAD") is not None:
        logger.info("\t|||\tserver is starting")
        logger.info("\t|||\tport is %s", str(os.getenv("SERVER_PORT", 4080)))
        http_server.bind(options.port)
        http_server.start(int(os.getenv("SERVER_THREAD")) | 0)
    else:
        http_server.listen(options.port)
        logger.info("\t|||\tserver is starting")
        logger.info("\t|||\tport is %s", str(os.getenv("SERVER_PORT", 4080)))

    # Register signal handlers to allow graceful shutdown (SIGINT/SIGTERM)
    try:
        def _handle_signal(signum, frame):
            logger.info("Received signal %s, stopping...", signum)
            try:
                # request the IOLoop to stop from its own thread
                tornado.ioloop.IOLoop.current().add_callback(tornado.ioloop.IOLoop.current().stop)
            except Exception:
                try:
                    tornado.ioloop.IOLoop.current().stop()
                except Exception:
                    pass

        signal.signal(signal.SIGINT, _handle_signal)
        try:
            # SIGTERM may not exist on some Windows setups; ignore failures
            signal.signal(signal.SIGTERM, _handle_signal)
        except Exception:
            pass
    except Exception:
        # best-effort: do not fail startup if signals can't be registered
        pass

    # Start the IOLoop and handle KeyboardInterrupt gracefully so closing
    # the app doesn't produce a long traceback in normal shutdown.
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down server...")
    except Exception:
        logger.exception("Exception running IOLoop")
    finally:
        # Stop accepting new connections and stop the IOLoop.
        try:
            http_server.stop()
        except Exception:
            pass
        try:
            io_loop = tornado.ioloop.IOLoop.current()
            # ensure the loop is stopped
            try:
                io_loop.add_callback(io_loop.stop)
            except Exception:
                try:
                    io_loop.stop()
                except Exception:
                    pass
        except Exception:
            pass


async def _run_shutdown_sequence(server, loop, timeout_seconds: int):
    """Wait for controller.active_request_count to drop to zero (or until timeout),
    then stop the server and close any remaining connections.

    This function is used by tests and by graceful shutdown logic to allow
    inflight requests to finish before the server is stopped.
    """
    try:
        import asyncio as _asyncio
        import cullinan.controller as _ctrl

        start = getattr(loop, 'time', _asyncio.get_event_loop().time)()
        deadline = start + (timeout_seconds or 0)

        # poll until active_request_count reaches 0 or timeout
        while getattr(_ctrl, 'active_request_count', 0) > 0:
            now = getattr(loop, 'time', _asyncio.get_event_loop().time)()
            if timeout_seconds and now >= deadline:
                break
            await _asyncio.sleep(0.1)

        # attempt to stop server and close connections
        try:
            if hasattr(server, 'stop') and callable(server.stop):
                server.stop()
        except Exception:
            pass
        try:
            if hasattr(server, 'close_all_connections') and callable(server.close_all_connections):
                server.close_all_connections()
        except Exception:
            pass
    except Exception:
        # be robust in tests or exotic environments
        try:
            if hasattr(server, 'stop') and callable(server.stop):
                server.stop()
        except Exception:
            pass
    return None

