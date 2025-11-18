title: "cullinan.app module"
slug: "modules-app"
module: ["cullinan.app"]
tags: ["api", "module"]
author: "Plumeink"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/modules/app.md"
related_tests: []
related_examples: []
estimate_pd: 0.8
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# cullinan.app

Summary: placeholder for `cullinan.app` module documentation. Describe entry-points and how to create app instances.

Public symbols to document: App, main (if present)

## Public API (auto-generated)

<!-- generated: docs/work/generated_modules/cullinan_app.md -->

### cullinan.app

| Name | Kind | Signature / Value |
| --- | --- | --- |
| `CullinanApplication` | class | `CullinanApplication(shutdown_timeout: int = 30)` |
| `create_app` | function | `create_app(shutdown_timeout: int = 30) -> cullinan.app.CullinanApplication` |

## Example: create and run an application

```python
# Quick (recommended): use the framework entrypoint in the process entry script
from cullinan import application

if __name__ == '__main__':
    application.run()

# Advanced (optional): programmatic control (e.g., tests or adding shutdown handlers)
from cullinan.app import create_app

application_instance = create_app()
# application_instance.startup()/application_instance.shutdown() or application_instance.add_shutdown_handler(...)
# application_instance.run()  # call at the process entrypoint
```
