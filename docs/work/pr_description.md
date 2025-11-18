PR Title: docs: MVP documentation site (placeholders, examples, API index)

Summary:
This PR adds the initial MVP documentation structure (English + Chinese 1:1), example smoke-tests, API index generator and module API auto-extraction, and a docs validation CI workflow.

Key changes:
- Docs: added module docs with auto-generated Public API tables and example snippets under `docs/modules/` and `docs/zh/modules/`.
- Scripts: added `docs/work/generate_module_api.py`, `docs/work/generate_api_index.py`, `docs/work/core_examples.py`, and docs validation scripts.
- CI: added `.github/workflows/docs-validate.yml` (runs docs validation and core examples smoke test).
- Inventory: generated `docs/work/inventory*.csv` and `docs/work/module_api_summary.*`.

Verification steps performed locally:
- Created venv, installed editable package and tornado, ran `examples/hello_http.py` and `docs/work/core_examples.py` (both succeeded).
- Ran `python docs/work/validate_docs.py` to generate inventory and ensure front-matter.

Review checklist:
- [ ] Technical review for `docs/modules/core.md` examples (core-eng)
- [ ] API tables review: filter or remove internal symbols (module owners)
- [ ] Validate PowerShell examples (Windows eng)
- [ ] Confirm CI workflow policy for core-examples (blocking vs non-blocking)
- [ ] Update owners in `docs/work/inventory_final.csv` if needed

Notes:
- Auto-generated API lists are drafts and require human review.
- Running example scripts requires Python 3.8+ and tornado installed in virtualenv.

