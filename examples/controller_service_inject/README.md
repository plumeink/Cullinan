# Controller, Service, and Inject Example

This example demonstrates the standard Cullinan business structure:

- `@service` owns business logic
- `@controller` exposes Web APIs
- `Inject()` wires the business dependency

Run:

```bash
python -m examples.controller_service_inject
```

Endpoints:

- `GET /users`
- `GET /users/{user_id}`

