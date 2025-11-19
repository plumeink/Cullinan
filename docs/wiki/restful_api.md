title: "RESTful API decorators"
slug: "restful-api"
author: "Plumeink"

# RESTful API decorators (detailed)

This page documents the HTTP method decorators used in Cullinan controllers: `get_api`, `post_api`, `patch_api`, `delete_api` and `put_api`.

Summary
- All decorators are defined as `def get_api(**kwargs)` (and similarly for others) and therefore accept only keyword arguments. Using a positional argument like `@get_api('/user')` is invalid and will raise a TypeError on import. Always use `@get_api(url='/users/{user_id}')`.
- URL templates use `{name}` placeholders parsed by `url_resolver`. Those placeholders are mapped to controller method arguments (order-based).

Supported keyword arguments (common)
- url: string route template, e.g. `'/users/{user_id}'`.
- query_params: iterable of query param names (mapped to `request_resolver`'s query section).
- file_params: iterable of file field names for uploads.
- headers: iterable of required HTTP header names; missing headers trigger the project's missing-header handler.

POST/PATCH specific
- body_params: iterable of body field names to parse from JSON or form body.
- get_request_body: boolean; if True, the raw request body will be passed to the handler via `request_handler`.

How URL templates work
- Use `{param}` placeholders. Example: `'/users/{user_id}/posts/{post_id}'`.
- `url_resolver` translates the template into a regex-like path and returns a list of parameter names in order (e.g. `['user_id','post_id']`).
- The decorated method receives path parameter values as positional args in the same order as the list returned by `url_resolver` (or combined with controller-level url param keys).
- Allowed characters for path captures are limited by the resolver (e.g. `[a-zA-Z0-9-]+`) and a trailing `/*` to allow an optional slash.

Decorator behavior and request handling
- Each decorator wraps the original function and registers a Tornado handler method via `EncapsulationHandler.add_func(url=local_url, type='get')` (or type='post', etc.).
- At request time the framework calls `request_resolver` and `header_resolver` to build (url_dict, query_dict, body_dict, file_dict) and passes them, together with header data, into `request_handler` which invokes your controller method.
- `get_api`/`delete_api`/`put_api` typically do not use `body_params`; `post_api` and `patch_api` support `body_params` and `get_request_body`.

Examples

1) Simple GET with path param

```text
@controller(url='/api/users')
class UserController:
    @get_api(url='/{user_id}')
    def get_user(self, url_param):
        # extract the path parameter from the url_param dict
        user_id = url_param.get('user_id') if url_param else None
        return {'id': user_id}
```

2) GET with query params

```text
@controller(url='/api/users')
class UserController:
    @get_api(url='/', query_params=('page','size'))
    def list_users(self, query_param):
        # page and size come from query string and are accessed via query_param
        page = query_param.get('page') if query_param else None
        size = query_param.get('size') if query_param else None
        return {'page': page, 'size': size}
```

3) POST with body params and files

```text
@controller(url='/api/upload')
class UploadController:
    @post_api(url='/', body_params=('title',), file_params=('file',))
    def upload(self, body_param, files):
        title = body_param.get('title') if body_param else None
        file_obj = files.get('file') if files else None
        return {'uploaded': bool(file_obj)}
```

Errors and common pitfalls
- Using positional decorator args: `@get_api('/user')` is invalid. Use `@get_api(url='/user')`.
- Mismatched path names: if your URL template includes `{user_id}` but your method signature lacks the corresponding parameter, the framework will pass None or may behave unexpectedly — ensure names match and argument order aligns.
- Missing required headers: if `headers` is provided and request omits them, the configured missing-header handler will be invoked (it may raise or set an error response).
- Body parsing: `body_params` attempts to parse JSON when Content-Type starts with `application/json`; if parsing fails, fields will be None.

When to use which decorator
- Use `get_api` for idempotent read operations.
- Use `post_api` for create operations where you need to parse body fields or accept file uploads.
- Use `patch_api` for partial updates and `put_api` for full replacements; behavior mirrors POST w.r.t. body_params when provided.

Linking to source
- Implementation lives in `cullinan/controller/core.py` (`get_api`, `post_api`, `url_resolver`, `request_resolver`, and `request_handler`). Prefer reading the tests in `tests/` (search for `@get_api(url=`) for practical examples.

See also
- `docs/getting_started.md` (quick overview)
- `docs/wiki/injection.md` (dependency injection patterns)
