title: "Cullinan Documentation"
slug: "docs-home"
module: []
tags: ["docs", "home"]
author: "Plumeink"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/README.md"
related_tests: []
related_examples: []
estimate_pd: 0.5
last_updated: "2025-11-18T17:35:00Z"
pr_links: []

# Cullinan Documentation

Welcome — this site contains the Cullinan framework documentation.

Use the navigation to the left to get started. Key areas:

- Getting Started — quick start and minimal app examples
- Architecture — system overview and diagrams
- Wiki — injection, lifecycle, middleware, extensions
- Modules — per-module API and examples
- Examples — runnable examples in the `examples/` directory
- Work — progress tracker and review tasks

For local preview, run:

```powershell
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -U pip; pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin
.\.venv\Scripts\Activate.ps1; mkdocs serve
```
