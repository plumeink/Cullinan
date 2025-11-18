title: "Testing & Verification"
slug: "testing"
module: []
tags: ["testing"]
author: "TBD"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/testing.md"
related_tests: ["tests/test_real_app_startup.py"]
related_examples: []
estimate_pd: 1.5
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# Testing & Verification

This page describes how to run the existing test suite, add new tests, run example smoke tests, and integrate test execution into CI. Commands are shown for Windows (PowerShell), Linux, and macOS.

## Prerequisites

- Python 3.8 or newer
- Git
- A working Cullinan checkout (see `docs/build_run.md` for environment setup)

## Running the test suite

After installing Cullinan in editable mode (see `docs/build_run.md`), you can run the tests with `pytest`.

On all platforms:

```bash
pytest -q
```

If your environment prefers invoking via the Python module interface, you can use:

```bash
python -m pytest -q
```

On Windows, it is also common to use the `py` launcher:

```powershell
py -3 -m pytest -q
```

## Running individual test modules

To run a single test file (for example `tests/test_core_injection.py`):

On all platforms:

```bash
pytest tests/test_core_injection.py -q
```

Or with the Python module interface:

```bash
python -m pytest tests/test_core_injection.py -q
```

## Adding new tests

When adding tests for new features or bug fixes:

1. Place test files under the `tests/` directory.
2. Use descriptive test names and group related tests in the same module.
3. Prefer `pytest` style tests (functions and classes) to match the existing suite.
4. Ensure tests are deterministic and do not depend on external services unless explicitly marked.

## Smoke tests using examples

Cullinan includes runnable examples under the `examples/` directory that can be used as smoke tests.

### Example: Hello HTTP

On Windows (PowerShell):

```powershell
python examples\hello_http.py
```

On Linux / macOS:

```bash
python examples/hello_http.py
```

Then open `http://localhost:4080/hello` in a browser to verify that the server responds.

### Example: Middleware demo

On Windows (PowerShell):

```powershell
python examples\middleware_demo.py
```

On Linux / macOS:

```bash
python examples/middleware_demo.py
```

The log output illustrates how middleware and injected services participate in request handling. Exact timestamps and IDs may vary between runs.

## Integrating tests into CI

In a CI pipeline, the following steps are typically required:

1. Set up a Python environment.
2. Install dependencies in editable mode (optionally with development extras).
3. Run the test suite with `pytest`.

Example sequence (bash-style, to be adapted to your CI system):

```bash
python -m pip install -U pip
pip install -e .[dev]
pytest -q
```

On Windows-based CI using PowerShell, the commands are analogous:

```powershell
python -m pip install -U pip
pip install -e .[dev]
py -3 -m pytest -q
```

Adjust the exact commands and options according to your CI provider and environment.
