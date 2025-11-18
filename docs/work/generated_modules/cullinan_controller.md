### cullinan.controller

| Name | Kind | Signature / Value |
| --- | --- | --- |
| `controller` | function | `controller(**kwargs) -> Callable` |
| `get_controller_registry` | function | `get_controller_registry() -> cullinan.controller.registry.ControllerRegistry` |
| `get_header_registry` | function | `get_header_registry() -> cullinan.controller.core.HeaderRegistry` |
| `request_resolver` | function | `request_resolver(self, url_param_key_list: Optional[Sequence] = None, url_param_value_list: Optional[Sequence] = None, query_param_names: Optional[Sequence] = None, body_param_names: Optional[Sequence] = None, file_param_key_list: Optional[Sequence] = None) -> Tuple[Optional[dict], Optional[dict], Optional[dict], Optional[dict]]` |
| `reset_controller_registry` | function | `reset_controller_registry() -> None` |
| `response_build` | function | `response_build(**kwargs) -> cullinan.controller.core.StatusResponse` |