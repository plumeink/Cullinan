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
from cullinan.exceptions import CallerPackageException

# Import packaging-aware path utilities
from cullinan.path_utils import (
    is_pyinstaller_frozen,
    is_nuitka_compiled,
)

# Import scan statistics utilities
from cullinan.scan_stats import (
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


def get_caller_package() -> str:
    """Get the caller package name for the importing application.
    
    Walk the stack and find the first frame whose module is not part of
    the `cullinan` package. Prefer module.__package__ if available, otherwise
    derive a dotted package name from the filename relative to CWD.
    
    Returns:
        str: The top-level package name of the caller
        
    Raises:
        CallerPackageException: If caller package cannot be determined
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


def scan_modules_nuitka() -> List[str]:
    """Scan for modules in Nuitka compiled environment.
    
    Uses multiple strategies to discover user modules:
    1. Configured user_packages (recommended, from config)
    2. Smart detection from sys.modules
    3. Inference from __main__ module
    4. Directory scanning of executable location
    
    Returns:
        List[str]: List of discovered module names (dotted strings)
    """
    logger.info("Detected Nuitka compiled environment")
    
    mode = get_nuitka_standalone_mode()
    logger.info("Nuitka mode: %s", mode or "unknown")
    
    modules = []
    
    # Get configuration
    from cullinan.config import get_config
    config = get_config()
    
    # Strategy 1: Use configured user packages (recommended)
    if config.user_packages:
        logger.info("Using configured user packages: %s", config.user_packages)
        
        for package_name in config.user_packages:
            try:
                # Import package
                pkg = importlib.import_module(package_name)
                logger.debug("Imported package: %s", package_name)
                
                # Add package itself
                if package_name not in modules:
                    modules.append(package_name)
                
                # Scan all submodules in package
                if hasattr(pkg, '__path__'):
                    for finder, name, is_pkg in pkgutil.walk_packages(pkg.__path__, package_name + '.'):
                        if name not in modules:
                            modules.append(name)
                            logger.debug("Found submodule: %s", name)
            
            except Exception as e:
                logger.warning("Failed to import package %s: %s", package_name, str(e))
                
                # Fallback: search in sys.modules
                for mod_name in sys.modules.keys():
                    if mod_name.startswith(package_name):
                        if mod_name not in modules:
                            modules.append(mod_name)
        
        logger.info("Found %d modules from configured packages", len(modules))
        
        # If configured packages found modules, return early
        if modules:
            return modules
    
    # Strategy 2: Auto-scan if no configured packages or no modules found
    if config.auto_scan:
        logger.info("No user packages configured or no modules found, using smart detection")
        logger.debug("Scanning sys.modules (total: %d)", len(sys.modules))
        
        for mod_name in list(sys.modules.keys()):
            mod = sys.modules.get(mod_name)
            if mod and _is_user_module_by_path(mod_name, mod):
                logger.debug("Found potential user module: %s", mod_name)
                modules.append(mod_name)
        
        logger.info("Found %d user modules in sys.modules", len(modules))
    
    # Strategy 3: Infer from __main__ module and scan its package
    if '__main__' in sys.modules and len(modules) == 0:
        main_mod = sys.modules['__main__']
        main_file = getattr(main_mod, '__file__', None)
        
        if main_file:
            main_file_abs = os.path.abspath(main_file)
            logger.debug("__main__ file: %s", main_file_abs)
            
            # Find package root by looking for __init__.py
            current_dir = os.path.dirname(main_file_abs)
            package_parts = []
            
            # Walk up directory tree until no __init__.py found
            while os.path.exists(os.path.join(current_dir, '__init__.py')):
                package_parts.insert(0, os.path.basename(current_dir))
                current_dir = os.path.dirname(current_dir)
            
            if package_parts:
                package_name = '.'.join(package_parts)
                logger.info("Inferred package from __main__: %s", package_name)
                
                try:
                    pkg = importlib.import_module(package_name)
                    logger.debug("Successfully imported package: %s", package_name)
                    
                    # Scan all modules in package
                    if hasattr(pkg, '__path__'):
                        for finder, name, is_pkg in pkgutil.walk_packages(pkg.__path__, package_name + '.'):
                            if name not in modules:
                                modules.append(name)
                                logger.debug("Found submodule: %s", name)
                    
                    # Add package itself
                    if package_name not in modules:
                        modules.append(package_name)
                    
                    logger.info("Added %d modules from inferred package", len(modules))
                except Exception as e:
                    logger.warning("Failed to import inferred package %s: %s", package_name, str(e))
    
    # Ensure __main__ module is included if it has controllers
    if '__main__' in sys.modules and '__main__' not in modules:
        main_mod = sys.modules['__main__']
        if hasattr(main_mod, '__file__'):
            logger.info("Adding __main__ module for scanning")
            modules.insert(0, '__main__')  # Process main module first
    
    # Strategy 4: Directory scanning from executable location
    if len(modules) <= 1:  # Only __main__ or no modules
        exe_dir = os.path.dirname(sys.executable)
        logger.info("Scanning Nuitka directory for Python modules: %s", exe_dir)
        
        scanned_modules = []
        
        for root, dirs, files in os.walk(exe_dir):
            # Exclude system directories
            dirs[:] = [d for d in dirs if not d.startswith('_') and d not in ['lib', 'bin', 'Lib']]
            
            # Check if directory is a Python package
            is_package = any(f in files for f in ['__init__.py', '__init__.pyc', '__init__.pyi'])
            
            if is_package or any(f.endswith(('.py', '.pyc', '.pyd', '.so')) for f in files):
                rel_path = os.path.relpath(root, exe_dir)
                
                if rel_path == '.':
                    prefix = ''
                else:
                    prefix = rel_path.replace(os.sep, '.')
                    
                    # Skip system packages and framework packages
                    if any(prefix.startswith(p) for p in ['cullinan', 'tornado', 'certifi', '_']):
                        continue
                
                # Scan Python files in directory
                for f in files:
                    if f.endswith('.py') and f != '__init__.py':
                        mod_name = f[:-3]
                        full_mod = f"{prefix}.{mod_name}" if prefix else mod_name
                        
                        if full_mod not in scanned_modules and not full_mod.startswith('cullinan'):
                            scanned_modules.append(full_mod)
                            logger.debug("Found Python file: %s -> module: %s", f, full_mod)
                    
                    elif f.endswith('.pyc') and f != '__init__.pyc':
                        mod_name = f[:-4]
                        full_mod = f"{prefix}.{mod_name}" if prefix else mod_name
                        
                        if full_mod not in scanned_modules and not full_mod.startswith('cullinan'):
                            scanned_modules.append(full_mod)
                            logger.debug("Found compiled file: %s -> module: %s", f, full_mod)
                    
                    elif f.endswith(('.pyd', '.so')):
                        mod_name = f.split('.')[0]
                        full_mod = f"{prefix}.{mod_name}" if prefix else mod_name
                        
                        if full_mod not in scanned_modules and not full_mod.startswith('cullinan'):
                            scanned_modules.append(full_mod)
                            logger.debug("Found extension: %s -> module: %s", f, full_mod)
                
                # Add package itself if it's a package
                if is_package and prefix and not prefix.startswith('cullinan'):
                    if prefix not in scanned_modules:
                        scanned_modules.append(prefix)
                        logger.debug("Found package: %s", prefix)
        
        if scanned_modules:
            logger.info("Found %d modules via directory scanning", len(scanned_modules))
            for mod in scanned_modules:
                if mod not in modules:
                    modules.append(mod)
    
    # Strategy 5: Onefile mode - try to infer from call stack
    if mode == 'onefile' and not modules:
        try:
            caller_pkg = get_caller_package()
            if caller_pkg:
                logger.info("Inferred package: %s", caller_pkg)
                try:
                    pkg = importlib.import_module(caller_pkg)
                    # Iterate through package attributes
                    for attr_name in dir(pkg):
                        if not attr_name.startswith('_'):
                            attr = getattr(pkg, attr_name, None)
                            if inspect.ismodule(attr):
                                mod_name = getattr(attr, '__name__', None)
                                if mod_name and mod_name not in modules:
                                    modules.append(mod_name)
                except Exception as e:
                    logger.debug("Failed to import package %s: %s", caller_pkg, e)
        except CallerPackageException:
            pass
    
    logger.info("Found %d modules via Nuitka scanning", len(modules))
    logger.info("Total discovered modules: %d", len(modules))
    if not modules:
        logger.warning("[WARN] No modules discovered! Consider configuring user_packages.")
        logger.warning("[WARN] Example: cullinan.configure(user_packages=['your_app'])")

    return modules


def scan_modules_pyinstaller() -> List[str]:
    """Scan for modules in PyInstaller frozen environment.
    
    Uses multiple strategies to discover user modules:
    1. Configured user_packages (recommended, from config)
    2. Directory scanning (_MEIPASS and executable location)
    3. Smart detection from sys.modules
    
    Returns:
        List[str]: List of discovered module names (dotted strings)
    """
    logger.info("Detected PyInstaller frozen environment")
    
    mode = get_pyinstaller_mode()
    logger.info("PyInstaller mode: %s", mode or "unknown")
    
    modules = []
    
    # Get configuration
    from cullinan.config import get_config
    config = get_config()
    
    # Strategy 1: Use configured user packages (recommended)
    if config.user_packages:
        logger.info("Using configured user packages: %s", config.user_packages)
        
        for package_name in config.user_packages:
            try:
                pkg = importlib.import_module(package_name)
                logger.debug("Imported package: %s", package_name)
                
                if package_name not in modules:
                    modules.append(package_name)
                
                if hasattr(pkg, '__path__'):
                    for finder, name, is_pkg in pkgutil.walk_packages(pkg.__path__, package_name + '.'):
                        if name not in modules:
                            modules.append(name)
                            logger.debug("Found submodule: %s", name)
            
            except Exception as e:
                logger.warning("Failed to import package %s: %s", package_name, str(e))
                
                # Fallback: search in sys.modules
                for mod_name in sys.modules.keys():
                    if mod_name.startswith(package_name):
                        if mod_name not in modules:
                            modules.append(mod_name)
        
        logger.info("Found %d modules from configured packages", len(modules))
        
        if modules:
            return modules
    
    # Strategy 2: Auto-scan if no configured packages or no modules found
    if config.auto_scan:
        logger.info("No user packages configured or no modules found, using directory scanning")
        
        base_dirs = []
        
        # Get PyInstaller temporary extraction directory
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            base_dirs.append(meipass)
            logger.info("PyInstaller _MEIPASS: %s", meipass)
        
        # Check executable directory (onedir mode)
        if mode == 'onedir':
            exe_dir = os.path.dirname(sys.executable)
            if exe_dir not in base_dirs:
                base_dirs.append(exe_dir)
                logger.info("Executable directory: %s", exe_dir)
        
        # Scan base directories for user modules
        for base_dir in base_dirs:
            for root, dirs, files in os.walk(base_dir):
                # Exclude system directories
                dirs[:] = [d for d in dirs if not d.startswith('_') and 
                          d not in ['lib', 'bin', 'Lib', 'Library']]
                
                # Check if directory is a Python package
                is_package = any(f in files for f in ['__init__.py', '__init__.pyc'])
                
                if is_package or any(f.endswith(('.py', '.pyc', '.pyd')) for f in files):
                    rel_path = os.path.relpath(root, base_dir)
                    
                    if rel_path == '.':
                        prefix = ''
                    else:
                        prefix = rel_path.replace(os.sep, '.')
                        
                        # Skip framework and system packages
                        if any(prefix.startswith(p) for p in ['cullinan', 'tornado', 'certifi', '_']):
                            continue
                    
                    # Scan Python files
                    for f in files:
                        if f.endswith('.py') and f != '__init__.py':
                            mod_name = f[:-3]
                            full_mod = f"{prefix}.{mod_name}" if prefix else mod_name
                            
                            if full_mod not in modules and not full_mod.startswith('cullinan'):
                                modules.append(full_mod)
                                logger.debug("Found module: %s", full_mod)
                        
                        elif f.endswith('.pyc') and f != '__init__.pyc':
                            mod_name = f[:-4]
                            full_mod = f"{prefix}.{mod_name}" if prefix else mod_name
                            
                            if full_mod not in modules and not full_mod.startswith('cullinan'):
                                modules.append(full_mod)
                                logger.debug("Found compiled module: %s", full_mod)
                    
                    # Add package itself
                    if is_package and prefix and not prefix.startswith('cullinan'):
                        if prefix not in modules:
                            modules.append(prefix)
                            logger.debug("Found package: %s", prefix)
        
        logger.info("Found %d modules via directory scanning", len(modules))
        
        # If directory scanning found modules, return
        if modules:
            return modules
        
        # Fallback: scan sys.modules
        logger.info("No modules from directory scan, checking sys.modules")
        
        for mod_name in list(sys.modules.keys()):
            mod = sys.modules.get(mod_name)
            if mod and _is_user_module_by_path(mod_name, mod):
                logger.debug("Found user module in sys.modules: %s", mod_name)
                modules.append(mod_name)
        
        logger.info("Found %d user modules in sys.modules", len(modules))
    
    logger.info("Total discovered modules: %d", len(modules))
    if not modules:
        logger.warning("[WARN] No modules discovered! Consider configuring user_packages.")
        logger.warning("[WARN] Example: cullinan.configure(user_packages=['your_app'])")

    return modules


def list_submodules(package_name: str) -> List[str]:
    """List all submodules within a package.
    
    Args:
        package_name: Dotted package name to scan
        
    Returns:
        List[str]: List of module names within the package
    """
    modules = []
    try:
        pkg = importlib.import_module(package_name)
        if hasattr(pkg, '__path__'):
            for importer, modname, ispkg in pkgutil.walk_packages(
                path=pkg.__path__,
                prefix=pkg.__name__ + '.',
                onerror=lambda x: None
            ):
                modules.append(modname)
    except ImportError as e:
        logger.warning("Could not import package %s: %s", package_name, str(e))
    
    return modules


def file_list_func() -> List[str]:
    """Discover candidate modules to import/reflect.
    
    Uses multiple strategies in order of priority:
    1. Detect packaging environment (Nuitka or PyInstaller)
       - If Nuitka, use scan_modules_nuitka()
       - If PyInstaller, use scan_modules_pyinstaller()
    2. Try caller package scanning (development environment)
    3. Fallback to current working directory scan
    
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
        from cullinan.path_utils import get_packaging_mode
        packaging_mode = get_packaging_mode()

        # Check for explicit registration mode (skip scanning)
        from cullinan.config import get_config
        config = get_config()

        # Initialize statistics collection
        stats_collector = get_scan_stats_collector()

        if config.explicit_services or config.explicit_controllers:
            stats_collector.start_scan(scan_mode="explicit", packaging_mode=packaging_mode)
            logger.info(
                "Explicit registration mode enabled: skipping module scanning. "
                "Services: %d, Controllers: %d",
                len(config.explicit_services) if config.explicit_services else 0,
                len(config.explicit_controllers) if config.explicit_controllers else 0
            )
            # Return empty list to skip scanning
            _module_list_cache = []
            stats = stats_collector.end_scan(0.0)
            log_scan_statistics(stats, level="info")
            return _module_list_cache

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
    # Strategy 1: Detect packaging environment and use specialized scanning
    # Note: Nuitka detection first, as it may also set sys.frozen
    if is_nuitka_compiled():
        logger.info("=== Using Nuitka scanning strategy ===")
        modules = scan_modules_nuitka()
        if modules:
            logger.info("Discovered %d modules", len(modules))
            return modules
    elif is_pyinstaller_frozen():
        logger.info("=== Using PyInstaller scanning strategy ===")
        modules = scan_modules_pyinstaller()
        if modules:
            logger.info("Discovered %d modules", len(modules))
            return modules
    
    # Strategy 2: Development environment - scan via caller package
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
