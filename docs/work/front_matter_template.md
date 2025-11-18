# Front-matter Template

Place this YAML-like block at the top of every public doc (replace values):

```
title: "<Short title>"
slug: "<path-friendly-slug>"
module: ["cullinan.core"]
tags: ["getting-started", "ioc"]
author: "Name <github>"
reviewers: ["Name <github>"]
status: draft
locale: en
translation_pair: "docs/zh/<file>.md"
related_tests: ["tests/test_real_app_startup.py"]
related_examples: ["examples/hello_http.py"]
estimate_pd: 2.0
last_updated: "2025-11-18T00:00:00Z"
pr_links: []
```

Notes:
- `module`, `related_tests`, and `related_examples` should be lists to simplify automation.
- Keep this block short and machine-parseable.

