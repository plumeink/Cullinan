title: "API Reference"
slug: "api-reference"
module: []
tags: ["api", "reference"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/api_reference.md"
related_tests: []
related_examples: []
estimate_pd: 1.5
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# API Reference

> **Note (v0.90)**: The core module has been reorganized. For the new API structure, see [IoC/DI 2.0](wiki/ioc_di_v2.md) and [Import Migration Guide](import_migration_090.md).

This page provides an overview of the public API surface of Cullinan and acts as an entry point for generated or manually maintained per-module API pages. The recommended structure includes: a module index, the public symbols and signatures for each module, and a brief description of how to regenerate API documentation.

## Module index (example)

The following module list is for illustration only. The concrete index should be derived from the actual code structure and/or automated generation results:

- `cullinan.app` — Application creation and run entrypoints
- `cullinan.application` — Application lifecycle and startup flow
- `cullinan.core` — IoC/DI core (providers, registries, scopes, injection APIs)
- `cullinan.controller` — Controllers and RESTful API decorators
- `cullinan.service` — Service base class and the `@service` decorator
- `cullinan.middleware` — Middleware base classes and extension points

## Public symbols and signatures (recommended structure)

For each module, the API reference is recommended to follow this structure:

- Module path, for example: `cullinan.controller`
- Short description: primary responsibility and typical usage scenarios
- List of public classes and functions (example):
  - `@controller(...)` — Controller decorator, responsible for auto-registering controllers and their routes
  - `@get_api(url=..., query_params=..., body_params=..., headers=...)` — GET endpoint decorator
  - `@post_api(url=..., body_params=..., headers=...)` — POST endpoint decorator
  - `Inject`, `InjectByName` — Property/constructor injection markers

A complete API reference can be populated using this structure, either via automated generation or by manual curation.

## Regenerating API documentation (example workflow)

When adding automation later, a static analysis script can be used to generate the API index and keep this page in sync with the source. A typical workflow might be:

1. Maintain a script under `docs/work/` (for example `generate_api_reference.py`) that scans modules and emits Markdown fragments.
2. Have the script produce a per-module API list (classes, functions, signatures, short descriptions) into `docs/work/api_modules.md` or update this page directly.
3. Run the script periodically in CI or as part of local documentation build steps to ensure the API reference reflects the current codebase.

The exact tooling and script implementation can be refined based on project conventions and the chosen documentation toolchain.
