title: "Framework Semantics"
slug: "framework-semantics"
tags: ["guide", "semantics", "diagnostics"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/framework_semantics.md"
related_tests: ["tests/regression/test_component_reliability.py", "tests/core/test_injection_annotation_parsing.py"]
related_examples: []
estimate_pd: 1.0
last_updated: "2026-06-01T00:00:00Z"
pr_links: []

# Framework Semantics

This page defines the runtime semantics Cullinan **guarantees**, the behaviors it only keeps for compatibility, and the situations that now produce warnings or startup failures.

## 1. Component discovery is import-executed, not static AST scanning

Cullinan discovers decorated components by **importing Python modules** and letting decorators execute.

- guaranteed: module-top-level `@service`, `@controller`, `@component`, and `@provider` definitions that execute during module import
- not guaranteed: classes defined inside functions, factories, branches, or other local scopes that only run later

```python
from cullinan import component


@component
class TopLevelCache:
    pass


def build_repository():
    @component
    class LocalRepository:
        pass

    return LocalRepository
```

`TopLevelCache` is in the supported discovery path. `LocalRepository` is not part of the automatic top-level discovery contract; Cullinan now emits a warning for this pattern, and if it happens after `refresh()` it fails fast.

## 2. `Inject()` is a strict type contract

`Inject()` only succeeds when Cullinan can normalize the annotation into a **stable and unique** dependency contract.

Supported examples include:

- `T`
- `"T"`
- `Optional[T]`
- `Annotated[T, ...]`
- `Final[T]`
- `Provider[T]`
- `list[T]`, `set[T]`, `tuple[T, ...]`
- `Union[A, B]` / `A | B` when only one candidate is bindable

Cullinan does **not** fall back to attribute-name guessing anymore. If the annotation is missing, unsupported, or ambiguous, startup fails with a typed diagnostic.

## 3. `InjectByName()` is explicit-name semantics

`InjectByName()` resolves by component name, not by type.

Recommended form:

```python
from cullinan import InjectByName


class ReportController:
    report_service: "ReportService" = InjectByName("ReportService")
```

Compatibility form:

```python
class ReportController:
    report_service = InjectByName()
```

The compatibility form still falls back to the attribute name, but Cullinan now warns because the binding becomes easier to break during refactors. Even with name-based injection, keeping a real type annotation is recommended for readability and static analysis.

## 4. Lifecycle registration freezes after `refresh()`

`ApplicationContext.refresh()` is the structural boundary:

- pending decorator registrations are drained and registered
- definitions are validated and warmed
- registries are frozen

After that point, adding new decorated classes is no longer a supported runtime mutation path. Cullinan now surfaces a semantic error that explains the rule and the fix.

## 5. Scope rules are enforced, not best-effort

Cullinan treats scope compatibility as a hard rule. In particular, a `singleton` component cannot directly depend on a `request` scoped component. This now produces structured lifecycle diagnostics instead of failing later in an unpredictable way.

## 6. Compatibility APIs are compatibility only

Legacy surfaces such as `@injectable`, `@inject_constructor`, and `get_injection_registry()` remain available so older code can still import them, but they are **not** the recommended programming model anymore. Cullinan now warns when these APIs are used.

## 7. How to read warnings and errors

Cullinan now formats key diagnostics as:

- **Semantic rule**: the contract the framework enforces
- **Current problem**: what the runtime observed
- **Suggestion**: the safest supported fix

When the framework can prove a core semantic violation, startup fails. When code is still technically runnable but likely misleading, Cullinan emits a warning instead.
