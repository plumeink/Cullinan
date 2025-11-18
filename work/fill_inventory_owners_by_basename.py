"""
Fill owners in inventory_enhanced.csv by matching basenames against entries
in docs/work/progress_tracker.md. Writes docs/work/inventory_enhanced2.csv.

Run: python docs\work\fill_inventory_owners_by_basename.py
"""
from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'docs' / 'work'
TRACKER = WORK / 'progress_tracker.md'
INV = WORK / 'inventory_enhanced.csv'
OUT = WORK / 'inventory_enhanced2.csv'

text = TRACKER.read_text(encoding='utf-8')
# parse small metadata blocks for '- doc:' and '- owner:' pairs, but be robust
doc_owner = {}
lines = text.splitlines()
current_doc = None
for ln in lines:
    s = ln.strip()
    if s.startswith('- doc:'):
        val = s.split(':',1)[1].strip().strip('"')
        # normalize: remove leading docs/ if present
        norm = val
        if norm.startswith('docs/'):
            norm = norm[5:]
        doc_owner[norm] = doc_owner.get(norm, None)
        current_doc = norm
    elif s.startswith('- ID:'):
        # also potential start of block with ID but we don't need it
        current_doc = None
    elif s.startswith('- owner:') and current_doc:
        owner = s.split(':',1)[1].strip().strip('"')
        if owner:
            doc_owner[current_doc] = owner
            current_doc = None

# also build alternative mapping by basename -> owner
basename_owner = {}
for k,v in doc_owner.items():
    if v:
        base = Path(k).name
        basename_owner[base] = v
        # also map with possible modules/... prefix
        basename_owner[str(Path('modules')/base)] = v
        basename_owner[str(Path('wiki')/base)] = v
        basename_owner[k] = v

if not INV.exists():
    print(f"Inventory enhanced file not found: {INV}")
    raise SystemExit(1)

rows = []
with INV.open('r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        path = r.get('path')
        owner = r.get('owner','')
        if not owner or owner.strip()=='' or owner.strip()=='TBD':
            # try direct match
            new_owner = None
            if path in doc_owner and doc_owner[path]:
                new_owner = doc_owner[path]
            else:
                # try without docs/ prefix
                if path.startswith('docs/'):
                    p2 = path[5:]
                else:
                    p2 = path
                if p2 in doc_owner and doc_owner[p2]:
                    new_owner = doc_owner[p2]
                # try basename
                if not new_owner:
                    base = Path(path).name
                    if base in basename_owner:
                        new_owner = basename_owner[base]
            if new_owner:
                r['owner'] = new_owner
        rows.append(r)

# write enhanced2 CSV
with OUT.open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"Wrote enhanced inventory to {OUT}")

