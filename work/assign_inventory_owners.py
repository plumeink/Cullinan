"""
Assign owners to docs/work/inventory.csv by reading owner entries from
docs/work/progress_tracker.md metadata blocks. Writes docs/work/inventory_enhanced.csv.

Run: python docs\work\assign_inventory_owners.py
"""
from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'docs' / 'work'
TRACKER = WORK / 'progress_tracker.md'
INV = WORK / 'inventory.csv'
OUT = WORK / 'inventory_enhanced.csv'

# Parse progress_tracker to map doc -> owner
text = TRACKER.read_text(encoding='utf-8')
# find metadata blocks: look for lines like '- doc: docs/...'
lines = text.splitlines()
mapping = {}
current_doc = None
for ln in lines:
    s = ln.strip()
    if s.startswith('- doc:'):
        # format: - doc: docs/xxxx.md
        current_doc = s.split(':',1)[1].strip()
        current_doc = current_doc.strip('"')
    elif s.startswith('- owner:') and current_doc:
        owner = s.split(':',1)[1].strip()
        owner = owner.strip('"')
        mapping[current_doc] = owner
        current_doc = None

# Read inventory and update owner where possible
if not INV.exists():
    print(f"Inventory file not found: {INV}")
    raise SystemExit(1)

rows = []
with INV.open('r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        path = r.get('path')
        # try to match mapping key; mapping may include docs/ prefix
        owner = r.get('owner','')
        if (not owner or owner.strip()=='TBD') and path in mapping:
            r['owner'] = mapping[path]
        rows.append(r)

# write enhanced CSV
with OUT.open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"Wrote enhanced inventory to {OUT}")

