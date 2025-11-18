# Review Issue Templates (per-module)

Below are markdown templates you can paste into GitHub Issues or a project board to assign reviewers and track decisions.

---

## [Review] core module docs and API candidates
**Owner:** @core-eng
**Files to review:**
- `docs/modules/core.md`
- `docs/zh/modules/core.md`
- `docs/work/api_cleanup_candidates.csv` (filter: module == cullinan.core)

**Tasks:**
- Verify examples in `docs/modules/core.md` match runtime behavior.
- For each row in the CSV where `module == cullinan.core`, set `decision` to `keep`/`remove`/`review` and add a short rationale.
- Confirm `InjectionRegistry`/`ProviderRegistry` APIs are correctly documented.

**Acceptance:** All CSV lines for `cullinan.core` annotated; docs example validated locally.

---

## [Review] controller module docs and API candidates
**Owner:** @controller-eng
**Files to review:**
- `docs/modules/controller.md`
- `docs/zh/modules/controller.md`
- `docs/work/api_cleanup_candidates.csv` (filter: module == cullinan.controller)

**Tasks:**
- Check controller decorator/function signatures and examples.
- Mark CSV decisions for controller symbols.

**Acceptance:** CSV entries annotated; examples verified.

---

## [Review] service module docs and API candidates
**Owner:** @service-eng
**Files to review:**
- `docs/modules/service.md`
- `docs/zh/modules/service.md`
- `docs/work/api_cleanup_candidates.csv` (filter: module == cullinan.service)

**Tasks:**
- Verify service lifecycle notes and example correctness.
- Mark CSV decisions for service symbols.

**Acceptance:** CSV entries annotated; examples verified.

---

## [Review] application & app docs
**Owner:** @writer/dev
**Files to review:**
- `docs/modules/application.md`
- `docs/modules/app.md`
- `docs/zh/modules/application.md`
- `docs/zh/modules/app.md`

**Tasks:**
- Confirm startup sequence and example snippets reflect actual `cullinan/app.py` behavior.

**Acceptance:** Docs match runtime and review comments addressed.

---

## How to run a local smoke check
1. Create and activate a virtualenv:

```powershell
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .
pip install tornado mkdocs mkdocs-material mkdocs-mermaid2-plugin
```

2. Run example smoke tests (e.g., `examples/middleware_demo.py`) to validate behavior.

3. Edit `docs/work/api_cleanup_candidates.csv` and set `decision` column values.

4. Comment on the review issue with "CSV updated: see commit <hash>" or attach a brief rationale for removes.

