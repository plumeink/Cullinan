# Minimal App Example

Shows the shortest recommended Cullinan path:

1. Declare business behavior with decorators
2. Define a `RootModule`
3. Start with `configure(root_module=...)` and `run()`

`run()` is intentionally presented as a Cullinan entrypoint rather than a
Tornado-specific bootstrap; the framework resolves the concrete backend for you.

Run:

```bash
python -m examples.minimal_app
```

Endpoint:

- `GET /hello`
