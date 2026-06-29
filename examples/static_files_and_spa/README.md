# Static Files and SPA Example

This example demonstrates Cullinan's declarative static-files mounts and
optional Single-Page Application fallback. The same configuration runs on
both Tornado and ASGI runtimes — Cullinan registers the mounts on its
gateway router so the choice of backend stays a deployment decision.

## Layout

```
examples/static_files_and_spa/
├── public/                # /public/* — long-cached "classic" assets
│   └── robots.txt
├── spa/                   # /  — SPA bundle with client-side routing
│   ├── index.html
│   └── assets/
│       ├── main.css       # /assets/* — long cache, immutable
│       └── main.js
└── root.py
```

## What it shows

1. `StaticFiles(url="/public", directory=..., max_age=3600)` — serves a
   normal asset directory with a 1-hour `Cache-Control` window.
2. `StaticFiles(url="/assets", directory=..., max_age=31536000, immutable=True)`
   — long-cache hashed bundle assets.
3. `StaticFiles.spa_app(directory="spa", index="index.html")` — falls back
   to `index.html` for paths like `/settings/profile` so client-side
   routing works, while requests for missing static-looking files (e.g.
   `/assets/missing.js`) still return `404`.
4. `@controller(url="/api/health")` — a regular controller coexists with
   the mounts and is matched first because the router prefers static path
   segments over wildcards.

## Run

```bash
python -m examples.static_files_and_spa
```

Then try:

- <http://localhost:4082/> — SPA index
- <http://localhost:4082/settings/profile> — same `index.html` (SPA fallback)
- <http://localhost:4082/assets/main.js> — real bundle file with
  `Cache-Control: max-age=31536000, public, immutable`
- <http://localhost:4082/public/robots.txt> — cached for 1 hour
- <http://localhost:4082/api/health> — controller JSON
- <http://localhost:4082/assets/missing.js> — 404 (asset-looking miss)

## See also

- `docs/static_files_guide.md` — full reference and recipes
- `docs/zh/static_files_guide.md` — 中文文档
