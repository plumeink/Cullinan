### cullinan.core

| Name | Kind | Signature / Value |
| --- | --- | --- |
| `Inject` | class | `Inject(name: Optional[str] = None, required: bool = True)` |
| `InjectByName` | class | `InjectByName(service_name: Optional[str] = None, required: bool = True)` |
| `InjectionRegistry` | class | `InjectionRegistry()` |
| `ProviderRegistry` | class | `ProviderRegistry()` |
| `RequestScope` | class | `RequestScope(storage_key: str = '_scoped_instances')` |
| `SingletonScope` | class | `SingletonScope()` |
| `TransientScope` | class | `TransientScope()` |
| `create_context` | function | `create_context() -> cullinan.core.context.RequestContext` |
| `destroy_context` | function | `destroy_context() -> None` |
| `get_context_value` | function | `get_context_value(key: str, default: Any = None) -> Any` |
| `get_current_context` | function | `get_current_context() -> Optional[cullinan.core.context.RequestContext]` |
| `get_injection_registry` | function | `get_injection_registry() -> cullinan.core.injection.InjectionRegistry` |
| `get_request_scope` | function | `get_request_scope() -> cullinan.core.scope.RequestScope` |
| `get_singleton_scope` | function | `get_singleton_scope() -> cullinan.core.scope.SingletonScope` |
| `get_transient_scope` | function | `get_transient_scope() -> cullinan.core.scope.TransientScope` |
| `inject_constructor` | function | `inject_constructor(cls: Optional[Type] = None)` |
| `injectable` | function | `injectable(cls: Optional[Type] = None)` |
| `reset_injection_registry` | function | `reset_injection_registry() -> None` |
| `set_context_value` | function | `set_context_value(key: str, value: Any) -> None` |
| `set_current_context` | function | `set_current_context(context: Optional[cullinan.core.context.RequestContext]) -> None` |