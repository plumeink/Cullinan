# Testing Flow Example

This example shows how to test a Cullinan application through the public API
without starting a real server process.

Run the example test:

```bash
python -m pytest examples/testing_flow/test_app.py -q
```

The test resolves the example through its entry method, creates the
ASGI app via `main.get_asgi_app()`, and asserts the response payload directly.

This keeps the example focused on Cullinan's public testing surface instead of
requiring application code to depend on a concrete server framework.
