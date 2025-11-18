"""
Generate per-module public API summaries for selected modules and write
- docs/work/module_api_summary.md (human-readable)
- docs/work/generated_<module>.md (per-module snippet)

Also inject cleaned markdown table into docs/modules/<module>.md at the marker
`<!-- generated: docs/work/generated_modules/<module>.md -->` if present.

Run: python docs\work\generate_module_api.py
"""
from pathlib import Path
import importlib
import inspect
import json
import types
import builtins
import csv

ROOT = Path(__file__).resolve().parents[2]
OUT_MD = ROOT / "docs" / "work" / "module_api_summary.md"
OUT_DIR = ROOT / "docs" / "work" / "generated_modules"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIS_PATH = ROOT / 'docs' / 'work' / 'api_visibility.json'
try:
    import json as _json
    if VIS_PATH.exists():
        _vis = _json.loads(VIS_PATH.read_text(encoding='utf-8'))
    else:
        _vis = {}
except Exception:
    _vis = {}

modules = [
    'cullinan.application',
    'cullinan.app',
    'cullinan.core',
    'cullinan.controller',
    'cullinan.service',
]

all_data = {}

# Helper to decide if an object should be included
def include_obj(modname, obj):
    """Return True if obj is a public symbol we should document for modname.
    Rules:
    - Include if the object's __module__ equals the module or is a submodule of it.
    - Otherwise, attempt to find the module file for the object's defining module; only include if that file is inside the repository (ROOT).
    - Exclude module objects (types.ModuleType), logging/inspect/typing artifacts, and large/complex reprs.
    - Include simple constants only when they are defined in the module (covered by first rule).
    """
    # Exclude modules outright
    if isinstance(obj, types.ModuleType):
        return False

    mod_of_obj = getattr(obj, '__module__', '')
    # If object is defined in the module or a submodule, include
    if mod_of_obj and (mod_of_obj == modname or mod_of_obj.startswith(modname + '.')):
        return True

    # Exclude common noisy modules by module name prefix
    noisy_prefixes = ('typing', 'inspect', 'importlib', 'logging', 'tornado', 'asyncio')
    if mod_of_obj and any(mod_of_obj.startswith(p) for p in noisy_prefixes):
        return False

    # Exclude builtin types (unless explicitly defined in module which we already handled)
    if mod_of_obj in ('builtins', ''):
        return False

    # Try to locate the defining module/file and include only if it lives inside the repo
    try:
        defining_mod = inspect.getmodule(obj)
        if defining_mod is None:
            # could be a simple constant like int/str; skip unless its __module__ matches
            return False
        mod_file = getattr(defining_mod, '__file__', None)
        if not mod_file:
            return False
        mod_path = Path(mod_file).resolve()
        try:
            mod_path.relative_to(ROOT)
            # defined inside repository
            return True
        except Exception:
            return False
    except Exception:
        return False

for modname in modules:
    try:
        mod = importlib.import_module(modname)
    except Exception as e:
        all_data[modname] = { 'error': repr(e) }
        continue
    public = []
    for name in sorted(dir(mod)):
        if name.startswith('_'):
            continue
        # If allowlist exists for module, skip anything not in allowlist early
        allow = _vis.get(modname, {}).get('allowlist')
        if allow is not None and name not in allow:
            continue
        try:
            obj = getattr(mod, name)
        except Exception:
            continue
        # Filter imported/third-party noise: include only module-defined or simple constants
        if not include_obj(modname, obj):
            continue
        entry = {'name': name}
        if inspect.isclass(obj):
            try:
                sig = inspect.signature(obj)
                entry['kind'] = 'class'
                entry['signature'] = f"{name}{sig}"
            except Exception:
                entry['kind'] = 'class'
                entry['signature'] = name
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            try:
                sig = inspect.signature(obj)
                entry['kind'] = 'function'
                entry['signature'] = f"{name}{sig}"
            except Exception:
                entry['kind'] = 'function'
                entry['signature'] = name
        else:
            entry['kind'] = type(obj).__name__
            try:
                entry['repr'] = repr(obj)
            except Exception:
                entry['repr'] = str(type(obj))
        public.append(entry)
    all_data[modname] = {'public': public}

# Also write a CSV of candidates vs allowlist for reviewers
CAND_CSV = ROOT / 'docs' / 'work' / 'api_cleanup_candidates.csv'
with CAND_CSV.open('w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['module','name','kind','signature','decision'])
    for modname, data in all_data.items():
        allow = set(_vis.get(modname, {}).get('allowlist') or [])
        if 'public' not in data:
            continue
        for e in data['public']:
            nm = e.get('name','')
            decision = 'keep' if (not allow or nm in allow) else 'review'
            writer.writerow([modname, nm, e.get('kind',''), e.get('signature',''), decision])

# Write human readable MD (with cleaned output)
lines = ["# Module API Summary", "", "Generated by docs/work/generate_module_api.py", ""]
for modname, data in all_data.items():
    lines.append(f"## {modname}")
    if 'error' in data:
        lines.append(f"Error importing module: {data['error']}")
        lines.append("")
        continue
    lines.append("")
    lines.append("| Name | Kind | Signature / Value |")
    lines.append("| --- | --- | --- |")
    for e in data['public']:
        if e['kind'] in ('class','function'):
            sig = e.get('signature','')
            lines.append(f"| `{e['name']}` | {e['kind']} | `{sig}` |")
        else:
            reprtext = e.get('repr','')
            if len(reprtext) > 200:
                reprtext = reprtext[:197] + '...'
            lines.append(f"| `{e['name']}` | {e['kind']} | `{reprtext}` |")
    lines.append("")

OUT_MD.write_text('\n'.join(lines), encoding='utf-8')

# Write per-module snippet files (clean tables) and attempt to inject into docs/modules/<name>.md
for modname, data in all_data.items():
    outp = OUT_DIR / (modname.replace('.', '_') + '.md')
    l = [f"### {modname}", "", "| Name | Kind | Signature / Value |", "| --- | --- | --- |"]
    if 'error' in data:
        l.append(f"Error importing module: {data['error']}")
    else:
        for e in data['public']:
            if e['kind'] in ('class','function'):
                sig = e.get('signature','')
                l.append(f"| `{e['name']}` | {e['kind']} | `{sig}` |")
            else:
                reprtext = e.get('repr','')
                if len(reprtext) > 200:
                    reprtext = reprtext[:197] + '...'
                l.append(f"| `{e['name']}` | {e['kind']} | `{reprtext}` |")
    outp.write_text('\n'.join(l), encoding='utf-8')

# Inject into docs/modules/<basename>.md if marker exists
for modname in all_data.keys():
    basename = modname.split('.')[-1]
    target = ROOT / 'docs' / 'modules' / f"{basename}.md"
    gen_file = OUT_DIR / (modname.replace('.', '_') + '.md')
    if not target.exists():
        continue
    content = target.read_text(encoding='utf-8')
    marker = f"<!-- generated: docs/work/generated_modules/{modname.replace('.', '_')}.md -->"
    gen_text = '\n' + gen_file.read_text(encoding='utf-8') + '\n'
    if marker in content:
        # replace marker line and everything after with marker + generated content
        parts = content.split(marker)
        new_content = parts[0] + marker + '\n' + gen_text
    else:
        # append generated content at end
        new_content = content + '\n\n' + gen_text
    target.write_text(new_content, encoding='utf-8')

# Also write JSON for programmatic use
OUT_JSON = ROOT / 'docs' / 'work' / 'module_api_summary.json'
with OUT_JSON.open('w', encoding='utf-8') as jf:
    json.dump(all_data, jf, indent=2, ensure_ascii=False)

print(f"Wrote module summaries to {OUT_MD} and {OUT_DIR} and {OUT_JSON}")
print(f"Wrote candidates CSV to {CAND_CSV}")
