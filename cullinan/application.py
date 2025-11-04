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


def is_nuitka_compiled():
    # Nuitka sets a module-level name __compiled__ when compiled; avoid direct NameError by checking globals
    return bool(globals().get('__compiled__', False))


def get_project_root_with_pyinstaller():
    return os.path.dirname(os.path.abspath(__file__)) + '/../'


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

    Errors during import or call are swallowed to keep scanning robust.
    """
    if not module_name:
        return
    # sanitize package-style paths that may come from file-system discovery
    if module_name.endswith('.py'):
        module_name = module_name[:-3]
    module_name = module_name.strip('.')
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        # if dotted import fails, try importing by file path (fallback)
        try:
            # treat module_name as a path
            if os.path.isabs(module_name) or os.path.exists(module_name):
                spec = importlib.util.spec_from_file_location('cullinan.dynamic.' + os.path.basename(module_name), module_name)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                else:
                    return
            else:
                return
        except Exception:
            return

    if func in ('nobody', 'controller'):
        return

    try:
        fn = getattr(mod, func, None)
        if callable(fn):
            fn()
    except Exception:
        # swallow errors to keep scanning tolerant
        return


def file_list_func():
    """Discover candidate modules to import/reflect.

    Strategy (best-effort, in order):
      1. If the caller package can be determined, walk its package path via pkgutil.
      2. If running frozen (PyInstaller/Nuitka), try scanning the frozen app directory (sys._MEIPASS or executable dir).
      3. Fall back to walking the current working directory and returning dotted module names for any package modules found.

    The function returns a list of dotted module names when possible; in some frozen cases
    it may return filesystem paths to .py files which `reflect_module` can load as fallback.
    """
    # 1) try caller package discovery
    try:
        caller_pkg = get_caller_package()
        if caller_pkg:
            mods = list_submodules(caller_pkg)
            if mods:
                return mods
    except CallerPackageException:
        # ignore and continue to other strategies
        pass

    # 2) frozen applications (PyInstaller / Nuitka onefile)
    if getattr(sys, 'frozen', False):
        # PyInstaller: sys._MEIPASS contains extraction path
        base_dirs = []
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            base_dirs.append(meipass)
        # Nuitka compiled bundle may expose a __compiled__ object with containing_dir
        compiled = globals().get('__compiled__')
        if compiled is not None:
            containing = getattr(compiled, 'containing_dir', None)
            if containing:
                base_dirs.append(containing)
        # fallback to executable dir
        base_dirs.append(os.path.dirname(sys.executable))

        seen = set()
        modules = []
        for base in base_dirs:
            if not base or not os.path.isdir(base):
                continue
            for root, dirs, files in os.walk(base):
                if '__init__.py' not in files:
                    continue
                # compute dotted package prefix relative to base
                rel = os.path.relpath(root, base)
                if rel == '.':
                    prefix = ''
                else:
                    prefix = rel.replace(os.sep, '.') + '.'
                for f in files:
                    if f.endswith('.py') and f != '__init__.py':
                        modname = prefix + f[:-3]
                        if modname not in seen:
                            seen.add(modname)
                            modules.append(modname)
        if modules:
            return modules

    # 3) fallback: walk current working directory and convert package files to dotted names
    modules = []
    cwd = os.getcwd()
    for root, dirs, files in os.walk(cwd):
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

