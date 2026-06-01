# Testing Flow Example

This example shows how to test a Cullinan application through the public API
without starting a real server process.

Run the example test:

```bash
python -m pytest examples/testing_flow/test_app.py -q
```

The test configures the example with `configure(root_module=...)`, creates the
ASGI app via `get_asgi_app()`, and asserts the response payload directly.

