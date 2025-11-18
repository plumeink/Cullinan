# Documentation Conventions (work area)

Purpose: Define the minimal conventions every documentation file must follow so that humans and automation can process docs reliably.

Encoding and format
- All docs must be UTF-8 encoded.
- Use Markdown syntax (.md) for all pages.

File placement
- Work docs: `docs/work/` (process, checklists, trackers, scripts)
- Target docs: `docs/` (public-facing guides) and `docs/zh/` (Chinese translations)
- Work docs and target docs must be kept separate; do not mix operational notes into public docs.

Front-matter schema (required fields)
- Every public doc under `docs/` and `docs/zh/` MUST include the following YAML-like front-matter fields at the top (see `front_matter_template.md` in this folder):
  - title, slug, module, tags, author, reviewers, status, locale, translation_pair, related_tests, related_examples, estimate_pd, last_updated

Naming and translation
- `docs/` and `docs/zh/` must maintain a 1:1 file and path mapping. Filenames and relative paths must match exactly; only content differs for translation.

PowerShell examples
- When showing PowerShell commands, use Windows PowerShell v5.1 syntax and separate commands with `;` when showing single-line sequences.
- Do not use `&&` to join commands.

Examples and runnable code
- Link to example code in the `examples/` folder; include an exact one-line command to run the example in PowerShell.
- Include expected output or behavior in plain text.

Review process
- Each public doc must have a work checklist (e.g., `docs/work/<doc>_checklist.md`) that documents progress, PR link, and reviewer sign-off.

Logging and emoji
- Do NOT use emoji in examples or logs per project rules.

Machine-friendly guidelines
- Provide `translation_pair` in front-matter for automation.
- Keep `related_tests` as a list of file paths so test automation can validate coverage.


