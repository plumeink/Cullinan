# -*- coding: utf-8 -*-
"""Import hook that automatically enables :pep:`563` for application modules.

When active, every module whose file path falls under the application root
package is compiled with ``CO_FUTURE_ANNOTATIONS``.  This makes bare
constructor-injection annotations (e.g., ``svc: UserService``) safe to use
with ``TYPE_CHECKING`` imports — Python stores annotations as strings and
Cullinan's existing ``find_by_type_name`` fallback resolves them.

**Scope:** only application modules; Cullinan internals, stdlib and
third-party packages are never affected.  Hooks are installed before
``discover()`` and removed after ``assemble()`` so they never leak.
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import linecache
import os
import sys
import types
from typing import Any, List, Optional, Sequence


# ---------------------------------------------------------------------------
# CO_FUTURE_ANNOTATIONS compile flag (Python 3.7+, always available)
# ---------------------------------------------------------------------------
_CO_FUTURE_ANNOTATIONS = 0x1000000  # PEP 563 compile flag


def _is_subpath(path: str, root: str) -> bool:
    """Return True if *path* is equal to or inside *root* (filesystem hierarchy)."""
    try:
        path_norm = os.path.normcase(os.path.normpath(os.path.abspath(path)))
        root_norm = os.path.normcase(os.path.normpath(os.path.abspath(root)))
    except (TypeError, ValueError):
        return False
    if path_norm == root_norm:
        return True
    if not root_norm.endswith(os.sep):
        root_norm += os.sep
    return path_norm.startswith(root_norm)


class _AnnotationsLoader(importlib.abc.FileLoader, importlib.abc.SourceLoader):
    """Loader that compiles source with ``CO_FUTURE_ANNOTATIONS``."""

    def __init__(self, fullname: str, path: str) -> None:
        super().__init__(fullname, path)  # type: ignore[arg-type]

    def get_data(self, path: str) -> bytes:
        if not path:
            raise ImportError("no path", name=self.name)
        with open(path, "rb") as f:
            return f.read()

    def source_to_code(  # type: ignore[override]
        self,
        data: bytes | str,
        path: str,
        *,
        _optimize: int = -1,
    ) -> types.CodeType:
        if isinstance(data, bytes):
            source = data.decode("utf-8")
        else:
            source = data
        return compile(
            source,
            path,
            "exec",
            flags=_CO_FUTURE_ANNOTATIONS,
            dont_inherit=True,
            optimize=_optimize,
        )

    def exec_module(self, module: types.ModuleType) -> None:
        """Execute the module with CO_FUTURE_ANNOTATIONS enabled."""
        # Invalidating the linecache ensures source_to_code re-reads the file
        # and re-compiles, so fresh annotation strings are produced.
        filename = self.get_filename(self.name)
        linecache.checkcache(filename)
        super().exec_module(module)


class _AnnotationsFinder(importlib.abc.MetaPathFinder):
    """Meta-path finder that routes application modules to ``_AnnotationsLoader``.

    Only modules whose file path is beneath *root_path* are intercepted;
    everything else falls through to the next finder.
    """

    def __init__(self, root_path: str) -> None:
        self._root_path = root_path

    def find_spec(
        self,
        fullname: str,
        path: Optional[Sequence[str]],
        target: Optional[types.ModuleType] = None,
    ) -> Optional[importlib.machinery.ModuleSpec]:
        # Try to locate the module on disk using standard machinery.
        try:
            spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        except Exception:
            return None
        if spec is None or spec.origin is None:
            return None

        # Only intercept modules under the application root.
        if not _is_subpath(spec.origin, self._root_path):
            return None

        # Don't touch namespace packages (no __init__.py).
        origin = spec.origin
        if origin.endswith(os.sep):  # namespace
            return None

        # Build our custom loader and replace the spec's loader.
        loader = _AnnotationsLoader(fullname, origin)
        # Use the original spec's submodule_search_locations if present.
        if hasattr(spec, "submodule_search_locations") and spec.submodule_search_locations is not None:
            submodule_search = spec.submodule_search_locations
        else:
            submodule_search = None

        new_spec = importlib.machinery.ModuleSpec(
            fullname,
            loader,
            origin=origin,
            is_package=spec.submodule_search_locations is not None,
            loader_state=spec.loader_state,
        )
        if submodule_search is not None:
            new_spec.submodule_search_locations = list(submodule_search)
        return new_spec


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_FINDER_INSTANCE: Optional[_AnnotationsFinder] = None


def install_annotations_hook(root_path: str) -> None:
    """Install the PEP-563 annotations hook for modules under *root_path*.

    Safe to call multiple times — only the first call installs.
    """
    global _FINDER_INSTANCE
    if _FINDER_INSTANCE is not None:
        return
    _FINDER_INSTANCE = _AnnotationsFinder(root_path)
    sys.meta_path.insert(0, _FINDER_INSTANCE)


def uninstall_annotations_hook() -> None:
    """Remove the annotations hook (idempotent)."""
    global _FINDER_INSTANCE
    if _FINDER_INSTANCE is not None:
        try:
            sys.meta_path.remove(_FINDER_INSTANCE)
        except ValueError:
            pass
        _FINDER_INSTANCE = None


def is_annotations_hook_installed() -> bool:
    """Return ``True`` if the hook is currently active."""
    return _FINDER_INSTANCE is not None


def get_hook_root_path() -> Optional[str]:
    """Return the root path of the installed hook, or ``None``."""
    if _FINDER_INSTANCE is not None:
        return _FINDER_INSTANCE._root_path  # type: ignore[union-attr]
    return None


def _resolve_app_root_path(root_module: Any) -> Optional[str]:
    """Best-effort resolve of the application root directory from *root_module*.

    Returns the package directory of the root module, or ``None`` when the
    path cannot be determined (e.g. for namespace packages or REPL-defined
    modules).  When ``None``, ``discover()`` skips hook installation.
    """
    try:
        mod = sys.modules[root_module.__module__]
        file = getattr(mod, "__file__", None)
        if file:
            return os.path.dirname(os.path.abspath(file))
    except Exception:
        pass
    return None
