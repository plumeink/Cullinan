# -*- coding: utf-8 -*-
import importlib
import inspect
import os
import importlib.util
import logging
import signal
import sys

from dotenv import load_dotenv
from pathlib import Path

# Tornado imports are now conditional — only loaded when engine='tornado'
# This allows the framework to run without tornado installed (ASGI mode)
_tornado_available = False
try:
    import tornado.ioloop
    import tornado.options
    import tornado.web
    import tornado.httpserver
    from tornado.options import define, options
    _tornado_available = True
except ImportError:
    pass

from cullinan.module_scanner import (
    is_pyinstaller_frozen,
    is_nuitka_compiled,
    file_list_func
)

# Module-level logger
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


def _init_framework():
    """Common initialization logic shared by all engine modes.

    Returns:
        Tuple of (ctx, pending_count) — ApplicationContext and the count of
        processed pending registrations.
    """
    logger.info("loading env...")
    load_dotenv()
    load_dotenv(verbose=True)
    env_path = Path(os.getcwd()) / '.env'
    load_dotenv(dotenv_path=env_path)

    # ========== IoC/DI 2.0: 使用 ApplicationContext 作为唯一入口 ==========
    logger.info("└---initializing IoC/DI 2.0 ApplicationContext...")
    from cullinan.core import ApplicationContext, set_application_context
    from cullinan.core.pending import PendingRegistry

    ctx = ApplicationContext()
    set_application_context(ctx)

    _register_explicit_classes()

    logger.info("└---scanning modules...")
    modules = file_list_func()

    if not modules:
        logger.warning("[WARN] No modules found for scanning!")
        logger.warning("[WARN] Consider using cullinan.configure(user_packages=['your_app'])")
    else:
        logger.info("└---found %d modules to scan", len(modules))
        scan_service(modules)
        scan_controller(modules)

    logger.info("└---refreshing ApplicationContext...")
    ctx.refresh()

    pending_count = PendingRegistry.get_instance().count
    logger.info(f"[OK] ApplicationContext refreshed with {pending_count} components")
    logger.info("└---lifecycle hooks executed by ApplicationContext")

    return ctx, pending_count


def _setup_middleware_pipeline():
    """Wire legacy @middleware-registered middleware into the gateway pipeline."""
    try:
        from cullinan.gateway import get_pipeline, AccessLogMiddleware, LegacyMiddlewareBridge
        from cullinan.middleware import get_middleware_registry

        pipeline = get_pipeline()

        # Add built-in access log middleware
        pipeline.add(AccessLogMiddleware())

        # Bridge legacy middleware
        mw_registry = get_middleware_registry()
        registered = mw_registry.get_registered_middleware()
        if registered:
            chain = mw_registry.get_middleware_chain()
            pipeline.add(LegacyMiddlewareBridge(chain))
            logger.info("└---bridged %d legacy middleware into gateway pipeline", len(registered))
    except Exception as exc:
        logger.debug("Middleware pipeline setup skipped: %s", exc)


def _setup_openapi():
    """Auto-register OpenAPI spec endpoints if enabled.

    Reads configuration from CullinanConfig and environment variables:
    - CULLINAN_OPENAPI_ENABLED: '1'/'true' to enable (default: enabled)
    - CULLINAN_OPENAPI_TITLE: API title
    - CULLINAN_OPENAPI_VERSION: API version

    Registers /openapi.json and /openapi.yaml GET endpoints.
    """
    try:
        # Check config
        enabled = True
        title = 'Cullinan API'
        version = '1.0.0'
        description = ''

        try:
            from cullinan.config import get_config
            cfg = get_config()
            enabled = getattr(cfg, 'openapi_enabled', True)
            title = getattr(cfg, 'openapi_title', title)
            version = getattr(cfg, 'openapi_version', version)
            description = getattr(cfg, 'openapi_description', description)
        except Exception:
            pass

        # Environment variable override
        env_enabled = os.getenv('CULLINAN_OPENAPI_ENABLED', '').strip().lower()
        if env_enabled in ('0', 'false', 'no', 'off'):
            enabled = False
        elif env_enabled in ('1', 'true', 'yes', 'on'):
            enabled = True

        env_title = os.getenv('CULLINAN_OPENAPI_TITLE', '').strip()
        if env_title:
            title = env_title
        env_version = os.getenv('CULLINAN_OPENAPI_VERSION', '').strip()
        if env_version:
            version = env_version

        if not enabled:
            logger.debug("OpenAPI auto-generation disabled")
            return

        from cullinan.gateway.openapi import OpenAPIGenerator
        from cullinan.gateway import get_router

        generator = OpenAPIGenerator(
            router=get_router(),
            title=title,
            version=version,
            description=description,
        )
        generator.register_spec_routes()
        logger.info("└---OpenAPI endpoints registered: /openapi.json, /openapi.yaml")

    except Exception as exc:
        logger.debug("OpenAPI setup skipped: %s", exc)


def run(handlers=None, engine=None):
    """Start the Cullinan application.

    Args:
        handlers: Extra (url, handler_class) pairs for Tornado mode.
        engine: Server engine — ``'tornado'`` (default), ``'asgi'``, or ``'auto'``.
                Can also be set via env-var ``CULLINAN_ENGINE`` or
                ``CullinanConfig.server_engine``.
    """
    if handlers is None:
        handlers = []

    installed_handler = _ensure_console_logging()
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

    # Determine engine
    if engine is None:
        engine = os.getenv('CULLINAN_ENGINE', '').strip().lower() or None
    if engine is None:
        try:
            from cullinan.config import get_config
            engine = getattr(get_config(), 'server_engine', 'tornado')
        except Exception:
            engine = 'tornado'

    ctx, pending_count = _init_framework()
    _setup_middleware_pipeline()
    _setup_openapi()

    port = int(os.getenv("SERVER_PORT", 4080))
    host = os.getenv("SERVER_HOST", "0.0.0.0")

    if engine == 'asgi':
        _run_asgi(host, port)
    else:
        # Default: tornado (backward-compatible)
        _run_tornado(host, port, handlers)


def _run_tornado(host: str, port: int, extra_handlers: list):
    """Start the server using the Tornado adapter (single-handler gateway mode)."""
    if not _tornado_available:
        raise ImportError(
            "Tornado is required for engine='tornado'. Install it with: pip install tornado"
        )

    from cullinan.gateway import get_dispatcher, get_router
    from cullinan.adapter import TornadoAdapter

    # Collect global headers from legacy HeaderRegistry
    global_headers = []
    try:
        from cullinan.controller.core import get_header_registry
        hr = get_header_registry()
        if hr.has_headers():
            global_headers = hr.get_headers()
    except Exception:
        pass

    settings = dict(
        template_path=os.path.join(os.getcwd(), 'templates'),
        static_path=os.path.join(os.getcwd(), 'static'),
    )

    dispatcher = get_dispatcher()
    router = get_router()

    logger.info("└---gateway router: %d routes registered", router.route_count())
    logger.info("└---starting Tornado (single-handler gateway mode)")

    adapter = TornadoAdapter(
        dispatcher=dispatcher,
        settings=settings,
        global_headers=global_headers,
        extra_handlers=extra_handlers,
    )

    try:
        define("port", default=port, help="run on the given port", type=int)
    except Exception:
        pass  # already defined (e.g. during tests or hot-reload)
    logger.info("server is starting")
    logger.info("port is %s", str(port))

    adapter.run(host=host, port=port)


def _run_asgi(host: str, port: int):
    """Start the server using the ASGI adapter."""
    from cullinan.gateway import get_dispatcher
    from cullinan.adapter import ASGIAdapter

    global_headers = []
    try:
        from cullinan.controller.core import get_header_registry
        hr = get_header_registry()
        if hr.has_headers():
            global_headers = hr.get_headers()
    except Exception:
        pass

    dispatcher = get_dispatcher()

    logger.info("└---starting ASGI server")

    adapter = ASGIAdapter(
        dispatcher=dispatcher,
        global_headers=global_headers,
    )

    adapter.run(host=host, port=port)


def get_asgi_app():
    """Create and return an ASGI application callable.

    This function performs full framework initialization and returns an ASGI 3.0
    app that can be served by uvicorn, hypercorn, or any ASGI server::

        # myapp.py
        from cullinan.application import get_asgi_app
        app = get_asgi_app()

        # Then: uvicorn myapp:app
    """
    installed_handler = _ensure_console_logging()
    if installed_handler is not None:
        old_fmt = getattr(installed_handler, 'formatter', None)
        try:
            installed_handler.setFormatter(logging.Formatter('%(message)s'))
            logger.info(BANNER)
        finally:
            try:
                installed_handler.setFormatter(old_fmt)
            except Exception:
                pass
    else:
        logger.info(BANNER)

    _init_framework()
    _setup_middleware_pipeline()
    _setup_openapi()

    from cullinan.gateway import get_dispatcher
    from cullinan.adapter import ASGIAdapter

    global_headers = []
    try:
        from cullinan.controller.core import get_header_registry
        hr = get_header_registry()
        if hr.has_headers():
            global_headers = hr.get_headers()
    except Exception:
        pass

    adapter = ASGIAdapter(
        dispatcher=get_dispatcher(),
        global_headers=global_headers,
    )
    return adapter.create_app()


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

