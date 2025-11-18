title: "cullinan.controller"
slug: "modules-controller"
module: ["cullinan.controller"]
tags: ["api", "module", "controller"]
author: "Plumeink"
reviewers: []
status: draft
locale: zh
translation_pair: "docs/modules/controller.md"
related_tests: ["tests/test_controller_injection_fix.py","tests/test_controller_with_methods.py"]
related_examples: ["examples/controller_di_middleware.py"]
estimate_pd: 1.5
last_updated: "2025-11-18T00:00:00Z"
pr_links: []

# cullinan.controller

摘要：控制器注册、生命周期与注入到控制器实例的机制。记录使用模式与常见陷阱。

## 公共 API（自动生成）

<!-- generated: docs/work/generated_modules/cullinan_controller.md -->

### cullinan.controller

| 名称 | 类型 | 签名 / 值 |
| --- | --- | --- |
| `ControllerRegistry` | class | `ControllerRegistry()` |
| `EncapsulationHandler` | class | `EncapsulationHandler()` |
| `Handler` | class | `Handler(application: 'Application', request: tornado.httputil.HTTPServerRequest, **kwargs: Any) -> None` |
| `HeaderRegistry` | class | `HeaderRegistry()` |
| `HttpResponse` | class | `HttpResponse() -> None` |
| `ResponsePool` | class | `ResponsePool(size: int = 100)` |
| `StatusResponse` | class | `StatusResponse(**kwargs) -> None` |
| `controller` | function | `controller(**kwargs) -> Callable` |
| `delete_api` | function | `delete_api(**kwargs: Any) -> Callable` |
| `disable_response_pooling` | function | `disable_response_pooling() -> None` |
| `emit_access_log` | function | `emit_access_log(request: Any, resp_obj: Optional[Any], status_code: Optional[int], duration: float) -> None` |
| `enable_response_pooling` | function | `enable_response_pooling(pool_size: int = 100) -> None` |
| `get_api` | function | `get_api(**kwargs: Any) -> Callable` |
| `get_controller_registry` | function | `get_controller_registry() -> cullinan.controller.registry.ControllerRegistry` |
| `get_header_registry` | function | `get_header_registry() -> cullinan.controller.core.HeaderRegistry` |
| `get_missing_header_handler` | function | `get_missing_header_handler() -> Callable[[Any, str], NoneType]` |
| `get_pooled_response` | function | `get_pooled_response() -> cullinan.controller.core.HttpResponse` |
| `get_response_pool_stats` | function | `get_response_pool_stats() -> Optional[dict]` |
| `header_resolver` | function | `header_resolver(self, header_names: Optional[Sequence] = None) -> Optional[dict]` |
| `patch_api` | function | `patch_api(**kwargs: Any) -> Callable` |
| `post_api` | function | `post_api(**kwargs: Any) -> Callable` |
| `put_api` | function | `put_api(**kwargs: Any) -> Callable` |
| `request_handler` | function | `request_handler(self, func: Callable, params: Tuple, headers: Optional[dict], type: str, get_request_body: bool = False) -> None` |
| `request_resolver` | function | `request_resolver(self, url_param_key_list: Optional[Sequence] = None, url_param_value_list: Optional[Sequence] = None, query_param_names: Optional[Sequence] = None, body_param_names: Optional[Sequence] = None, file_param_key_list: Optional[Sequence] = None) -> Tuple[Optional[dict], Optional[dict], Optional[dict], Optional[dict]]` |
| `reset_controller_registry` | function | `reset_controller_registry() -> None` |
| `response` | class | `response()` |
| `response_build` | function | `response_build(**kwargs) -> cullinan.controller.core.StatusResponse` |
| `return_pooled_response` | function | `return_pooled_response(resp: cullinan.controller.core.HttpResponse) -> None` |
| `set_missing_header_handler` | function | `set_missing_header_handler(handler: Callable[[Any, str], NoneType])` |
| `url_resolver` | function | `url_resolver(url: str) -> Tuple[str, list]` |

## 示例：注册一个简单控制器

```python
from cullinan.controller import controller, get_controller_registry

@controller(path='/hello')
def hello(request):
    return {'status': 200, 'body': 'Hello World'}

# 可选：直接注册到 registry（通常由模块扫描自动发现）
registry = get_controller_registry()
registry.register(r'/hello', hello)
```

说明：
- 使用 `controller` 装饰器注册路由处理器；框架支持模块扫描自动发现或显式注册。
- 若处理器需要依赖注入，请使用 `@injectable` 类或属性注入并确保在应用启动前已注册相应 provider。
