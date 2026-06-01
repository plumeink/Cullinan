# Parameter Handling Example

This example keeps parameter handling attached to controller methods instead of
teaching raw request plumbing first.

Run:

```bash
python -m examples.parameter_handling
```

Endpoints:

- `GET /catalog/items/{item_id}?include_meta=true&locale=zh-CN`
- `POST /catalog/search`

