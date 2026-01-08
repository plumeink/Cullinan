title: "RESTful API decorators"
slug: "restful-api"
author: "Plumeink"
status: updated
locale: en
translation_pair: "docs/zh/wiki/restful_api.md"
last_updated: "2026-01-08T00:00:00Z"

# RESTful API decorators (detailed)

This page documents the HTTP method decorators used in Cullinan controllers: `get_api`, `post_api`, `patch_api`, `delete_api` and `put_api`.

Summary
- All decorators are defined as `def get_api(**kwargs)` (and similarly for others) and therefore accept only keyword arguments. Using a positional argument like `@get_api('/user')` is invalid and will raise a TypeError on import. Always use `@get_api(url='/users/{user_id}')`.
- URL templates use `{name}` placeholders parsed by `url_resolver`. Those placeholders are mapped to controller method arguments (order-based).

---

## v0.90+ Recommended: Type-Safe Parameters

Cullinan 0.90 introduces a new type-safe parameter system. See [Parameter System Guide](../parameter_system_guide.md) for full details.

### Quick Example

```python
from cullinan.controller import controller, get_api, post_api
from cullinan.params import Path, Query, Body, DynamicBody

@controller(url='/api/users')
class UserController:
    # Type-safe parameters with automatic conversion and validation
    @get_api(url='/{id}')
    async def get_user(
        self,
        id: Path(int),
        include_posts: Query(bool, default=False),
    ):
        return {"id": id, "include_posts": include_posts}
    
    @post_api(url='/')
    async def create_user(
        self,
        name: Body(str, required=True),
        age: Body(int, default=0, ge=0, le=150),
    ):
        return {"name": name, "age": age}
    
    # DynamicBody for flexible body access
    @post_api(url='/dynamic')
    async def create_dynamic(self, body: DynamicBody):
        return {"name": body.name, "age": body.get('age', 0)}
```

### Available Parameter Types

| Type | Source | Example |
|------|--------|---------|
| `Path(type)` | URL path | `id: Path(int)` |
| `Query(type)` | Query string | `page: Query(int, default=1)` |
| `Body(type)` | Request body | `name: Body(str, required=True)` |
| `Header(type)` | HTTP headers | `auth: Header(str, alias='Authorization')` |
| `File()` | File upload | `avatar: File(max_size=5*1024*1024)` |
| `DynamicBody` | Full request body | `body: DynamicBody` |

### File Uploads (v0.90a5+)

```python
from cullinan.params import File, FileInfo, FileList

@controller(url='/api')
class UploadController:
    # Single file with validation
    @post_api(url='/upload')
    async def upload(self, avatar: File(max_size=5*1024*1024, allowed_types=['image/*'])):
        # avatar is a FileInfo instance
        print(avatar.filename, avatar.size, avatar.content_type)
        avatar.save('/uploads/')
        return {"filename": avatar.filename}
    
    # Multiple files
    @post_api(url='/upload-multiple')
    async def upload_multiple(self, files: File(multiple=True, max_count=10)):
        # files is a FileList instance
        return {"count": len(files), "names": files.filenames}
```

### Dataclass Field Validation (v0.90a5+)

```python
from cullinan.params import validated_dataclass, field_validator

@validated_dataclass
class CreateUserRequest:
    name: str
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v
```

### Pydantic Integration (v0.90a5+)

Pydantic models are automatically supported when Pydantic is installed:

```bash
pip install pydantic
```

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    age: int = Field(default=0, ge=0, le=150)

@post_api(url="/users")
async def create_user(self, user: CreateUserRequest):
    # Pydantic validation is automatic
    return {"name": user.name, "email": user.email}
```

The framework uses a pluggable model handler architecture. See [Parameter System Guide](../parameter_system_guide.md#pluggable-model-handlers-v090a5) for details.

### Validation

Built-in validators: `required`, `ge`, `le`, `gt`, `lt`, `min_length`, `max_length`, `regex`.

```python
@post_api(url='/register')
async def register(
    self,
    email: Body(str, regex=r'^[\w.-]+@[\w.-]+\.\w+$'),
    password: Body(str, min_length=8),
    age: Body(int, ge=18, le=120),
):
    pass
```

---

## Legacy Style (Decorator Options)

<details>
<summary><strong>Click to expand legacy style documentation</strong></summary>

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

### Legacy Examples

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

</details>

---

## Errors and common pitfalls

- Using positional decorator args: `@get_api('/user')` is invalid. Use `@get_api(url='/user')`.
- Mismatched path names: if your URL template includes `{user_id}` but your method signature lacks the corresponding parameter, the framework will pass None or may behave unexpectedly — ensure names match and argument order aligns.
- Missing required headers: if `headers` is provided and request omits them, the configured missing-header handler will be invoked (it may raise or set an error response).
- Body parsing: `body_params` attempts to parse JSON when Content-Type starts with `application/json`; if parsing fails, fields will be None.

## When to use which decorator

- Use `get_api` for idempotent read operations.
- Use `post_api` for create operations where you need to parse body fields or accept file uploads.
- Use `patch_api` for partial updates and `put_api` for full replacements; behavior mirrors POST w.r.t. body_params when provided.

## Linking to source

- Implementation lives in `cullinan/controller/core.py` (`get_api`, `post_api`, `url_resolver`, `request_resolver`, and `request_handler`). Prefer reading the tests in `tests/` (search for `@get_api(url=`) for practical examples.

## See also

- `docs/getting_started.md` (quick overview)
- `docs/wiki/injection.md` (dependency injection patterns)
- `docs/parameter_system_guide.md` (new type-safe parameter system)

