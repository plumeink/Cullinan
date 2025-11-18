title: "Extensions & Plugins"
slug: "extensions"
module: ["cullinan"]
tags: ["extensions", "plugins"]
author: "TBD"
reviewers: []
status: draft
locale: en
translation_pair: "docs/zh/wiki/extensions.md"
related_tests: []
related_examples: []
estimate_pd: 1.5
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# Extensions & Plugins

This page explains how to extend Cullinan with custom plugins and extensions. It covers extension points, provider registration, typical plugin patterns, and a minimal example showing how to register a custom provider and hook it into the application lifecycle.

Design principles

- Non-invasive: prefer registering providers, controllers, or middleware rather than patching framework internals.
- Reversible: exposed extension points should be removable/unregisterable for tests and dynamic reconfiguration.
- Discoverable: plugins should be discoverable via module scanning or explicit registration APIs.

Extension points

1. Providers and ServiceRegistry
   - Use `ProviderRegistry` and provider implementations (`ClassProvider`, `FactoryProvider`, `InstanceProvider`) to provide services. Register providers and then add the provider registry into the global `InjectionRegistry` so injections resolve correctly.
   - Key API: `cullinan.core.ProviderRegistry`, `cullinan.core.ScopedProvider`, `cullinan.service.registry.ServiceRegistry`.

2. Controllers
   - Register controller functions or classes via the `controller` decorator or via explicit registry APIs. Plugins that add routes should register controllers during application startup.
   - Key API: `cullinan.controller.controller`, `cullinan.controller.get_controller_registry()`.

3. Middleware
   - Implement middleware classes/functions that follow the project's middleware contract and register them in the app configuration or during startup to influence request/response processing.
   - Key API: `cullinan.middleware` package (see examples).

4. Lifecycle hooks
   - Plugins can register startup and shutdown handlers with the `CullinanApplication` via `add_shutdown_handler` or by implementing `LifecycleAware` interfaces if needed.
   - Key API: `CullinanApplication.add_shutdown_handler`, `cullinan.core.lifecycle` utilities.

Discovery and registration patterns

- Explicit registration (recommended for clarity): your plugin provides a function `register(app_or_registry)` which the application calls during startup. Example:

```python
# my_plugin.py
from cullinan.service import Service, service
from cullinan.core import ProviderRegistry, ScopedProvider, SingletonScope

class MyService(Service):
    def __init__(self):
        self.value = 'my plugin service'

def register_service(provider_registry: ProviderRegistry):
    provider_registry.register_provider(
        'MyService',
        ScopedProvider(lambda: MyService(), SingletonScope(), 'MyService')
    )

# Application startup
# from my_plugin import register_service
# provider_registry = ProviderRegistry()
# register_service(provider_registry)
# injection_registry.add_provider_registry(provider_registry)
```

- Auto-discovery (convenience): use module scanning (if enabled) to discover plugin packages under a well-known namespace (e.g., `myproject.plugins.*`). Prefer explicit registration for production deployments.

Packaging and distribution

- Package your plugin as a standard Python package. Expose a `register()` entrypoint or a well-known module path for discovery.
- Optionally provide an entry_point in setup.cfg / setup.py under a custom group (e.g., `cullinan.plugins`) and use pkg_resources or importlib.metadata to discover installed plugins.

Minimal plugin example — logging middleware

```python
# my_logging_plugin.py
import logging
from cullinan.middleware import MiddlewareBase

logger = logging.getLogger('my_plugin')

class RequestLogger(MiddlewareBase):
    def process_request(self, request):
        logger.info('Incoming %s %s', request.method, request.path)

def register(app):
    # app-specific registration, pseudocode
    app.add_middleware(RequestLogger())
```

Testing plugins

- Unit-test your plugin in isolation, mocking provider registries and application lifecycle.
- Ensure `register()` is idempotent and can be called multiple times safely (or add guards).

Security and compatibility notes

- Plugins run inside the application process; avoid executing untrusted code or allowing plugins to run arbitrary startup scripts.
- Document compatibility with Cullinan versions and provide upgrade notes in your plugin's package.

Next steps

- Provide a plugin scaffold generator (cookiecutter) for easier authoring.
- Add example plugin packages to the `examples/` directory for documentation and CI tests.
