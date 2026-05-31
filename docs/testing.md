title: "Testing & Verification"
slug: "testing"
module: []
tags: ["testing"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/testing.md"
related_tests: ["tests/core/test_application_model_refactor.py", "tests/core/test_decorators.py", "tests/integration/test_adapter_integration.py", "tests/web/test_web_runtime.py", "tests/di/test_core_constructor_injection.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2026-05-31T00:00:00Z"
pr_links: []

# Testing & Verification

This page describes the current repository test workflow after the latest
application-model and adapter test refresh.

## Official repository entrypoint

Use the repository virtual environment and run:

```powershell
.venv\Scripts\python -m pytest
```

That is the formal repository command for full-suite verification.

## Test discovery configuration

`pytest.ini` defines the repository defaults:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -ra
```

`tests/conftest.py` adds the repository root to `sys.path`, so new tests should not repeat local `sys.path.insert(...)` bootstrapping.

## Test layout

The test suite is organized by topic:

- `tests/core`
- `tests/di`
- `tests/web`
- `tests/integration`
- `tests/regression`
- `tests/compat`
- `tests/helpers`

Prefer placing new tests in the closest existing topic folder instead of creating ad-hoc top-level files.

## Running targeted tests

Examples:

```powershell
.venv\Scripts\python -m pytest tests\web\test_web_runtime.py -q
.venv\Scripts\python -m pytest tests\di\test_core_constructor_injection.py -q
```

Generic `python -m pytest` also works, but the repository documentation standard uses the `.venv\Scripts\python` form on Windows.

## Current conventions

1. Write standard pytest tests with plain `assert` statements.
2. New and refreshed suites should be pytest-native, even if some historical files still keep migration shims.
3. Reuse shared setup from `tests/conftest.py` and `tests/helpers/` when appropriate.
4. Keep tests deterministic and isolated; clear global registries or active application context when a test mutates them.

## Scope covered by the test suite

The current suite covers:

- application-first bootstrap, module ownership resolution, and runtime switching
- container and lifecycle behavior
- compatibility shims
- gateway / Web Runtime behavior
- controller routing and parameter handling
- integration and regression scenarios

Representative files:

- `tests/core/test_application_model_refactor.py`
- `tests/core/test_decorators.py`
- `tests/integration/test_adapter_integration.py`

## Related documents

- [Runtime consolidation overview](runtime_updates_v093.md)
- [Application Runtime Model](wiki/application_runtime.md)
- [Architecture](architecture.md)
- [Web Runtime Guide](web_runtime_guide.md)
