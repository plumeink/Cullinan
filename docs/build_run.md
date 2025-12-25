title: "Local Build & Run"
slug: "build-run"
module: []
tags: ["build", "run"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/build_run.md"
related_tests: []
related_examples: []
estimate_pd: 1.0
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# Local Build & Run

This page describes how to set up a local environment, install Cullinan in editable mode, run tests, and start example applications on Windows (PowerShell), Linux, and macOS.

## Prerequisites

- Python 3.8 or newer
- Git

## Clone the repository

On all platforms:

```bash
git clone https://github.com/plumeink/Cullinan.git
cd Cullinan
```

## Create and activate a virtual environment (optional but recommended)

On Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

## Install dependencies in editable mode

On all platforms:

```bash
python -m pip install -U pip
pip install -e .
```

If you have additional development extras configured in `setup.py` or `pyproject.toml`, you can install them as needed, for example:

```bash
pip install -e .[dev]
```

## Run the test suite

On all platforms:

```bash
pytest -q
```

If your environment uses a different test runner, adapt the command accordingly (e.g. `python -m pytest`).

## Run an example application

### Hello HTTP example

On Windows (PowerShell):

```powershell
python examples\hello_http.py
```

On Linux / macOS:

```bash
python examples/hello_http.py
```

Then open `http://localhost:4080/hello` in a browser to verify the server is running.

### Middleware demo

On Windows (PowerShell):

```powershell
python examples\middleware_demo.py
```

On Linux / macOS:

```bash
python examples/middleware_demo.py
```

Refer to the middleware documentation for a description of the expected log output and behavior.
