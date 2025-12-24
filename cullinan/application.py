# -*- coding: utf-8 -*-
import importlib
import inspect
import os
import importlib.util
import logging
import signal

import tornado.ioloop
from cullinan.handler import get_handler_registry
from dotenv import load_dotenv
from pathlib import Path
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpserver
from tornado.options import define, options
import sys

# Import module scanning utilities (refactored for better maintainability)
from cullinan.module_scanner import (
    is_pyinstaller_frozen,
    is_nuitka_compiled,
    file_list_func
)

# Module-level logger (FastAPI-style)
logger = logging.getLogger(__name__)


def reflect_module(module_name: str, func: str) -> None:
    """Import a module by dotted name and optionally call a function on it.

    - If `func` is 'nobody' or 'controller' we only import the module (decorators will run at import).
    - Otherwise, if the attribute named `func` exists and is callable, call it.

    Errors during import or call are logged but swallowed to keep scanning robust.
    
    Args:
        module_name: Dotted module name to import (e.g., 'myapp.controllers.user')
        func: Function name to call after import, or 'nobody'/'controller' to skip calling
    """
    if not module_name:
        return

    # sanitize package-style paths that may come from file-system discovery
    if module_name.endswith('.py'):
        module_name = module_name[:-3]
    module_name = module_name.strip('.')

    if not module_name:
        return

    logger.debug("Reflecting module: %s (func: %s)", module_name, func)

    mod = None

    # 策略0: 优先检查 sys.modules（Nuitka 环境下模块通常已加载）
    if module_name in sys.modules:
        mod = sys.modules[module_name]
        logger.info("[OK] Found in sys.modules: %s", module_name)

        # 对于 controller 和 service，模块已加载意味着装饰器已执行
        if func in ('nobody', 'controller'):
            logger.debug("[OK] Module already loaded (decorators executed): %s", module_name)
            return

        # 继续调用函数（如果需要）
        if func not in ('nobody', 'controller'):
            try:
                fn = getattr(mod, func, None)
                if callable(fn):
                    fn()
                    logger.debug("[OK] Called function: %s.%s", module_name, func)
            except Exception as e:
                logger.debug("[FAIL] Error calling %s.%s: %s", module_name, func, str(e))
        return

    # 策略1: 标准导入（适用于所有环境）
    try:
        mod = importlib.import_module(module_name)
        logger.info("[OK] Successfully imported: %s", module_name)

        # 对于 controller 和 service，导入即可（装饰器会执行）
        if func in ('nobody', 'controller'):
            logger.debug("[OK] Module imported (decorators executed): %s", module_name)
            return

    except ImportError as e:
        error_msg = str(e)
        logger.warning("[FAIL] Import failed for %s: %s", module_name, error_msg)

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
                        logger.info("[OK] Imported as attribute: %s from %s", mod_part, parent_pkg)

                        if func in ('nobody', 'controller'):
                            return
                    else:
                        # 尝试使用 __import__ 的 fromlist 参数
                        try:
                            mod = __import__(module_name, fromlist=[mod_part])
                            logger.info("[OK] Imported using __import__: %s", module_name)

                            if func in ('nobody', 'controller'):
                                return
                        except Exception as e2:
                            logger.debug("[FAIL] __import__ also failed: %s", str(e2))
                except Exception as e3:
                    logger.debug("[FAIL] Relative import failed: %s", str(e3))

        # 策略3: 从 sys.modules 获取（可能已被打包工具预加载）
        if module_name in sys.modules:
            mod = sys.modules[module_name]
            logger.info("[OK] Found in sys.modules: %s", module_name)

            if func in ('nobody', 'controller'):
                return

        # 策略4: 尝试通过文件路径导入（最后手段）
        elif is_pyinstaller_frozen() or is_nuitka_compiled():
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
                            logger.info("[OK] Imported from file: %s", module_path)
                            break
                    except Exception as import_ex:
                        logger.warning("[FAIL] Failed to import from file %s: %s", module_path, str(import_ex))
    except Exception as e:
        logger.warning("[FAIL] Unexpected error importing %s: %s", module_name, str(e))
        return

    if mod is None:
        logger.warning("[FAIL] Could not import module: %s", module_name)
        return

    # 对于 controller 和 service，只需导入即可（装饰器会在导入时执行）
    if func in ('nobody', 'controller'):
        logger.debug("[OK] Module imported (decorators executed): %s", module_name)
        return

    # 调用指定的函数（如果存在）
    try:
        fn = getattr(mod, func, None)
        if callable(fn):
            fn()
            logger.debug("[OK] Called function: %s.%s", module_name, func)
    except Exception as e:
        logger.debug("[FAIL] Error calling %s.%s: %s", module_name, func, str(e))
        return



def scan_controller(modules: list) -> None:
    """Scan and import controller modules to register their handlers.
    
    Args:
        modules: List of dotted module names to scan
    """
    for mod in modules:
        reflect_module(mod, 'controller')



def scan_service(modules: list) -> None:
    """Scan and import service modules to register their services.
    
    Args:
        modules: List of dotted module names to scan
    """
    for mod in modules:
        reflect_module(mod, 'nobody')



def sort_url() -> None:
    """Sort URL handlers with O(n log n) complexity instead of O(n³).
    
    Optimized version that uses the HandlerRegistry's built-in sort method.
    Handlers with dynamic segments (e.g., ([a-zA-Z0-9-]+)) are prioritized lower than
    static segments to ensure more specific routes match first.
    """
    registry = get_handler_registry()
    registry.sort()


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


def _register_explicit_classes():
    """Register explicit services and controllers if configured.

    This allows users to skip module scanning and directly register classes,
    which improves startup performance for large projects.
    """
    from cullinan.config import get_config

    config = get_config()

    # Register explicit services
    if config.explicit_services:
        logger.info(
            "Registering %d explicit services (skipping scan)",
            len(config.explicit_services)
        )
        for service_class in config.explicit_services:
            try:
                # Import the service's module to trigger decorator registration
                module = inspect.getmodule(service_class)
                if module:
                    logger.debug(
                        "Explicit service registered: %s from %s",
                        service_class.__name__,
                        module.__name__
                    )
            except Exception as e:
                logger.warning(
                    "Failed to register explicit service %s: %s",
                    service_class.__name__ if hasattr(service_class, '__name__') else service_class,
                    str(e)
                )

    # Register explicit controllers
    if config.explicit_controllers:
        logger.info(
            "Registering %d explicit controllers (skipping scan)",
            len(config.explicit_controllers)
        )
        for controller_class in config.explicit_controllers:
            try:
                # Import the controller's module to trigger decorator registration
                module = inspect.getmodule(controller_class)
                if module:
                    logger.debug(
                        "Explicit controller registered: %s from %s",
                        controller_class.__name__,
                        module.__name__
                    )
            except Exception as e:
                logger.warning(
                    "Failed to register explicit controller %s: %s",
                    controller_class.__name__ if hasattr(controller_class, '__name__') else controller_class,
                    str(e)
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
    logger.info("loading env...")
    load_dotenv()
    load_dotenv(verbose=True)
    env_path = Path(os.getcwd()) / '.env'
    load_dotenv(dotenv_path=env_path)
    settings = dict(
        template_path=os.path.join(os.getcwd(), 'templates'),
        static_path=os.path.join(os.getcwd(), 'static')
    )

    # IMPORTANT: Configure dependency injection system BEFORE scanning
    # This ensures that when @service and @controller decorators execute,
    # the injection system is already set up
    logger.info("└---configuring dependency injection...")
    from cullinan.core.injection import get_injection_registry
    from cullinan.service.registry import get_service_registry
    from cullinan.core.injection_executor import InjectionExecutor, set_injection_executor

    # Get registries (ServiceRegistry auto-registers itself as provider in __init__)
    injection_registry = get_injection_registry()
    service_registry = get_service_registry()

    # Initialize InjectionExecutor with the registry
    executor = InjectionExecutor(injection_registry)
    set_injection_executor(executor)

    logger.info("└---dependency injection configured (InjectionExecutor initialized)")

    # Register explicit services and controllers (if configured)
    _register_explicit_classes()

    # Now scan services and controllers
    logger.info("└---scanning services...")
    logger.info("...")
    service_modules = file_list_func()

    if not service_modules:
        logger.warning("[WARN] No modules found for service scanning!")
        logger.warning("[WARN] This is expected in packaged environments without configuration.")
        logger.warning("[WARN] Consider using cullinan.configure(user_packages=['your_app'])")
    else:
        logger.info("└---found %d modules to scan", len(service_modules))
        scan_service(service_modules)

    logger.info("└---scanning controllers...")
    logger.info("...")
    controller_modules = file_list_func()

    if not controller_modules:
        logger.warning("[WARN] No modules found for controller scanning!")
        logger.warning("[WARN] This is expected in packaged environments without configuration.")
    else:
        logger.info("└---found %d modules to scan", len(controller_modules))
        scan_controller(controller_modules)

    sort_url()

    # ========== Service 初始化（扫描完成后） ==========
    logger.info("└---initializing services...")
    from cullinan.service import get_service_registry

    service_registry = get_service_registry()
    service_count = service_registry.count()

    if service_count > 0:
        logger.info(f"└---found {service_count} registered services")
        try:
            # 按依赖顺序初始化所有 Service（调用 initialize_all）
            service_registry.initialize_all()
            logger.info(f"[OK] All {service_count} services initialized")
        except Exception as e:
            logger.error(f"[FAIL] Service initialization failed: {e}", exc_info=True)
            logger.warning("[WARN] Application will continue with partial initialization")
    else:
        logger.info("└---no services registered")
    # ========== END Service 初始化 ==========

    # Get handlers from registry
    handler_registry = get_handler_registry()
    registered_handlers = handler_registry.get_handlers()
    
    mapping = tornado.web.Application(
        handlers=registered_handlers + handlers,
        **settings
    )
    logger.info("└---loading controller finish\n")
    define("port", default=os.getenv("SERVER_PORT", 4080), help="run on the given port", type=int)
    logger.info("loading env finish\n")
    http_server = tornado.httpserver.HTTPServer(mapping)
    if os.getenv("SERVER_THREAD") is not None:
        logger.info("server is starting")
        logger.info("port is %s", str(os.getenv("SERVER_PORT", 4080)))
        http_server.bind(options.port)
        http_server.start(int(os.getenv("SERVER_THREAD")) | 0)
    else:
        http_server.listen(options.port)
        logger.info("server is starting")
        logger.info("port is %s", str(os.getenv("SERVER_PORT", 4080)))

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

