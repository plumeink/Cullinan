title: "Cullinan Knowledge Base"
slug: "docs-home"
module: []
tags: ["docs", "home", "knowledge-base"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/README.md"
related_tests: []
related_examples: []
estimate_pd: 0.5
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# Cullinan Knowledge Base

Cullinan documentation is now organized as a **knowledge base**, not as a mixed
list of wiki pages, module pages, guides, and migration notes.

> **Current version: 0.93a6**. The recommended application path is
> `from cullinan import configure, run`: start from business decorators and
> business methods first, then enter advanced runtime details only when the
> application really needs them.

## Default learning path

1. [Application Build](start/index.md)
2. [Framework Semantics](concepts/index.md)
3. [Engineering Practices](how-to/index.md)
4. [API Reference](reference/index.md)

This path is the default for most developers using Cullinan to build business
applications. It intentionally keeps advanced runtime internals and version
migration notes outside the first-read path.

## Knowledge domains

### 1. [Application Build](start/index.md)

Use this section to bootstrap a new application with the recommended public API.

- [Getting Started](getting_started.md)
- [Examples](examples.md)
- [Build & Run](build_run.md)

### 2. [Framework Semantics](concepts/index.md)

Use this section to understand how Cullinan thinks and why it discourages
explicit app-centric wiring.

- [Framework Semantics](framework_semantics.md)
- [Architecture](architecture.md)

### 3. [Engineering Practices](how-to/index.md)

Use this section for task-oriented guides.

- [Dependency Injection Guide](dependency_injection_guide.md)
- [Web Runtime Guide](web_runtime_guide.md)
- [Parameter System Guide](parameter_system_guide.md)
- [Testing & Verification](testing.md)

### 4. [API Reference](reference/index.md)

Use this section for symbol lookup and stable API surface review.

- [API Reference Overview](api_reference.md)
- [Module Reference: app](modules/app.md)
- [Module Reference: application](modules/application.md)
- [Module Reference: core](modules/core.md)
- [Module Reference: controller](modules/controller.md)
- [Module Reference: service](modules/service.md)

### 5. [Internals & Extensions](internals/index.md)

Use this section only when you intentionally need advanced runtime or extension knowledge.

- [Application Runtime Model](wiki/application_runtime.md)
- [Extension Development Guide](extension_development_guide.md)
- [Quick Start Extensions](quick_start_extensions.md)

### 6. [Migration & Version Notes](migration/index.md)

Use this section when upgrading or reconciling old code with newer semantics.

- [Runtime Consolidation](runtime_updates_v093.md)
- [Migration Guide](migration_guide.md)
- [Migration Guide v2](migration_guide_v2.md)
- [Import Migration 0.90](import_migration_090.md)

## Documentation governance

- New content should be written under a clear knowledge role first
- Teaching pages, reference pages, internals, and migration notes should not share one page's primary responsibility
- Advanced topics must say that they are advanced
- English pages live under `docs/`; Chinese mirrors live under `docs/zh/` with matching relative paths

For source code and release history, visit the [GitHub repository](https://github.com/plumeink/Cullinan).
