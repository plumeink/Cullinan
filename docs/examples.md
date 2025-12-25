title: "Examples and Demos"
slug: "examples"
module: []
tags: ["examples"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/examples.md"
related_tests: []
related_examples: ["examples/hello_http.py"]
estimate_pd: 1.5
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# Examples and Demos

> **Note (v0.90)**: Some examples below use the legacy 1.x DI API.
> For the new 2.0 API examples, see [IoC/DI 2.0 Architecture](wiki/ioc_di_v2.md).
> New projects should use `ApplicationContext` from `cullinan.core.container`.

This page lists canonical runnable examples shipped with Cullinan. Each entry includes the example path, a short description, and how to run it on common platforms.

## Hello HTTP

- **Path**: `examples/hello_http.py`
- **Description**: Minimal HTTP server returning a greeting.

### How to run

On Windows (PowerShell):

```powershell
python examples\hello_http.py
```

On Linux / macOS:

```bash
python examples/hello_http.py
```

Expected behavior:

- Starts an HTTP server.
- Serves a response on `http://localhost:4080/hello`.

## Controller + DI + Middleware demo

- **Path**: `examples/controller_di_middleware.py`
- **Description**: Demonstrates integration between controllers, dependency injection, and middleware.

### How to run

On Windows (PowerShell):

```powershell
python examples\controller_di_middleware.py
```

On Linux / macOS:

```bash
python examples/controller_di_middleware.py
```

Expected behavior:

- Logs request handling through middleware.
- Shows how injected services participate in the request pipeline.

<!-- ...you can extend this list with additional examples as they are added to the repository... -->
