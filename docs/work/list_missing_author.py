from pathlib import Path
root = Path(__file__).resolve().parents[1] / 'docs'
missing = []
for p in sorted(root.rglob('*.md')):
    text = p.read_text(encoding='utf-8')
    head = '\n'.join(text.splitlines()[:50])
    if 'title:' in head:
        if 'author:' not in head:
            missing.append(str(p.relative_to(root)))
    else:
        missing.append(str(p.relative_to(root)))
print(len(missing))
for m in missing:
    print(m)

