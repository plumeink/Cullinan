title: "RESTful API 装饰器"
slug: "restful-api"
author: "Plumeink"

# RESTful API 装饰器（详细）

本页面记录 Cullinan 控制器中用于路由绑定的 HTTP 动词装饰器：`get_api`、`post_api`、`patch_api`、`delete_api`、`put_api`。

摘要
- 所有装饰器在源码中定义为 `def get_api(**kwargs)`（其它动词同理），因此**仅接受关键字参数**。使用位置参数写法如 `@get_api('/user')` 是不合法的，会在导入时抛出 TypeError。请始终使用 `@get_api(url='/users/{user_id}')`。
- URL 模板使用 `{name}` 占位符，由 `url_resolver` 解析，按顺序映射到控制器方法参数。

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

示例

1) 简单 GET（带路径参数）

```text
@controller(url='/api/users')
class UserController:
    @get_api(url='/{user_id}')
    def get_user(self, user_id):
        return {'id': user_id}
```

2) GET 带查询参数

```text
@controller(url='/api/users')
class UserController:
    @get_api(url='/', query_params=('page','size'))
    def list_users(self, page, size):
        return {'page': page, 'size': size}
```

3) POST（body + 文件）

```text
@controller(url='/api/upload')
class UploadController:
    @post_api(url='/', body_params=('title',), file_params=('file',))
    def upload(self, body_params, files):
        title = body_params.get('title') if body_params else None
        file_obj = files.get('file') if files else None
        return {'uploaded': bool(file_obj)}
```

常见错误与陷阱
- 使用位置参数：`@get_api('/user')` 是错误的。请使用 `@get_api(url='/user')`。
- 模板与方法参数不匹配：若 URL 模板含 `{user_id}` 而方法签名缺少对应参数，框架会传入 None 或导致异常；请保持命名与顺序一致。
- 缺少必须头部：若指定 `headers`，请求未包含时会触发缺失头处理器，可能导致错误响应。
- body 解析失败：当 Content-Type 为 `application/json` 时框架会尝试解析 JSON；解析失败会导致 body 字段为 None。

使用建议
- `get_api`：用于幂等的读取操作。
- `post_api`：用于创建/上传，支持 body 与文件处理。
- `patch_api`：用于部分更新。
- `put_api`：用于完整替换（与 POST 在 body 参数处理上类似）。

源码参考
- 关键实现位于 `cullinan/controller/core.py`（`get_api`, `post_api`, `url_resolver`, `request_resolver`, `request_handler`）。
- 可以在 `tests/` 中通过搜索 `@get_api(url=` 找到实战测试样例。

另见
- `docs/getting_started.md`（快速说明）
- `docs/wiki/injection.md`（注入模式说明）
