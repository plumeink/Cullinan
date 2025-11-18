"""
Simple validation script for docs:
- Ensures 1:1 mapping between `docs/` and `docs/zh/` (excluding `docs/work/`)
- Checks required front-matter keys are present at top of each markdown file
- Writes a summary to `docs/work/inventory.md` and `docs/work/inventory.csv`

Run from repository root with: python docs/work/validate_docs.py
"""
from pathlib import Path
import csv

REQUIRED_FIELDS = ["title","slug","module","status","locale","translation_pair"]

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
WORK = DOCS / "work"
ZH = DOCS / "zh"

entries = []

for md in DOCS.rglob("*.md"):
    # Skip work files
    try:
        rel = md.relative_to(DOCS)
    except Exception:
        continue
    if str(rel).startswith("work"):
        continue
    # Only consider top docs (include wiki/) but skip zh
    if str(rel).startswith("zh"):
        continue
    # Read first section for simple key: value front-matter
    data = {}
    with md.open("r", encoding="utf-8") as f:
        for ln in f:
            line = ln.strip()
            if not line:
                break
            if ":" in line:
                k,v = line.split(":",1)
                data[k.strip()] = v.strip().strip('"')
    has_zh = (ZH / rel).exists()
    missing = [k for k in REQUIRED_FIELDS if k not in data]
    entries.append({
        "path": str(rel),
        "title": data.get("title",""),
        "locale": data.get("locale","en"),
        "has_zh": bool(has_zh),
        "missing_fields": missing,
        "owner": data.get("author",""),
        "priority": data.get("priority","medium")
    })

# Write inventory.md
lines = ["# Docs & Examples Inventory","","Path | Title | Locale | Has_ZH | Missing_Fields","--- | --- | --- | --- | ---"]
for e in entries:
    lines.append(f"{e['path']} | {e['title']} | {e['locale']} | { 'yes' if e['has_zh'] else 'no' } | {', '.join(e['missing_fields'])}")

WORK.mkdir(parents=True, exist_ok=True)
inv_md = WORK / "inventory.md"
inv_md.write_text("\n".join(lines), encoding="utf-8")

# Write inventory.csv
inv_csv = WORK / "inventory.csv"
with inv_csv.open("w", newline='', encoding='utf-8') as csvf:
    writer = csv.writer(csvf)
    writer.writerow(["path","title","locale","has_zh","missing_fields","owner","priority"])
    for e in entries:
        writer.writerow([e['path'], e['title'], e['locale'], 'yes' if e['has_zh'] else 'no', ';'.join(e['missing_fields']), e['owner'], e['priority']])

# Print summary
print(f"Found {len(entries)} docs under docs/ (excluding work/ and zh/). Inventory written to {inv_md} and {inv_csv}")
for e in entries:
    if e['missing_fields'] or not e['has_zh']:
        print(f"- {e['path']}: missing {e['missing_fields']} ; has_zh={e['has_zh']}")
