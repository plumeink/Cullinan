# Minimal App Example

Shows the shortest recommended Cullinan path:

1. Declare business behavior with decorators
2. Declare an entry method with `@application`
3. Attach startup settings with `@configure(...)`
4. Start by calling `main()`

The entry method is intentionally presented as a Cullinan entrypoint rather than
a Tornado-specific bootstrap; the framework resolves the concrete backend for you.

Run:

```bash
python -m examples.minimal_app
```

Endpoint:

- `GET /hello`
