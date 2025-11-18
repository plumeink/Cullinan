"""
Fill remaining TBD/empty owners in inventory_enhanced2.csv with a default owner ('writer').
Writes docs/work/inventory_final.csv
Run: python docs\work\fill_remaining_owners.py
"""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'docs' / 'work'
INV = WORK / 'inventory_enhanced2.csv'
OUT = WORK / 'inventory_final.csv'

DEFAULT_OWNER = 'writer'

if not INV.exists():
    print(f"Input not found: {INV}")
    raise SystemExit(1)

rows = []
with INV.open('r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for r in reader:
        owner = r.get('owner','').strip()
        if not owner or owner.upper() == 'TBD':
            r['owner'] = DEFAULT_OWNER
        rows.append(r)

with OUT.open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"Wrote final inventory to {OUT}")

