# Middleware and Module Boundary Example

This example explains two ideas that are easy to confuse:

- `@module` defines a runtime boundary for a package
- `@middleware` extends the request pipeline, not the application bootstrap model

Run:

```bash
python -m examples.middleware_and_module
```

Endpoint:

- `GET /inventory/summary`

Response headers:

- `X-Cullinan-Example: middleware-and-module`
- `X-Module-Boundary: examples.middleware_and_module`

