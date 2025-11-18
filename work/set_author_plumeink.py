#!/usr/bin/env python3
"""
Set author: "Plumeink" in front-matter of all Markdown files under docs/ and docs/zh/.
Handles two front-matter styles:
- YAML block delimited with leading '---' (will insert/replace author inside it)
- Simple key:value header lines at top (no '---') until first blank line or first markdown header

Prints a list of modified files.
"""
import io
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / 'docs'
TARGETS = [ROOT, ROOT / 'zh']
MODIFIED = []

def process_file(path: Path):
    text = path.read_text(encoding='utf-8')
    orig = text
    # Detect YAML block starting with ---
    if text.lstrip().startswith('---'):
        # find end of yaml block
        m = re.search(r"^---\s*$", text, flags=re.MULTILINE)
        if not m:
            return False
        # find second '---'
        start = m.start()
        second = re.search(r"^---\s*$", text[m.end():], flags=re.MULTILINE)
        if second:
            end = m.end() + second.end()
            fm = text[:end]
            rest = text[end:]
            # replace or add author line inside fm
            if re.search(r"^author\s*:\s*.*$", fm, flags=re.MULTILINE):
                fm = re.sub(r"^author\s*:\s*.*$", 'author: "Plumeink"', fm, flags=re.MULTILINE)
            else:
                # insert before the closing ---
                fm = fm.rstrip('\n')
                fm = fm[:-3] + '\n' + 'author: "Plumeink"\n' + '---\n'
            new = fm + rest
            if new != text:
                path.write_text(new, encoding='utf-8')
                return True
            return False
    else:
        # simple header style: contiguous key: value lines at top until first blank line or header
        lines = text.splitlines()
        fm_lines = []
        rest_lines = []
        in_fm = True
        for i, line in enumerate(lines):
            if in_fm:
                if line.strip() == '' or line.lstrip().startswith('#'):
                    in_fm = False
                    rest_lines = lines[i:]
                    break
                if ':' in line:
                    fm_lines.append(line)
                else:
                    # non key:value line -> treat as end
                    in_fm = False
                    rest_lines = lines[i:]
                    break
        else:
            # all lines are fm-like
            in_fm = False
            rest_lines = []
        if not fm_lines:
            # no recognizable front-matter: do nothing
            return False
        # process fm_lines: find author
        found = False
        new_fm = []
        for line in fm_lines:
            if re.match(r"^author\s*:\s*", line):
                new_fm.append('author: "Plumeink"')
                found = True
            else:
                new_fm.append(line)
        if not found:
            # insert author after tags line if exists, else after slug, else at top
            insert_at = 0
            for idx, line in enumerate(new_fm):
                if line.strip().startswith('tags:'):
                    insert_at = idx + 1
                    break
                if line.strip().startswith('slug:'):
                    insert_at = idx + 1
            new_fm.insert(insert_at, 'author: "Plumeink"')
        # reassemble
        new_text = '\n'.join(new_fm + [''] + rest_lines)
        if new_text != text:
            path.write_text(new_text, encoding='utf-8')
            return True
        return False

for base in TARGETS:
    if not base.exists():
        continue
    for p in sorted(base.rglob('*.md')):
        try:
            changed = process_file(p)
            if changed:
                MODIFIED.append(str(p.relative_to(Path.cwd())))
        except Exception as e:
            print(f"Error processing {p}: {e}")

print(f"Modified {len(MODIFIED)} files")
for m in MODIFIED:
    print(m)

