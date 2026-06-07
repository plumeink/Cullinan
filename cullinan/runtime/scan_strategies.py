# -*- coding: utf-8 -*-
"""
Unified scan strategies for module discovery across packaging environments.

This module provides six independent, composable strategy functions for
discovering user modules. Each strategy follows a uniform signature:
    (config, mode) -> List[str]

Strategies are combined into pipelines (see scan_pipelines.py) that are
selected based on the detected packaging mode (Nuitka standalone/onefile,
PyInstaller onedir/onefile, or development).
"""

import importlib
import inspect
import os
import pkgutil
import sys
import logging
from typing import List, Optional, TYPE_CHECKING

from cullinan.support.exceptions import CallerPackageException

# Import shared helper from module_scanner to avoid duplication
from cullinan.runtime.module_scanner import _is_user_module_by_path

if TYPE_CHECKING:
    from cullinan.support.config import CullinanConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Strategy S0: explicit_modules
# ---------------------------------------------------------------------------

def strategy_explicit_modules(
    config: "CullinanConfig",
    _mode: Optional[str] = None,
    _base_dirs: Optional[List[str]] = None,
) -> List[str]:
    """Discover modules from the explicitly configured module list.

    When the user provides `explicit_modules` in configuration, this strategy
    imports each package, walks its subpackages via pkgutil, and also collects
    any already-imported submodules from sys.modules.

    This is the first strategy executed in every pipeline because explicit
    configuration takes highest priority.

    Args:
        config: Cullinan configuration instance.
        _mode: Unused; present for uniform strategy signature.
        _base_dirs: Unused; present for uniform strategy signature.

    Returns:
        List of dotted module names discovered, or empty list if
        ``explicit_modules`` is not configured.
    """
    if not config.explicit_modules:
        return []

    modules: List[str] = []
    logger.info(
        "S0 explicit_modules: using configured list: %s",
        config.explicit_modules,
    )

    for mod_name in config.explicit_modules:
        if mod_name not in modules:
            modules.append(mod_name)
        # Also collect already-imported submodules
        for sys_mod_name in sys.modules.keys():
            if sys_mod_name.startswith(mod_name + '.') and sys_mod_name not in modules:
                modules.append(sys_mod_name)

    # Walk subpackages for each explicitly listed module
    for mod_name in list(modules):
        try:
            pkg = importlib.import_module(mod_name)
            if hasattr(pkg, '__path__'):
                for _finder, name, _is_pkg in pkgutil.walk_packages(
                    pkg.__path__, mod_name + '.', onerror=lambda x: None
                ):
                    if name not in modules:
                        modules.append(name)
        except Exception as e:
            logger.debug("S0: could not walk subpackages of %s: %s", mod_name, e)

    logger.info("S0 explicit_modules: found %d modules", len(modules))
    return modules


# ---------------------------------------------------------------------------
# Strategy S1: user_packages
# ---------------------------------------------------------------------------

def strategy_user_packages(
    config: "CullinanConfig",
    _mode: Optional[str] = None,
    _base_dirs: Optional[List[str]] = None,
) -> List[str]:
    """Discover modules from the configured user_packages list.

    Imports each configured package and walks its subpackages via pkgutil.
    Falls back to searching sys.modules by prefix if import fails.

    Args:
        config: Cullinan configuration instance.
        _mode: Unused; present for uniform strategy signature.
        _base_dirs: Unused; present for uniform strategy signature.

    Returns:
        List of dotted module names discovered, or empty list if
        ``user_packages`` is not configured.
    """
    if not config.user_packages:
        return []

    modules: List[str] = []
    logger.info(
        "S1 user_packages: using configured packages: %s",
        config.user_packages,
    )

    for package_name in config.user_packages:
        try:
            pkg = importlib.import_module(package_name)
            logger.debug("S1: imported package: %s", package_name)

            if package_name not in modules:
                modules.append(package_name)

            if hasattr(pkg, '__path__'):
                for _finder, name, _is_pkg in pkgutil.walk_packages(
                    pkg.__path__, package_name + '.'
                ):
                    if name not in modules:
                        modules.append(name)
                        logger.debug("S1: found submodule: %s", name)

        except Exception as e:
            logger.warning(
                "S1: failed to import package %s: %s", package_name, str(e)
            )
            # Fallback: search sys.modules by prefix
            for mod_name in sys.modules.keys():
                if mod_name.startswith(package_name) and mod_name not in modules:
                    modules.append(mod_name)

    logger.info("S1 user_packages: found %d modules", len(modules))
    return modules


# ---------------------------------------------------------------------------
# Strategy S2: sys_modules_scan
# ---------------------------------------------------------------------------

def strategy_sys_modules_scan(
    config: "CullinanConfig",
    _mode: Optional[str] = None,
    _base_dirs: Optional[List[str]] = None,
) -> List[str]:
    """Auto-scan sys.modules for user modules using path-based heuristics.

    Only runs when ``auto_scan`` is enabled in configuration. Uses
    ``_is_user_module_by_path`` to filter out stdlib, site-packages, and
    framework modules.

    Args:
        config: Cullinan configuration instance.
        _mode: Unused; present for uniform strategy signature.
        _base_dirs: Unused; present for uniform strategy signature.

    Returns:
        List of dotted module names discovered.
    """
    if not config.auto_scan:
        return []

    modules: List[str] = []
    logger.info("S2 sys_modules_scan: scanning sys.modules (total: %d)", len(sys.modules))

    for mod_name in list(sys.modules.keys()):
        mod = sys.modules.get(mod_name)
        if mod and _is_user_module_by_path(mod_name, mod):
            logger.debug("S2: found user module: %s", mod_name)
            modules.append(mod_name)

    logger.info("S2 sys_modules_scan: found %d modules", len(modules))
    return modules


# ---------------------------------------------------------------------------
# Strategy S3: main_module_inference
# ---------------------------------------------------------------------------

def strategy_main_module_inference(
    config: "CullinanConfig",
    _mode: Optional[str] = None,
    _base_dirs: Optional[List[str]] = None,
) -> List[str]:
    """Infer the application package from ``__main__`` and scan its submodules.

    Walks up from ``__main__.__file__`` looking for ``__init__.py`` files to
    determine the package hierarchy, then imports the inferred package and
    walks its subpackages.

    Also ensures ``__main__`` itself is included if it has a ``__file__``
    attribute (so controllers defined at the top level are discovered).

    Args:
        config: Cullinan configuration instance (unused; kept for uniform
            signature).
        _mode: Unused; present for uniform strategy signature.
        _base_dirs: Unused; present for uniform strategy signature.

    Returns:
        List of dotted module names discovered.
    """
    modules: List[str] = []

    if '__main__' not in sys.modules:
        return modules

    main_mod = sys.modules['__main__']
    main_file = getattr(main_mod, '__file__', None)

    # Attempt package inference from __main__
    if main_file:
        main_file_abs = os.path.abspath(main_file)
        logger.debug("S3: __main__ file: %s", main_file_abs)

        current_dir = os.path.dirname(main_file_abs)
        package_parts: List[str] = []

        while os.path.exists(os.path.join(current_dir, '__init__.py')):
            package_parts.insert(0, os.path.basename(current_dir))
            current_dir = os.path.dirname(current_dir)

        if package_parts:
            package_name = '.'.join(package_parts)
            logger.info("S3: inferred package from __main__: %s", package_name)

            try:
                pkg = importlib.import_module(package_name)
                if hasattr(pkg, '__path__'):
                    for _finder, name, _is_pkg in pkgutil.walk_packages(
                        pkg.__path__, package_name + '.'
                    ):
                        if name not in modules:
                            modules.append(name)

                if package_name not in modules:
                    modules.append(package_name)
            except Exception as e:
                logger.warning(
                    "S3: failed to import inferred package %s: %s",
                    package_name, str(e),
                )

    # Ensure __main__ is included if it has a file (may contain controllers)
    if '__main__' not in modules:
        if hasattr(main_mod, '__file__'):
            logger.info("S3: adding __main__ module for scanning")
            modules.insert(0, '__main__')

    logger.info("S3 main_module_inference: found %d modules", len(modules))
    return modules


# ---------------------------------------------------------------------------
# Strategy S4: directory_scanning
# ---------------------------------------------------------------------------

def strategy_directory_scanning(
    config: "CullinanConfig",
    mode: Optional[str] = None,
    base_dirs: Optional[List[str]] = None,
) -> List[str]:
    """Scan filesystem directories for Python modules.

    Used in packaged environments (Nuitka standalone, PyInstaller onedir/onefile)
    where the executable directory or ``_MEIPASS`` contains the application
    files. Walks the directory tree, identifies ``.py``, ``.pyc``, ``.pyd``,
    and ``.so`` files, and converts relative paths to dotted module names.

    Args:
        config: Cullinan configuration instance (unused; kept for uniform
            signature).
        mode: Packaging mode hint (e.g., 'standalone', 'onedir', 'onefile').
        base_dirs: List of filesystem directories to scan. If empty or None,
            defaults to the executable directory.

    Returns:
        List of dotted module names discovered.
    """
    modules: List[str] = []

    if base_dirs is not None and len(base_dirs) == 0:
        return modules

    if not base_dirs:
        base_dirs = [os.path.dirname(sys.executable)]

    # Collect all entries: (rel_path_from_base, is_package, files_in_dir)
    entries_to_process: List[tuple] = []

    for base_dir in base_dirs:
        logger.info("S4 directory_scanning: scanning %s", base_dir)
        for root, dirs, files in os.walk(base_dir):
            # Exclude system directories
            dirs[:] = [
                d for d in dirs
                if not d.startswith('_')
                and d not in ['lib', 'bin', 'Lib', 'Library']
            ]

            is_package = any(
                f in files for f in ['__init__.py', '__init__.pyc', '__init__.pyi']
            )

            if is_package or any(
                f.endswith(('.py', '.pyc', '.pyd', '.so')) for f in files
            ):
                rel_path = os.path.relpath(root, base_dir)
                entries_to_process.append((rel_path, is_package, files))

    for rel_path, is_package, files in entries_to_process:
        if rel_path == '.':
            prefix = ''
        else:
            prefix = rel_path.replace(os.sep, '.')

            # Skip framework and system packages
            if any(
                prefix.startswith(p)
                for p in ['cullinan', 'tornado', 'certifi', '_']
            ):
                continue

        for f in files:
            full_mod: Optional[str] = None

            if f.endswith('.py') and f != '__init__.py':
                mod_name = f[:-3]
                full_mod = f"{prefix}.{mod_name}" if prefix else mod_name
            elif f.endswith('.pyc') and f != '__init__.pyc':
                mod_name = f[:-4]
                full_mod = f"{prefix}.{mod_name}" if prefix else mod_name
            elif f.endswith(('.pyd', '.so')):
                mod_name = f.split('.')[0]
                full_mod = f"{prefix}.{mod_name}" if prefix else mod_name

            if full_mod and full_mod not in modules and not full_mod.startswith('cullinan'):
                modules.append(full_mod)
                logger.debug("S4: found module: %s", full_mod)

        # Add package itself
        if is_package and prefix and not prefix.startswith('cullinan'):
            if prefix not in modules:
                modules.append(prefix)
                logger.debug("S4: found package: %s", prefix)

    logger.info("S4 directory_scanning: found %d modules", len(modules))
    return modules


# ---------------------------------------------------------------------------
# Strategy S5: onefile_dir_fallback
# ---------------------------------------------------------------------------

def strategy_onefile_dir_fallback(
    config: "CullinanConfig",
    _mode: Optional[str] = None,
    _base_dirs: Optional[List[str]] = None,
) -> List[str]:
    """Fallback discovery for onefile modes using ``dir(pkg)`` introspection.

    In onefile packaging (Nuitka onefile, PyInstaller onefile), the filesystem
    does not contain the original ``.py`` files, so S4 directory scanning is
    ineffective. This strategy uses ``get_caller_package()`` to infer the
    application package, then iterates ``dir(pkg)`` to find submodule
    attributes.

    This is a best-effort fallback — the onefile pipeline should prefer
    ``explicit_modules`` or ``user_packages`` for reliable results.

    Args:
        config: Cullinan configuration instance (unused; kept for uniform
            signature).
        _mode: Unused; present for uniform strategy signature.
        _base_dirs: Unused; present for uniform strategy signature.

    Returns:
        List of dotted module names discovered via introspection.
    """
    modules: List[str] = []

    try:
        caller_pkg = _resolve_caller_package()
        if caller_pkg:
            logger.info("S5 onefile_dir_fallback: inferred package: %s", caller_pkg)
            try:
                pkg = importlib.import_module(caller_pkg)
                for attr_name in dir(pkg):
                    if not attr_name.startswith('_'):
                        attr = getattr(pkg, attr_name, None)
                        if inspect.ismodule(attr):
                            mod_name = getattr(attr, '__name__', None)
                            if mod_name and mod_name not in modules:
                                modules.append(mod_name)
            except Exception as e:
                logger.debug("S5: failed to import package %s: %s", caller_pkg, e)
    except CallerPackageException:
        pass

    logger.info("S5 onefile_dir_fallback: found %d modules", len(modules))
    return modules


def _resolve_caller_package() -> Optional[str]:
    """Resolve the caller package using ``sys._getframe``.

    Walks up the call stack to find the first frame whose globals define a
    ``__package__`` that does not belong to the Cullinan framework.
    """
    from cullinan.runtime.module_scanner import get_caller_package
    try:
        return get_caller_package()
    except CallerPackageException:
        return None
