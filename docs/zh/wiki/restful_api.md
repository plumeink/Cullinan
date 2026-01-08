title: "RESTful API 装饰器"
slug: "restful-api"
author: "Plumeink"
status: updated
locale: zh
translation_pair: "docs/wiki/restful_api.md"
last_updated: "2026-01-08T00:00:00Z"

# RESTful API 装饰器（详细）

本页面记录 Cullinan 控制器中用于路由绑定的 HTTP 动词装饰器：`get_api`、`post_api`、`patch_api`、`delete_api`、`put_api`。

摘要
- 所有装饰器在源码中定义为 `def get_api(**kwargs)`（其它动词同理），因此**仅接受关键字参数**。使用位置参数写法如 `@get_api('/user')` 是不合法的，会在导入时抛出 TypeError。请始终使用 `@get_api(url='/users/{user_id}')`。
- URL 模板使用 `{name}` 占位符，由 `url_resolver` 解析，按顺序映射到控制器方法参数。

---

## v0.90+ 推荐：类型安全参数

Cullinan 0.90 引入了新的类型安全参数系统。详见 [参数系统指南](../parameter_system_guide.md)。

### 快速示例

```python
from cullinan.controller import controller, get_api, post_api
from cullinan.params import Path, Query, Body, DynamicBody

@controller(url='/api/users')
class UserController:
    # 类型安全参数，支持自动转换和校验（新的统一语法）
    @get_api(url='/{id}')
    async def get_user(
        self,
        id: int = Path(),
        include_posts: bool = Query(default=False),
    ):
        return {"id": id, "include_posts": include_posts}
    
    @post_api(url='/')
    async def create_user(
        self,
        name: str = Body(required=True),
        age: int = Body(default=0, ge=0, le=150),
    ):
        return {"name": name, "age": age}
    
    # DynamicBody 提供灵活的请求体访问
    @post_api(url='/dynamic')
    async def create_dynamic(self, body: DynamicBody):
        return {"name": body.name, "age": body.get('age', 0)}
```

### 可用的参数类型

| 类型 | 来源 | 示例 |
|------|------|------|
| `Path(type)` | URL 路径 | `id: int = Path()` |
| `Query(type)` | 查询字符串 | `page: int = Query(default=1)` |
| `Body(type)` | 请求体 | `name: str = Body(required=True)` |
| `Header(type)` | HTTP 请求头 | `auth: str = Header(alias='Authorization')` |
| `File()` | 文件上传 | `avatar: File = File(max_size=5*1024*1024)` |
| `RawBody` | 原始请求体 (未解析的 bytes) | `raw: bytes = RawBody()` |
| `DynamicBody` | 完整请求体 (已解析) | `body: DynamicBody = DynamicBody()` |

> **注意**: 纯类型注解如 `page: int` 会自动作为 Query 参数处理。
> 使用 `= RawBody()` 或 `= DynamicBody()` 可以避免 "non-default parameter follows default parameter" 错误。

### 文件上传 (v0.90a5+)

```python
from cullinan.params import File, FileInfo, FileList

@controller(url='/api')
class UploadController:
    # 带校验的单文件上传（新语法）
    @post_api(url='/upload')
    async def upload(self, avatar: File = File(max_size=5*1024*1024, allowed_types=['image/*'])):
        # avatar 是 FileInfo 实例
        print(avatar.filename, avatar.size, avatar.content_type)
        avatar.save('/uploads/')
        return {"filename": avatar.filename}
    
    # 使用 as_required() 声明必填文件
    @post_api(url='/upload-required')
    async def upload_required(self, avatar: File = File.as_required(max_size=5*1024*1024)):
        return {"filename": avatar.filename}
    
    # 多文件上传
    @post_api(url='/upload-multiple')
    async def upload_multiple(self, files: File = File(multiple=True, max_count=10)):
        # files 是 FileList 实例
        return {"count": len(files), "names": files.filenames}
```

### Dataclass 字段校验 (v0.90a5+)

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
            raise ValueError('无效的邮箱')
        return v
```

### Pydantic 集成 (v0.90a5+)

安装 Pydantic 后，Pydantic 模型会自动被支持：

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
    # Pydantic 校验自动执行
    return {"name": user.name, "email": user.email}
```

框架使用可插拔的模型处理器架构。详见 [参数系统指南](../parameter_system_guide.md#可插拔模型处理器-v090a5)。

### 校验

内置校验器：`required`、`ge`、`le`、`gt`、`lt`、`min_length`、`max_length`、`regex`。

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

## 传统方式（装饰器选项）

<details>
<summary><strong>点击展开传统方式文档</strong></summary>

支持关键字参数（通用）
- url：路由模板字符串，例如 `'/users/{user_id}'`。
- query_params：查询参数名的可迭代对象（由 `request_resolver` 的 query 部分解析）。
- file_params：用于文件上传的字段名集合。
- headers：要求存在的 HTTP 请求头，缺失时会触发缺失头处理器。

POST/PATCH 特有
- body_params：需要从 JSON/form body 中解析的字段名集合。
- get_request_body：布尔值；为 True 时，原始请求体会传入处理器。

URL 模板如何工作
- 使用 `{param}` 占位符，例如 `'/users/{user_id}/posts/{post_id}'`。
- `url_resolver` 将模板解析为匹配路径并返回参数名顺序列表（例如 `['user_id','post_id']`）。
- 被装饰的方法将按该顺序接收到路径参数值（或结合控制器级别的 url 参数键列表）。
- 占位符允许的字符由解析器限制（例如 `[a-zA-Z0-9-]+`），并允许可选的尾随 `/`。

装饰器行为与请求处理流程
- 装饰器会包装原始函数并通过 `EncapsulationHandler.add_func(url=local_url, type='get')` 注册为 Tornado 处理器（或其它动词）。
- 请求时，框架调用 `request_resolver` 与 `header_resolver` 构建 `(url_dict, query_dict, body_dict, file_dict)`，并将解析的数据传入 `request_handler`，最终由其调用你的控制器方法。
- `get_api`/`delete_api`/`put_api` 通常不处理 body（除非显式配置），而 `post_api`/`patch_api` 支持 `body_params` 与 `get_request_body`。

### 传统示例

1) 简单 GET（带路径参数）

```text
@controller(url='/api/users')
class UserController:
    @get_api(url='/{user_id}')
    def get_user(self, url_param):
        # 从 url_param 字典中获取路径参数
        user_id = url_param.get('user_id') if url_param else None
        return {'id': user_id}
```

2) GET 带查询参数

```text
@controller(url='/api/users')
class UserController:
    @get_api(url='/', query_params=('page','size'))
    def list_users(self, query_param):
        # page 和 size 从查询字符串解析，通过 query_param 访问
        page = query_param.get('page') if query_param else None
        size = query_param.get('size') if query_param else None
        return {'page': page, 'size': size}
```

3) POST（body + 文件）

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

## 常见错误与陷阱

- 使用位置参数：`@get_api('/user')` 是错误的。请使用 `@get_api(url='/user')`。
- 模板与方法参数不匹配：若 URL 模板含 `{user_id}` 而方法签名缺少对应参数，框架会传入 None 或导致异常；请保持命名与顺序一致。
- 缺少必须头部：若指定 `headers`，请求未包含时会触发缺失头处理器，可能导致错误响应。
- body 解析失败：当 Content-Type 为 `application/json` 时框架会尝试解析 JSON；解析失败会导致 body 字段为 None。

## 使用建议

- `get_api`：用于幂等的读取操作。
- `post_api`：用于创建/上传，支持 body 与文件处理。
- `patch_api`：用于部分更新。
- `put_api`：用于完整替换（与 POST 在 body 参数处理上类似）。

## 源码参考

- 关键实现位于 `cullinan/controller/core.py`（`get_api`, `post_api`, `url_resolver`, `request_resolver`, `request_handler`）。
- 可以在 `tests/` 中通过搜索 `@get_api(url=` 找到实战测试样例。

## 另见

- `docs/getting_started.md`（快速说明）
- `docs/wiki/injection.md`（注入模式说明）
- `docs/parameter_system_guide.md`（新的类型安全参数系统）
