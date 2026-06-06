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
entry-method startup with `@application`, optional `@configure(...)`,
decorator-first business code, and `Inject()` for type-led injection.

The examples are intentionally engine-neutral at the application layer: business
code targets Cullinan semantics first, while the framework decides whether to
bridge into ASGI or Tornado at runtime.

Historical compatibility demos live under `examples/legacy/` and are not part of
the maintained default learning path. Only `decorator_demo_090.py` remains —
other legacy demos were cleaned up when their referenced APIs (`cullinan.run`,
`cullinan.core.provider`) were removed.

## Advanced extension demos

- `examples/extension_registration_demo.py` — maintained advanced demo for extension discovery and middleware registration
