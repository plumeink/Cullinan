title: "Engineering Practices"
slug: "engineering-practices"
module: []
tags: ["docs", "how-to", "knowledge-base"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/how-to/index.md"
related_tests: ["tests/core/test_developer_experience.py", "tests/web/test_openapi_generator.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# Engineering Practices

This section is organized by **development tasks**, not by internal module names.

Use it after you understand the recommended startup path and the framework's
semantic rules. Each page here should answer "how do I do X in Cullinan?".

## Common tasks

- [Dependency Injection Guide](../dependency_injection_guide.md) — choose and apply injection primitives
- [Web Runtime Guide](../web_runtime_guide.md) — build Web APIs on the public runtime surface
- [Parameter System Guide](../parameter_system_guide.md) — use typed request parameters
- [Testing & Verification](../testing.md) — follow the repository test workflow
- [Build & Run](../build_run.md) — local run/build conventions

## Knowledge role

These pages are practical guides. They should not become the primary place for:

- low-level runtime internals
- historical migration notes
- full API symbol indexes

For those topics, use [Internals & Extensions](../internals/index.md),
[Migration & Version Notes](../migration/index.md), or [API Reference](../reference/index.md).
