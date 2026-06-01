title: "API Reference"
slug: "reference-index"
module: []
tags: ["docs", "reference", "knowledge-base"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/reference/index.md"
related_tests: []
related_examples: []
estimate_pd: 1.0
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# API Reference

This knowledge domain is for **lookup**, not onboarding.

Use it when you already know the symbol, surface, or module family you want to
inspect. The pages here should stay stable, searchable, and role-clear.

## Main entrypoints

- [API Reference Overview](../api_reference.md) — recommended, advanced, and compatibility API layers
- Module references under `cullinan.app`, `cullinan.application`, `cullinan.core`, `cullinan.controller`, and `cullinan.service`

## Reference rules

- Regular application code should start from the top-level `cullinan` API
- Advanced runtime APIs should be explicitly imported from their own modules
- Compatibility modules remain documented, but they are not the default path

## Related domains

- Need explanation instead of lookup? Go to [Framework Semantics](../concepts/index.md)
- Need step-by-step usage? Go to [Engineering Practices](../how-to/index.md)
- Need internals? Go to [Internals & Extensions](../internals/index.md)
