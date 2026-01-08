title: "API Reference"
slug: "api-reference"
module: []
tags: ["api", "reference"]
author: "Plumeink"
reviewers: []
status: updated
locale: en
translation_pair: "docs/zh/api_reference.md"
related_tests: []
related_examples: []
estimate_pd: 1.5
last_updated: "2025-12-25T00:00:00Z"
pr_links: []

# API Reference

> **Note (v0.90)**: The core module has been reorganized. For the new API structure, see [Dependency Injection Guide](dependency_injection_guide.md) and [Import Migration Guide](import_migration_090.md).

This page provides an overview of the public API surface of Cullinan and acts as an entry point for generated or manually maintained per-module API pages. The recommended structure includes: a module index, the public symbols and signatures for each module, and a brief description of how to regenerate API documentation.

## Module index (example)

The following module list is for illustration only. The concrete index should be derived from the actual code structure and/or automated generation results:

- `cullinan.app` — Application creation and run entrypoints
- `cullinan.application` — Application lifecycle and startup flow
- `cullinan.core` — IoC/DI core (providers, registries, scopes, injection APIs)
- `cullinan.controller` — Controllers and RESTful API decorators
- `cullinan.service` — Service base class and the `@service` decorator
- `cullinan.middleware` — Middleware base classes and extension points
- `cullinan.codec` — Request/response encoding/decoding (JSON, Form, etc.)
- `cullinan.params` — Parameter handling (Path, Query, Body, Header, File, validators)

## New in v0.90+: Parameter System

The parameter system provides type-safe request parameter handling. See [Parameter System Guide](parameter_system_guide.md) for details.

### cullinan.params (v0.90a4+)

| Symbol | Type | Description |
|--------|------|-------------|
| `Param` | class | Base parameter class |
| `Path` | class | URL path parameter marker |
| `Query` | class | Query string parameter marker |
| `Body` | class | Request body parameter marker |
| `Header` | class | HTTP header parameter marker |
| `File` | class | File upload parameter marker |
| `UNSET` | sentinel | Sentinel value for unset parameters |
| `TypeConverter` | class | Type conversion utility |
| `Auto` | class | Auto type inference utility |
| `AutoType` | class | Auto type marker for signatures |
| `DynamicBody` | class | Dynamic request body container |
| `SafeAccessor` | class | Chain-safe property accessor |
| `EMPTY` | sentinel | Empty value sentinel |
| `ParamValidator` | class | Parameter validation utility |
| `ValidationError` | exception | Validation error |
| `ModelResolver` | class | dataclass model resolution |
| `ModelError` | exception | Model resolution error |
| `ParamResolver` | class | Parameter resolution orchestrator |
| `ResolveError` | exception | Parameter resolution error |

### cullinan.params (v0.90a5+)

| Symbol | Type | Description |
|--------|------|-------------|
| `FileInfo` | class | File metadata container |
| `FileList` | class | Multiple files container |
| `field_validator` | decorator | Dataclass field validator |
| `validated_dataclass` | decorator | Auto-validating dataclass |
| `FieldValidationError` | exception | Field validation error |
| `Response` | decorator | Response model decorator |
| `ResponseModel` | class | Response model definition |
| `ResponseSerializer` | class | Response serialization utility |
| `serialize_response` | function | Convenience serialization function |
| `get_response_models` | function | Get response models from function |

### cullinan.params.model_handlers (v0.90a5+)

Pluggable model handler architecture for third-party library integration.

| Symbol | Type | Description |
|--------|------|-------------|
| `ModelHandler` | class | Abstract base class for model handlers |
| `ModelHandlerError` | exception | Model handler error |
| `ModelHandlerRegistry` | class | Registry for model handlers |
| `DataclassHandler` | class | Built-in dataclass handler |
| `PydanticHandler` | class | Optional Pydantic handler (if installed) |
| `get_model_handler_registry()` | function | Get global handler registry |
| `reset_model_handler_registry()` | function | Reset registry (testing) |

### cullinan.codec

| Symbol | Type | Description |
|--------|------|-------------|
| `BodyCodec` | class | Abstract request body codec |
| `ResponseCodec` | class | Abstract response codec |
| `JsonBodyCodec` | class | JSON body decoder |
| `JsonResponseCodec` | class | JSON response encoder |
| `FormBodyCodec` | class | Form body decoder |
| `CodecRegistry` | class | Codec registry |
| `get_codec_registry()` | function | Get global codec registry |
| `reset_codec_registry()` | function | Reset codec registry (testing) |
| `DecodeError` | exception | Decoding error |
| `EncodeError` | exception | Encoding error |
| `CodecError` | exception | Base codec error |

### cullinan.middleware (new additions)

| Symbol | Type | Description |
|--------|------|-------------|
| `BodyDecoderMiddleware` | class | Auto body decoding middleware |
| `get_decoded_body()` | function | Get decoded request body |
| `set_decoded_body()` | function | Set decoded body (testing) |

## Public symbols and signatures (recommended structure)

For each module, the API reference is recommended to follow this structure:

- Module path, for example: `cullinan.controller`
- Short description: primary responsibility and typical usage scenarios
- List of public classes and functions (example):
  - `@controller(...)` — Controller decorator, responsible for auto-registering controllers and their routes
  - `@get_api(url=..., query_params=..., body_params=..., headers=...)` — GET endpoint decorator
  - `@post_api(url=..., body_params=..., headers=...)` — POST endpoint decorator
  - `Inject`, `InjectByName` — Property/constructor injection markers

A complete API reference can be populated using this structure, either via automated generation or by manual curation.

## Regenerating API documentation (example workflow)

When adding automation later, a static analysis script can be used to generate the API index and keep this page in sync with the source. A typical workflow might be:

1. Maintain a script under `docs/work/` (for example `generate_api_reference.py`) that scans modules and emits Markdown fragments.
2. Have the script produce a per-module API list (classes, functions, signatures, short descriptions) into `docs/work/api_modules.md` or update this page directly.
3. Run the script periodically in CI or as part of local documentation build steps to ensure the API reference reflects the current codebase.

The exact tooling and script implementation can be refined based on project conventions and the chosen documentation toolchain.
