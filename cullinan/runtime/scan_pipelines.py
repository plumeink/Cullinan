# -*- coding: utf-8 -*-
"""
Pipeline definitions that compose scan strategies for each packaging mode.

Each pipeline is a list of (strategy_name, strategy_callable) tuples that
execute in order. A pipeline stops when one strategy returns a non-empty
module list (early-termination semantics) unless ``exhaustive`` is set.

Pipeline routing is handled by ``execute_pipeline()`` which selects the
appropriate pipeline based on the return value of ``get_packaging_mode()``.
"""

import sys
import logging
from typing import List, Optional, Callable, Dict

from cullinan.runtime.scan_strategies import (
    strategy_explicit_modules,
    strategy_user_packages,
    strategy_sys_modules_scan,
    strategy_main_module_inference,
    strategy_directory_scanning,
    strategy_onefile_dir_fallback,
)

if True:  # TYPE_CHECKING guard – always import at runtime
    from cullinan.support.config import CullinanConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Strategy type alias
# ---------------------------------------------------------------------------

# A strategy callable:
#   (config, mode, base_dirs) -> List[str]
StrategyFunc = Callable[
    [CullinanConfig, Optional[str], Optional[List[str]]],
    List[str],
]

# A pipeline is a list of (label, callable) tuples
Pipeline = List[tuple]

# ---------------------------------------------------------------------------
# Pipeline definitions
# ---------------------------------------------------------------------------

def _build_nuitka_standalone_pipeline() -> Pipeline:
    """Nuitka standalone mode (--standalone).

    Strategies: S0 → S1 → S2 → S3 → S4
    - S0 (explicit_modules): user-provided explicit list
    - S1 (user_packages): user-configured packages
    - S2 (sys_modules_scan): auto-scan sys.modules
    - S3 (main_module_inference): infer from __main__
    - S4 (directory_scanning): walk executable directory
    """
    return [
        ("S0_explicit_modules", strategy_explicit_modules),
        ("S1_user_packages", strategy_user_packages),
        ("S2_sys_modules_scan", strategy_sys_modules_scan),
        ("S3_main_module_inference", strategy_main_module_inference),
        ("S4_directory_scanning", strategy_directory_scanning),
    ]


def _build_nuitka_onefile_pipeline() -> Pipeline:
    """Nuitka onefile mode (--onefile).

    Strategies: S0 → S1 → S2 → S3 → S5
    S4 (directory scanning) is skipped because onefile extracts to a temp
    directory that does not reliably contain source files.  S5 uses recursive
    ``dir(pkg)`` introspection and ``sys.modules`` prefix scanning as a
    best-effort fallback that now catches deeply nested subpackages.
    """
    return [
        ("S0_explicit_modules", strategy_explicit_modules),
        ("S1_user_packages", strategy_user_packages),
        ("S2_sys_modules_scan", strategy_sys_modules_scan),
        ("S3_main_module_inference", strategy_main_module_inference),
        ("S5_onefile_dir_fallback", strategy_onefile_dir_fallback),
    ]


def _build_pyinstaller_onedir_pipeline() -> Pipeline:
    """PyInstaller onedir mode.

    Strategies: S0 → S1 → S4
    Directory scanning (S4) is effective in onedir mode as all files are
    unpacked alongside the executable.
    """
    return [
        ("S0_explicit_modules", strategy_explicit_modules),
        ("S1_user_packages", strategy_user_packages),
        ("S4_directory_scanning", strategy_directory_scanning),
    ]


def _build_pyinstaller_onefile_pipeline() -> Pipeline:
    """PyInstaller onefile mode.

    Strategies: S0 → S1 → S4
    PyInstaller onefile uses ``_MEIPASS`` (a temp extraction directory) so
    filesystem scanning via S4 remains effective — unlike Nuitka onefile.
    """
    return [
        ("S0_explicit_modules", strategy_explicit_modules),
        ("S1_user_packages", strategy_user_packages),
        ("S4_directory_scanning", strategy_directory_scanning),
    ]


def _build_development_pipeline() -> Pipeline:
    """Development environment (direct Python).

    Strategies: S0 → S1 → S2 → S3
    No filesystem scanning; relies on package imports and sys.modules.
    """
    return [
        ("S0_explicit_modules", strategy_explicit_modules),
        ("S1_user_packages", strategy_user_packages),
        ("S2_sys_modules_scan", strategy_sys_modules_scan),
        ("S3_main_module_inference", strategy_main_module_inference),
    ]


# ---------------------------------------------------------------------------
# Pipeline registry
# ---------------------------------------------------------------------------

PIPELINE_REGISTRY: Dict[str, Pipeline] = {
    "nuitka-standalone": _build_nuitka_standalone_pipeline(),
    "nuitka-onefile": _build_nuitka_onefile_pipeline(),
    "pyinstaller-onedir": _build_pyinstaller_onedir_pipeline(),
    "pyinstaller-onefile": _build_pyinstaller_onefile_pipeline(),
    "development": _build_development_pipeline(),
}

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

def execute_pipeline(
    config: CullinanConfig,
    packaging_mode: Optional[str] = None,
    base_dirs: Optional[List[str]] = None,
    early_termination: bool = True,
) -> List[str]:
    """Execute the strategy pipeline for the given packaging mode.

    Selects the appropriate pipeline from ``PIPELINE_REGISTRY`` and executes
    each strategy in order.  By default, stops at the first strategy that
    returns a non-empty result (early termination).

    Args:
        config: Cullinan configuration instance.
        packaging_mode: Override packaging mode. If None, auto-detected via
            ``get_packaging_mode()``.
        base_dirs: List of directories to scan (for S4 strategy). If None,
            auto-populated based on the detected packaging mode.
        early_termination: If True (default), return the first non-empty
            result. If False, merge results from all strategies.

    Returns:
        List of dotted module names discovered across all executed strategies.
    """
    # Resolve packaging mode
    if packaging_mode is None:
        from cullinan.support.path_utils import get_packaging_mode
        packaging_mode = get_packaging_mode()

    if packaging_mode is None:
        packaging_mode = "development"

    mode = packaging_mode

    # Select pipeline
    pipeline_key = _map_mode_to_pipeline_key(mode)
    pipeline = PIPELINE_REGISTRY.get(pipeline_key)
    if pipeline is None:
        logger.warning(
            "Unknown packaging mode '%s', falling back to development pipeline",
            mode,
        )
        pipeline = PIPELINE_REGISTRY["development"]
        pipeline_key = "development"

    logger.info("Executing pipeline: %s (mode: %s)", pipeline_key, mode)

    # Resolve base directories for S4
    if base_dirs is None:
        base_dirs = _resolve_base_dirs(mode)

    all_modules: List[str] = []

    for label, strategy_func in pipeline:
        logger.debug("Running strategy: %s", label)
        try:
            result = strategy_func(config, mode, base_dirs)
        except Exception as e:
            logger.warning("Strategy %s raised %s: %s", label, type(e).__name__, e)
            continue

        if result:
            logger.info("Strategy %s returned %d modules", label, len(result))
            if early_termination:
                logger.info("Early termination at %s", label)
                return result
            for mod in result:
                if mod not in all_modules:
                    all_modules.append(mod)
        else:
            logger.debug("Strategy %s returned no modules", label)

    logger.info(
        "Pipeline %s complete: %d total modules",
        pipeline_key,
        len(all_modules),
    )
    return all_modules


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _map_mode_to_pipeline_key(mode: str) -> str:
    """Map a packaging mode string to a pipeline registry key.

    Args:
        mode: Raw packaging mode string (e.g., 'nuitka-standalone',
            'pyinstaller-onefile', None).

    Returns:
        Pipeline registry key (e.g., 'nuitka-standalone').
    """
    # Normalize: lowercase, strip whitespace
    normalized = mode.strip().lower() if mode else "development"

    # Direct mappings
    direct_mappings = {
        "nuitka-standalone": "nuitka-standalone",
        "nuitka-onefile": "nuitka-onefile",
        "nuitka": "nuitka-standalone",  # default Nuitka → standalone
        "pyinstaller-onedir": "pyinstaller-onedir",
        "pyinstaller-onefile": "pyinstaller-onefile",
        "pyinstaller": "pyinstaller-onedir",  # default PyInstaller → onedir
        "development": "development",
        "none": "development",
    }

    return direct_mappings.get(normalized, "development")


def _resolve_base_dirs(mode: str) -> List[str]:
    """Resolve base directories for filesystem scanning (S4).

    Args:
        mode: Normalized packaging mode string.

    Returns:
        List of directory paths to scan.
    """
    base_dirs: List[str] = []

    # PyInstaller: use _MEIPASS (temp extraction dir)
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        base_dirs.append(meipass)
        logger.info("PyInstaller _MEIPASS: %s", meipass)

    # For onedir / standalone modes, also scan executable directory
    if mode in ("nuitka-standalone", "nuitka-onefile", "pyinstaller-onedir", "pyinstaller-onefile"):
        exe_dir = os.path.dirname(sys.executable)
        if exe_dir not in base_dirs:
            base_dirs.append(exe_dir)
            logger.info("Executable directory: %s", exe_dir)

    return base_dirs


# Pre-import os for _resolve_base_dirs at module level
import os  # noqa: E402
