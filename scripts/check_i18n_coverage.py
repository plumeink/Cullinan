import yaml
import os

ROOT = os.path.dirname(os.path.dirname(__file__))
MKDOCS = os.path.join(ROOT, 'mkdocs.yml')

with open(MKDOCS, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

nav = cfg.get('nav', [])

# flatten nav to paths
paths = []

def walk(items):
    for it in items:
        if isinstance(it, dict):
            for k, v in it.items():
                if isinstance(v, str):
                    paths.append(v)
                elif isinstance(v, list):
                    walk(v)
        elif isinstance(it, str):
            paths.append(it)

walk(nav)

missing = []
for p in paths:
    # map to zh path
    if p.startswith('zh/'):
        continue
    zh_p = os.path.join(ROOT, 'docs', 'zh', p)
    if os.path.exists(zh_p):
        continue
    # handle paths like 'work/progress_tracker.md' -> zh/work/progress_tracker.md
    zh_candidate = os.path.join(ROOT, 'docs', 'zh', p)
    if not os.path.exists(zh_candidate):
        missing.append(p)

print('Total nav entries:', len(paths))
print('Missing zh translations for:')
for m in missing:
    print('-', m)

