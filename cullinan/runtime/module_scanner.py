# -*- coding: utf-8 -*-
"""Module scanning and discovery for different packaging environments.

This module provides utilities to discover and import Python modules across
different deployment scenarios:
- Development environment (direct Python execution)
- Nuitka compiled/packaged applications
- PyInstaller frozen applications

Extracted from application.py for better maintainability and separation of concerns.
"""

import importlib
import inspect
import os
import pkgutil
import sys
import logging
from typing import List, Optional
from cullinan.support.exceptions import CallerPackageException

# Import packaging-aware path utilities
from cullinan.support.path_utils import (
    is_pyinstaller_frozen,
    is_nuitka_compiled,
)

# Import scan statistics utilities
from cullinan.runtime.scan_stats import (
    get_scan_stats_collector,
    log_scan_statistics,
    ScanPhase,
)

logger = logging.getLogger(__name__)

# Module scanning result cache (to avoid duplicate scanning)
_module_list_cache: Optional[List[str]] = None
_cache_lock = None


def _get_cache_lock():
    """Get or create the cache lock (lazy initialization for thread safety)."""
    global _cache_lock
    if _cache_lock is None:
        import threading
        _cache_lock = threading.Lock()
    return _cache_lock


def invalidate_module_cache() -> None:
    """Clear the module scan cache to force re-discovery on the next file_list_func() call.

    Thread-safe: uses the same lock as cache population for consistency.
    Useful when:
    - Dynamically imported new modules in tests need re-scanning
    - Plugins are hot-loaded and the framework needs to discover new components
    """
    global _module_list_cache
    lock = _get_cache_lock()
    with lock:
        _module_list_cache = None
        logger.debug("Module cache invalidated, next scan will re-discover")


def get_nuitka_standalone_mode() -> Optional[str]:
    """Detect Nuitka packaging mode.
    
    Returns:
        str: 'onefile', 'standalone', or None if not Nuitka compiled
    """
    if not is_nuitka_compiled():
        return None
    
    # Nuitka onefile mode characteristics:
    # 1. sys.frozen is True
    # 2. Executable extracts to temporary directory
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        # onefile mode typically runs in temp directory with random characters
        if 'onefile' in exe_dir.lower() or 'temp' in exe_dir.lower() or '_MEI' in exe_dir:
            return 'onefile'
        return 'standalone'
    
    return None


def get_pyinstaller_mode() -> Optional[str]:
    """Detect PyInstaller packaging mode.
    
    Returns:
        str: 'onefile', 'onedir', or None if not PyInstaller frozen
    """
    if not is_pyinstaller_frozen():
        return None
    
    # PyInstaller onefile mode sets sys._MEIPASS
    if hasattr(sys, '_MEIPASS'):
        meipass = sys._MEIPASS
        # Check if _MEIPASS is in temporary directory (onefile characteristic)
        if '_MEI' in meipass or 'Temp' in meipass or 'tmp' in meipass:
            return 'onefile'
        return 'onedir'
    
    return None


def get_caller_package(fallback_package: Optional[str] = None) -> str:
    """Get the caller package name for the importing application.
    
    Walk the stack and find the first frame whose module is not part of
    the `cullinan` package. Prefer module.__package__ if available, otherwise
    derive a dotted package name from the filename relative to CWD.
    
    Args:
        fallback_package: Optional package name to return if stack inspection fails.
    
    Returns:
        str: The top-level package name of the caller
        
    Raises:
        CallerPackageException: If caller package cannot be determined and no fallback
    """
    cwd = os.getcwd()
    
    # Primary: use sys._getframe() for efficiency (works in Nuitka/PyInstaller)
    try:
        frame = sys._getframe(1)  # caller's frame
        while frame is not None:
            module = inspect.getmodule(frame)
            if module is not None:
                mod_name = getattr(module, '__name__', '')
                if mod_name and not mod_name.startswith('cullinan'):
                    pkg = getattr(module, '__package__', None)
                    if pkg:
                        return pkg.split('.')[0]
                    try:
                        frame_file = getattr(frame, 'f_code', None)
                        if frame_file is not None:
                            filename = getattr(frame_file, 'co_filename', '')
                            rel = os.path.relpath(filename, cwd)
                            pkg_from_path = os.path.dirname(rel).replace(os.sep, '.')
                            if pkg_from_path and pkg_from_path != '.':
                                return pkg_from_path
                    except Exception:
                        pass
            frame = frame.f_back
    except Exception:
        pass
    
    # Fallback: use inspect.stack() for backward compatibility
    stack = inspect.stack()
    
    for frame_info in stack:
        module = inspect.getmodule(frame_info[0])
        if not module:
            continue
        
        mod_name = getattr(module, '__name__', '')
        if mod_name and mod_name.startswith('cullinan'):
            continue
        
        pkg = getattr(module, '__package__', None)
        if pkg:
            # Return top-level package
            return pkg.split('.')[0]
        
        # Derive from filename
        try:
            rel = os.path.relpath(frame_info.filename, cwd)
            pkg_from_path = os.path.dirname(rel).replace(os.sep, '.')
            if pkg_from_path == '.':
                pkg_from_path = ''
            return pkg_from_path
        except Exception:
            continue
    
    if fallback_package is not None:
        return fallback_package
    raise CallerPackageException()


def _is_user_module_by_path(mod_name: str, mod) -> bool:
    """Check if a module is user code (not stdlib or third-party).
    
    Args:
        mod_name: Module name
        mod: Module object
        
    Returns:
        bool: True if module is user code
    """
    # Exclude framework itself
    if mod_name.startswith('cullinan'):
        return False
    
    # Exclude built-in modules
    if mod_name.startswith('_'):
        return False
    
    # Check module file path
    mod_file = getattr(mod, '__file__', None)
    if not mod_file:
        return False
    
    # Normalize path separators for cross-platform compatibility
    mod_file_normalized = mod_file.replace('\\', '/').replace('//', '/')

    # Exclude site-packages (third-party libraries)
    if 'site-packages' in mod_file_normalized:
        return False
    
    # Exclude standard library (typically in lib/python3.x/)
    # Check both Unix-style and Windows-style paths
    if '/lib/python' in mod_file_normalized or '\\lib\\python' in mod_file:
        return False

    # Also check for Python installation patterns
    if '/usr/lib/python' in mod_file_normalized:
        return False
    
    # Exclude packaging tools
    if 'nuitka' in mod_file.lower() or 'pyinstaller' in mod_file.lower():
        return False
    
    # Exclude system paths
    system_paths = [
        os.path.join(sys.prefix, 'lib'),
        os.path.join(sys.prefix, 'Lib'),  # Windows
    ]
    for sys_path in system_paths:
        if mod_file.startswith(sys_path):
            return False
    
    return True


# scan_modules_nuitka() and scan_modules_pyinstaller() have been replaced
# by the unified pipeline architecture in scan_strategies.py + scan_pipelines.py.
# See: scan_pipelines.execute_pipeline() for the routing logic.


def list_submodules(package_name: str) -> List[str]:
    """List all submodules within a package.
    
    Uses both pkgutil.walk_packages (primary) and filesystem scanning
    (fallback) to ensure deep subpackages are discovered across different
    Python versions and packaging modes.
    
    Args:
        package_name: Dotted package name to scan
        
    Returns:
        List[str]: List of module names within the package
    """
    modules = []
    try:
        pkg = importlib.import_module(package_name)
    except ImportError as e:
        logger.warning("Could not import package %s: %s", package_name, str(e))
        return modules
    
    # Strategy 1: pkgutil.walk_packages (primary)
    if hasattr(pkg, '__path__'):
        for importer, modname, ispkg in pkgutil.walk_packages(
            path=pkg.__path__,
            prefix=pkg.__name__ + '.',
            onerror=lambda x: None
        ):
            if modname not in modules:
                modules.append(modname)
    
    # Strategy 2: Filesystem fallback for deep subpackages
    # pkgutil.walk_packages may skip deeply nested subpackages on some
    # Python versions or packaging modes. Walk the filesystem directly.
    try:
        pkg_paths = pkg.__path__ if hasattr(pkg, '__path__') else []
        for pkg_path in pkg_paths:
            _fs_walk_submodules(package_name, pkg_path, modules)
    except Exception as e:
        logger.debug("Filesystem fallback for %s failed: %s", package_name, e)
    
    return modules


def _fs_walk_submodules(package_prefix: str, directory: str, modules: List[str], _depth: int = 0) -> None:
    """Recursively walk filesystem to discover submodules not found by pkgutil.
    
    Args:
        package_prefix: Dotted package name prefix
        directory: Filesystem directory to scan
        modules: List to append discovered module names to (mutated in-place)
        _depth: Current recursion depth (internal use, max 10)
    """
    import os as _os
    
    if _depth > 10:
        return
    
    try:
        entries = _os.listdir(directory)
    except OSError:
        return
    
    for entry in sorted(entries):
        full_path = _os.path.join(directory, entry)
        
        if entry.startswith('.') or entry.startswith('__pycache__'):
            continue
        
        if _os.path.isdir(full_path):
            init_file = _os.path.join(full_path, '__init__.py')
            child_pkg = package_prefix + '.' + entry
            if _os.path.isfile(init_file):
                # Regular package
                if child_pkg not in modules:
                    modules.append(child_pkg)
                _fs_walk_submodules(child_pkg, full_path, modules, _depth + 1)
            else:
                # Namespace package or plain directory — still worth scanning
                _fs_walk_submodules(child_pkg, full_path, modules, _depth + 1)
        
        elif entry.endswith('.py') and not entry.startswith('__'):
            mod_name = package_prefix + '.' + entry[:-3]  # strip .py
            if mod_name not in modules:
                modules.append(mod_name)


def file_list_func() -> List[str]:
    """Discover candidate modules to import/reflect.

    Routes to the unified scan pipeline (scan_pipelines) which selects the
    correct strategy chain based on the detected environment:
    - onefile / standalone / onedir for Nuitka
    - onefile / onedir for PyInstaller
    - development environment (caller-package → cwd scan)

    Results are cached to avoid duplicate scanning overhead.

    Returns:
        List[str]: List of dotted module names
    """
    import time

    global _module_list_cache

    # Check cache first (fast path)
    if _module_list_cache is not None:
        logger.debug("Using cached module list (%d modules)", len(_module_list_cache))
        # Record cache hit
        stats_collector = get_scan_stats_collector()
        stats_collector.record_modules_cached(len(_module_list_cache))
        return _module_list_cache

    # Thread-safe cache check and population
    lock = _get_cache_lock()
    with lock:
        # Double-check pattern: another thread might have populated the cache
        if _module_list_cache is not None:
            logger.debug("Using cached module list (%d modules)", len(_module_list_cache))
            return _module_list_cache

        # Determine packaging mode
        from cullinan.support.path_utils import get_packaging_mode
        packaging_mode = get_packaging_mode()

        # Initialize statistics collection
        stats_collector = get_scan_stats_collector()

        # Perform actual scanning with performance measurement
        logger.info("Starting module discovery...")
        start_time = time.perf_counter()

        # Start statistics collection
        stats_collector.start_scan(scan_mode="auto", packaging_mode=packaging_mode)

        # Discovery phase
        stats_collector.start_phase(ScanPhase.DISCOVERY)
        modules = _do_module_discovery()
        stats_collector.end_phase(ScanPhase.DISCOVERY)

        elapsed = time.perf_counter() - start_time
        elapsed_ms = elapsed * 1000

        # Cache the results
        stats_collector.start_phase(ScanPhase.CACHING)
        _module_list_cache = modules
        stats_collector.end_phase(ScanPhase.CACHING)

        # Record statistics
        stats_collector.record_modules_found(len(modules))
        stats = stats_collector.end_scan(elapsed_ms)

        # Log performance metrics with statistics
        log_scan_statistics(stats, level="info" if elapsed_ms < 1000 else "warning")

        return modules


def _do_module_discovery() -> List[str]:
    """Internal function that performs the actual module discovery.

    Separated from file_list_func() to enable caching.

    Returns:
        List[str]: List of dotted module names
    """
    from cullinan.support.path_utils import get_packaging_mode
    from cullinan.runtime.scan_pipelines import execute_pipeline

    packaging_mode = get_packaging_mode()

    # Packaged environments: use unified strategy pipeline
    if packaging_mode and packaging_mode != "development":
        from cullinan.support.config import get_config
        config = get_config()
        logger.info("=== Using pipeline scanning: %s ===", packaging_mode)
        modules = execute_pipeline(config, packaging_mode)
        if modules:
            logger.info("Pipeline discovered %d modules", len(modules))
            return modules

    # Development environment: scan via caller package
    logger.info("=== Using development environment scanning ===")
    try:
        caller_pkg = get_caller_package()
        if caller_pkg:
            logger.info("Caller package: %s", caller_pkg)
            mods = list_submodules(caller_pkg)
            if mods:
                logger.info("Discovered %d modules via package scanning", len(mods))
                return mods
    except CallerPackageException:
        logger.debug("Could not determine caller package")
        pass

    # Strategy 3: Fallback - scan current working directory
    logger.info("=== Fallback: scanning current working directory ===")
    modules = []
    cwd = os.getcwd()
    logger.info("Scanning directory: %s", cwd)

    for root, dirs, files in os.walk(cwd):
        # Exclude hidden directories and virtual environments
        dirs[:] = [d for d in dirs if not d.startswith('.') and
                  d not in ['venv', 'env', '__pycache__', 'build', 'dist']]

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

    logger.info("Discovered %d modules via directory scanning", len(modules))
    return modules
