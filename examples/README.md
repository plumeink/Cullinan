# Cullinan Examples

This directory is the single source of runnable examples for the current Cullinan public API.

## Recommended order

1. `examples/minimal_app/`
2. `examples/controller_service_inject/`
3. `examples/middleware_and_module/`
4. `examples/parameter_handling/`
5. `examples/testing_flow/`

## Run examples

- `python -m examples.minimal_app`
- `python -m examples.controller_service_inject`
- `python -m examples.middleware_and_module`
- `python -m examples.parameter_handling`
- `python -m pytest examples/testing_flow/test_app.py -q`

Each example keeps one teaching goal and follows the recommended Cullinan path:
`configure(root_module=...)`, decorator-first business code, and `Inject()` for type-led injection.

